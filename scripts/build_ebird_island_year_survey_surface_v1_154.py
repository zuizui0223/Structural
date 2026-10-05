#!/usr/bin/env python3
"""Build a response-independent eBird island-year survey-support surface.

Species identities/detections are forbidden. The script consumes only official
Sampling Event Data plus the frozen USGS/Sayre island geometry. Shared checklists
are deduplicated before point-in-polygon mapping.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import sqlite3
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/ebird_island_year_survey_contract_v1_154.json"

class Stop(RuntimeError):
    pass

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def norm_header(x:str)->str:
    return " ".join(str(x).replace("_"," ").replace("."," ").upper().split())

def open_text(path:Path):
    if path.name.lower().endswith(".gz"):
        return gzip.open(path,"rt",encoding="utf-8",newline="")
    return path.open("r",encoding="utf-8",newline="")

def parse_bool(x:str)->bool:
    v=str(x).strip().casefold()
    if v in {"1","true"}: return True
    if v in {"0","false"}: return False
    raise Stop(f"invalid ALL SPECIES REPORTED value: {x!r}")

def opt_float(x:str,label:str,minimum:float|None=None):
    s=str(x).strip()
    if not s:return None
    try:v=float(s)
    except ValueError as e:raise Stop(f"invalid {label}: {s!r}") from e
    if not math.isfinite(v):raise Stop(f"nonfinite {label}")
    if minimum is not None and v<minimum:raise Stop(f"{label} below minimum")
    return v

def opt_int(x:str,label:str,minimum:int|None=None):
    s=str(x).strip()
    if not s:return None
    try:
        v=int(s) if not any(c in s for c in ".eE") else int(float(s))
    except ValueError as e:raise Stop(f"invalid {label}: {s!r}") from e
    if minimum is not None and v<minimum:raise Stop(f"{label} below minimum")
    return v

def make_event_key(sid:str,gid:str)->str:
    return ("G:"+gid) if gid else ("S:"+sid)

def init_db(conn:sqlite3.Connection):
    conn.execute("""
      CREATE TABLE events(
        event_key TEXT PRIMARY KEY,
        sid TEXT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        complete INTEGER NOT NULL,
        duration REAL,
        distance REAL,
        area REAL,
        observers INTEGER,
        protocol_type TEXT,
        protocol_code TEXT,
        conflict INTEGER NOT NULL DEFAULT 0
      )
    """)
    conn.execute("CREATE INDEX idx_events_year ON events(year)")

def insert_or_merge(conn:sqlite3.Connection,event:dict,tol:float):
    old=conn.execute(
      "SELECT sid,year,month,lat,lon,complete,duration,distance,area,observers,protocol_type,protocol_code,conflict FROM events WHERE event_key=?",
      (event["event_key"],)
    ).fetchone()
    if old is None:
        conn.execute(
          "INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
          (event["event_key"],event["sid"],event["year"],event["month"],event["lat"],event["lon"],
           int(event["complete"]),event["duration"],event["distance"],event["area"],event["observers"],
           event["protocol_type"],event["protocol_code"])
        )
        return
    old_sid,year,month,lat,lon,complete,dur,dist,area,obs,ptype,pcode,conflict=old
    bad=(year!=event["year"] or month!=event["month"] or complete!=int(event["complete"]) or
         abs(lat-event["lat"])>tol or abs(lon-event["lon"])>tol)
    new_conflict=int(bool(conflict or bad))
    if event["sid"] < old_sid:
        conn.execute(
          """UPDATE events SET sid=?,year=?,month=?,lat=?,lon=?,complete=?,duration=?,distance=?,area=?,
             observers=?,protocol_type=?,protocol_code=?,conflict=? WHERE event_key=?""",
          (event["sid"],event["year"],event["month"],event["lat"],event["lon"],int(event["complete"]),
           event["duration"],event["distance"],event["area"],event["observers"],event["protocol_type"],
           event["protocol_code"],new_conflict,event["event_key"])
        )
    elif new_conflict!=conflict:
        conn.execute("UPDATE events SET conflict=? WHERE event_key=?",(new_conflict,event["event_key"]))

def ingest_sed(sed_file:Path,contract:dict,conn:sqlite3.Connection)->dict:
    years=set(contract["official_sampling_event_source"]["analysis_years"])
    tol=float(contract["checklist_deduplication"]["conflicting_group_coordinates"].split("1e-6")[0] or 1e-6) if False else 1e-6
    forbidden={
      "SCIENTIFIC NAME","COMMON NAME","OBSERVATION COUNT","TAXONOMIC ORDER","CATEGORY","TAXON CONCEPT ID","SPECIES COMMENTS"
    }
    required={
      "SAMPLING EVENT IDENTIFIER","OBSERVATION DATE","LATITUDE","LONGITUDE","PROTOCOL TYPE","PROTOCOL CODE",
      "DURATION MINUTES","EFFORT DISTANCE KM","EFFORT AREA HA","NUMBER OBSERVERS","ALL SPECIES REPORTED","GROUP IDENTIFIER"
    }
    total=0
    with open_text(sed_file) as h:
        reader=csv.DictReader(h,delimiter="\t")
        if reader.fieldnames is None:raise Stop("missing SED header")
        col={norm_header(k):k for k in reader.fieldnames}
        missing=sorted(required-set(col))
        if missing:raise Stop(f"missing required SED headers: {missing}")
        bad=sorted(forbidden & set(col))
        if bad:raise Stop(f"species-response headers found in SED input: {bad}")
        for row in reader:
            total+=1
            sid=str(row[col["SAMPLING EVENT IDENTIFIER"]]).strip()
            if not sid:raise Stop("blank sampling event identifier")
            gid=str(row[col["GROUP IDENTIFIER"]]).strip()
            ds=str(row[col["OBSERVATION DATE"]]).strip()
            try:d=date.fromisoformat(ds)
            except ValueError as e:raise Stop(f"invalid date: {ds!r}") from e
            lat=opt_float(row[col["LATITUDE"]],"latitude")
            lon=opt_float(row[col["LONGITUDE"]],"longitude")
            if lat is None or lon is None:raise Stop("blank checklist coordinate")
            if not -90<=lat<=90 or not -180<=lon<=180:raise Stop("coordinate out of range")
            ev={
              "event_key":make_event_key(sid,gid),"sid":sid,"year":d.year,"month":d.month,
              "lat":lat,"lon":lon,"complete":parse_bool(row[col["ALL SPECIES REPORTED"]]),
              "duration":opt_float(row[col["DURATION MINUTES"]],"duration",0),
              "distance":opt_float(row[col["EFFORT DISTANCE KM"]],"distance",0),
              "area":opt_float(row[col["EFFORT AREA HA"]],"area",0),
              "observers":opt_int(row[col["NUMBER OBSERVERS"]],"observers",1),
              "protocol_type":str(row[col["PROTOCOL TYPE"]]).strip(),
              "protocol_code":str(row[col["PROTOCOL CODE"]]).strip()
            }
            insert_or_merge(conn,ev,tol)
            if total%100000==0:conn.commit()
    conn.commit()
    counts={
      "raw_checklist_rows":total,
      "deduplicated_event_keys":conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
      "conflicting_event_keys":conn.execute("SELECT COUNT(*) FROM events WHERE conflict=1").fetchone()[0],
      "complete_nonconflicting_events_in_analysis_years":conn.execute(
        "SELECT COUNT(*) FROM events WHERE conflict=0 AND complete=1 AND year BETWEEN ? AND ?",
        (min(years),max(years))
      ).fetchone()[0]
    }
    return counts

def load_island_geometry(path:Path,id_field_expected:str):
    try:
        import geopandas as gpd
    except ImportError as e:
        raise Stop("geopandas is required for geometry mapping") from e
    gdf=gpd.read_file(path)
    if gdf.empty:raise Stop("island geometry contains zero rows")
    names={norm_header(c):c for c in gdf.columns}
    key=norm_header(id_field_expected)
    if key not in names:raise Stop(f"missing island ID field: {id_field_expected}")
    idcol=names[key]
    if gdf.crs is None:raise Stop("island geometry CRS missing")
    gdf=gdf[[idcol,"geometry"]].rename(columns={idcol:"OBJECTID"})
    gdf=gdf.to_crs("EPSG:4326")
    if gdf["OBJECTID"].isna().any():raise Stop("blank OBJECTID")
    if gdf["OBJECTID"].astype(str).duplicated().any():raise Stop("duplicate OBJECTID")
    if gdf.geometry.isna().any():raise Stop("blank island geometry")
    return gdf

def aggregate_mapped_rows(rows:list[dict],min_checklists:int,min_months:int)->list[dict]:
    agg=defaultdict(lambda:{
      "checklists":0,"months":set(),"dur_n":0,"dur_sum":0.0,"dist_n":0,"dist_sum":0.0,
      "area_n":0,"obs_n":0,"protocols":set()
    })
    for r in rows:
        k=(str(r["OBJECTID"]),int(r["year"]))
        a=agg[k];a["checklists"]+=1;a["months"].add(int(r["month"]))
        if r["duration"] is not None:a["dur_n"]+=1;a["dur_sum"]+=float(r["duration"])
        if r["distance"] is not None:a["dist_n"]+=1;a["dist_sum"]+=float(r["distance"])
        if r["area"] is not None:a["area_n"]+=1
        if r["observers"] is not None:a["obs_n"]+=1
        a["protocols"].add((r["protocol_type"],r["protocol_code"]))
    out=[]
    for (oid,year),a in sorted(agg.items(),key=lambda z:(int(float(z[0][0])),z[0][1])):
        nmonths=len(a["months"])
        out.append({
          "OBJECTID":oid,"year":year,
          "complete_deduplicated_checklists":a["checklists"],
          "distinct_months":nmonths,
          "duration_minutes_nonmissing":a["dur_n"],
          "duration_minutes_sum":a["dur_sum"],
          "effort_distance_km_nonmissing":a["dist_n"],
          "effort_distance_km_sum":a["dist_sum"],
          "effort_area_ha_nonmissing":a["area_n"],
          "number_observers_nonmissing":a["obs_n"],
          "protocol_pairs":len(a["protocols"]),
          "surveyed":int(a["checklists"]>=min_checklists and nmonths>=min_months)
        })
    return out

def map_events(conn:sqlite3.Connection,gdf,years:set[int],batch_size:int=50000):
    import geopandas as gpd
    from shapely.geometry import Point
    mapped=[]
    outside=ambiguous=0
    cur=conn.execute(
      "SELECT year,month,lat,lon,duration,distance,area,observers,protocol_type,protocol_code "
      "FROM events WHERE conflict=0 AND complete=1 AND year BETWEEN ? AND ? ORDER BY event_key",
      (min(years),max(years))
    )
    while True:
        batch=cur.fetchmany(batch_size)
        if not batch:break
        base=[]
        for i,(year,month,lat,lon,dur,dist,area,obs,ptype,pcode) in enumerate(batch):
            base.append({
              "_row":i,"year":year,"month":month,"lat":lat,"lon":lon,"duration":dur,"distance":dist,
              "area":area,"observers":obs,"protocol_type":ptype,"protocol_code":pcode
            })
        pts=gpd.GeoDataFrame(base,geometry=[Point(r["lon"],r["lat"]) for r in base],crs="EPSG:4326")
        joined=gpd.sjoin(pts,gdf,how="left",predicate="intersects")
        groups=defaultdict(list)
        for _,r in joined.iterrows():
            groups[int(r["_row"])].append(None if r.get("OBJECTID") is None or str(r.get("OBJECTID"))=="nan" else r.get("OBJECTID"))
        for i,b in enumerate(base):
            ids={str(x) for x in groups.get(i,[]) if x is not None}
            if len(ids)==0:
                outside+=1;continue
            if len(ids)>1:
                ambiguous+=1;continue
            b["OBJECTID"]=next(iter(ids))
            mapped.append(b)
    return mapped,outside,ambiguous

def write_csv(path:Path,rows:list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=[
      "OBJECTID","year","complete_deduplicated_checklists","distinct_months",
      "duration_minutes_nonmissing","duration_minutes_sum","effort_distance_km_nonmissing",
      "effort_distance_km_sum","effort_area_ha_nonmissing","number_observers_nonmissing",
      "protocol_pairs","surveyed"
    ]
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n")
        w.writeheader();w.writerows(rows)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("sed_file",type=Path)
    ap.add_argument("island_geometry",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if c.get("schema")!="structural.ebird_island_year_survey_contract.v1_154":
        raise Stop("contract schema drift")
    if c["response_access_authorized"] is not False:raise Stop("response boundary drift")
    years=set(c["official_sampling_event_source"]["analysis_years"])
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    try:
        with tempfile.TemporaryDirectory() as td:
            conn=sqlite3.connect(str(Path(td)/"events.sqlite"))
            init_db(conn)
            ingest=ingest_sed(args.sed_file,c,conn)
            gdf=load_island_geometry(args.island_geometry,c["island_geometry"]["id_field"])
            mapped,outside,ambiguous=map_events(conn,gdf,years)
        q=c["annual_survey_quality_rule"]
        annual=aggregate_mapped_rows(mapped,int(q["complete_deduplicated_checklists_min"]),int(q["distinct_months_min"]))
        write_csv(out/"ebird_island_year_survey_surface.csv",annual)
        surveyed=sum(int(r["surveyed"]) for r in annual)
        islands=len({r["OBJECTID"] for r in annual if int(r["surveyed"])==1})
        year_support={str(y):sum(1 for r in annual if r["year"]==y and int(r["surveyed"])==1) for y in sorted(years)}
        receipt={
          "schema":"structural.ebird_island_year_survey_result.v1_154",
          "status":"RESPONSE_INDEPENDENT_ISLAND_YEAR_SURVEY_SURFACE_FROZEN",
          "candidate_id":c["candidate_id"],
          "sed_sha256":sha256(args.sed_file),
          "island_geometry_sha256":sha256(args.island_geometry),
          **ingest,
          "mapped_complete_events":len(mapped),
          "outside_geometry_events":outside,
          "ambiguous_geometry_events":ambiguous,
          "island_year_rows":len(annual),
          "surveyed_island_years":surveyed,
          "distinct_surveyed_islands":islands,
          "surveyed_islands_by_year":year_support,
          "survey_surface_sha256":sha256(out/"ebird_island_year_survey_surface.csv"),
          "species_identity_read":False,
          "species_detection_read":False,
          "species_nondetection_constructed":False,
          "annual_species_occupancy_constructed":False,
          "source_loss_events_constructed":False,
          "response_access_authorized":False,
          "counts_as_empirical_source_loss_evidence":False
        };code=0
    except Exception as e:
        if isinstance(e,(KeyboardInterrupt,SystemExit)):raise
        receipt={
          "schema":"structural.ebird_island_year_survey_result.v1_154","status":"STOP",
          "reason":str(e),"species_identity_read":False,"species_detection_read":False,
          "species_nondetection_constructed":False,"annual_species_occupancy_constructed":False,
          "source_loss_events_constructed":False,"response_access_authorized":False,
          "counts_as_empirical_source_loss_evidence":False
        };code=2
    (out/"ebird_island_year_survey_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
