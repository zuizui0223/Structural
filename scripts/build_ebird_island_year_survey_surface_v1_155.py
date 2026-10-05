#!/usr/bin/env python3
"""Build response-independent eBird island-year survey support.

Consumes checklist-level Sampling Event Data plus USGS/Sayre island geometry.
Species-response columns are forbidden.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,json,math,sqlite3,tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/ebird_island_year_survey_contract_v1_155.json"
class Stop(RuntimeError): pass

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def norm(x:str)->str:
    return " ".join(str(x).replace("_"," ").replace("."," ").upper().split())

def open_text(p:Path):
    return gzip.open(p,"rt",encoding="utf-8",newline="") if p.name.lower().endswith(".gz") else p.open("r",encoding="utf-8",newline="")

def parse_bool(x:str)->bool:
    v=str(x).strip().casefold()
    if v in {"1","true"}:return True
    if v in {"0","false"}:return False
    raise Stop(f"invalid ALL SPECIES REPORTED: {x!r}")

def opt_float(x,label,minimum=None):
    s=str(x).strip()
    if not s:return None
    try:v=float(s)
    except ValueError as e:raise Stop(f"invalid {label}: {s!r}") from e
    if not math.isfinite(v):raise Stop(f"nonfinite {label}")
    if minimum is not None and v<minimum:raise Stop(f"{label} below minimum")
    return v

def opt_int(x,label,minimum=None):
    s=str(x).strip()
    if not s:return None
    try:
        z=float(s);v=int(z)
        if z!=v:raise ValueError
    except ValueError as e:raise Stop(f"invalid {label}: {s!r}") from e
    if minimum is not None and v<minimum:raise Stop(f"{label} below minimum")
    return v

def resolve_protocol_schema(contract,col):
    matched=[]
    for name,spec in contract["official_sampling_event_source"]["protocol_schema_variants"].items():
        if set(spec["required_headers"])<=set(col):matched.append(name)
    if len(matched)!=1:raise Stop(f"expected exactly one supported protocol schema, found {matched}")
    spec=contract["official_sampling_event_source"]["protocol_schema_variants"][matched[0]]
    return matched[0],col[spec["observation_type_header"]],None if spec["protocol_name_header"] is None else col[spec["protocol_name_header"]]

def event_key(sid,gid):
    return f"G:{gid}" if gid else f"S:{sid}"

def init_db(conn):
    conn.execute("""CREATE TABLE events(
      event_key TEXT PRIMARY KEY,sid TEXT NOT NULL,year INTEGER NOT NULL,month INTEGER NOT NULL,
      lat REAL NOT NULL,lon REAL NOT NULL,complete INTEGER NOT NULL,duration REAL,distance REAL,area REAL,
      observers INTEGER,observation_type TEXT,protocol_name TEXT,protocol_code TEXT,conflict INTEGER NOT NULL DEFAULT 0)""")
    conn.execute("CREATE INDEX idx_events_year ON events(year)")

def insert_or_merge(conn,e,tol=1e-6):
    old=conn.execute("SELECT sid,year,month,lat,lon,complete,conflict FROM events WHERE event_key=?",(e["event_key"],)).fetchone()
    if old is None:
        conn.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
          (e["event_key"],e["sid"],e["year"],e["month"],e["lat"],e["lon"],int(e["complete"]),
           e["duration"],e["distance"],e["area"],e["observers"],e["observation_type"],e["protocol_name"],e["protocol_code"]))
        return
    sid,year,month,lat,lon,complete,conflict=old
    bad=(year!=e["year"] or month!=e["month"] or complete!=int(e["complete"]) or abs(lat-e["lat"])>tol or abs(lon-e["lon"])>tol)
    conflict=int(bool(conflict or bad))
    if e["sid"]<sid:
        conn.execute("""UPDATE events SET sid=?,year=?,month=?,lat=?,lon=?,complete=?,duration=?,distance=?,area=?,
          observers=?,observation_type=?,protocol_name=?,protocol_code=?,conflict=? WHERE event_key=?""",
          (e["sid"],e["year"],e["month"],e["lat"],e["lon"],int(e["complete"]),e["duration"],e["distance"],e["area"],
           e["observers"],e["observation_type"],e["protocol_name"],e["protocol_code"],conflict,e["event_key"]))
    else:
        conn.execute("UPDATE events SET conflict=? WHERE event_key=?",(conflict,e["event_key"]))

def ingest_sed(p,contract,conn):
    forbidden={"SCIENTIFIC NAME","COMMON NAME","OBSERVATION COUNT","TAXONOMIC ORDER","CATEGORY","TAXON CONCEPT ID","SPECIES COMMENTS"}
    common={"SAMPLING EVENT IDENTIFIER","OBSERVATION DATE","LATITUDE","LONGITUDE","PROTOCOL CODE","DURATION MINUTES","EFFORT DISTANCE KM","EFFORT AREA HA","NUMBER OBSERVERS","ALL SPECIES REPORTED","GROUP IDENTIFIER"}
    total=0
    with open_text(p) as h:
        rd=csv.DictReader(h,delimiter="\t")
        if rd.fieldnames is None:raise Stop("missing header")
        col={norm(k):k for k in rd.fieldnames}
        missing=sorted(common-set(col))
        if missing:raise Stop(f"missing required headers: {missing}")
        bad=sorted(forbidden & set(col))
        if bad:raise Stop(f"species-response headers forbidden: {bad}")
        variant,otype_col,pname_col=resolve_protocol_schema(contract,col)
        for row in rd:
            total+=1
            sid=str(row[col["SAMPLING EVENT IDENTIFIER"]]).strip()
            if not sid:raise Stop("blank sampling event identifier")
            d=date.fromisoformat(str(row[col["OBSERVATION DATE"]]).strip())
            lat=opt_float(row[col["LATITUDE"]],"latitude");lon=opt_float(row[col["LONGITUDE"]],"longitude")
            if lat is None or lon is None or not(-90<=lat<=90) or not(-180<=lon<=180):raise Stop("invalid coordinates")
            gid=str(row[col["GROUP IDENTIFIER"]]).strip()
            e={
              "event_key":event_key(sid,gid),"sid":sid,"year":d.year,"month":d.month,"lat":lat,"lon":lon,
              "complete":parse_bool(row[col["ALL SPECIES REPORTED"]]),
              "duration":opt_float(row[col["DURATION MINUTES"]],"duration",0),
              "distance":opt_float(row[col["EFFORT DISTANCE KM"]],"distance",0),
              "area":opt_float(row[col["EFFORT AREA HA"]],"area",0),
              "observers":opt_int(row[col["NUMBER OBSERVERS"]],"observers",1),
              "observation_type":str(row[otype_col]).strip(),
              "protocol_name":"" if pname_col is None else str(row[pname_col]).strip(),
              "protocol_code":str(row[col["PROTOCOL CODE"]]).strip()
            }
            insert_or_merge(conn,e)
            if total%100000==0:conn.commit()
    conn.commit()
    return variant,{
      "raw_checklist_rows":total,
      "deduplicated_event_keys":conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
      "conflicting_event_keys":conn.execute("SELECT COUNT(*) FROM events WHERE conflict=1").fetchone()[0]
    }

def load_geometry(p,id_field):
    try:import geopandas as gpd
    except ImportError as e:raise Stop("geopandas required") from e
    g=gpd.read_file(p)
    cols={norm(c):c for c in g.columns}
    key=norm(id_field)
    if key not in cols:raise Stop(f"missing geometry ID field {id_field}")
    if g.crs is None:raise Stop("geometry CRS missing")
    g=g[[cols[key],"geometry"]].rename(columns={cols[key]:"OBJECTID"}).to_crs("EPSG:4326")
    if g.empty or g["OBJECTID"].isna().any() or g["OBJECTID"].astype(str).duplicated().any():raise Stop("invalid OBJECTID geometry")
    return g

def map_events(conn,g,years):
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError as e:raise Stop("geopandas/shapely required") from e
    cur=conn.execute("""SELECT year,month,lat,lon,duration,distance,area,observers,observation_type,protocol_name,protocol_code
      FROM events WHERE conflict=0 AND complete=1 AND year BETWEEN ? AND ? ORDER BY event_key""",(min(years),max(years)))
    mapped=[];outside=ambiguous=0
    while True:
        batch=cur.fetchmany(50000)
        if not batch:break
        base=[{"_row":i,"year":r[0],"month":r[1],"lat":r[2],"lon":r[3],"duration":r[4],"distance":r[5],"area":r[6],
               "observers":r[7],"observation_type":r[8],"protocol_name":r[9],"protocol_code":r[10]} for i,r in enumerate(batch)]
        pts=gpd.GeoDataFrame(base,geometry=[Point(r["lon"],r["lat"]) for r in base],crs="EPSG:4326")
        j=gpd.sjoin(pts,g,how="left",predicate="intersects")
        hits=defaultdict(set)
        for _,r in j.iterrows():
            x=r.get("OBJECTID")
            if x is not None and str(x)!="nan":hits[int(r["_row"])].add(str(x))
        for i,r in enumerate(base):
            ids=hits.get(i,set())
            if not ids:outside+=1
            elif len(ids)>1:ambiguous+=1
            else:r["OBJECTID"]=next(iter(ids));mapped.append(r)
    return mapped,outside,ambiguous

def aggregate(rows,min_n,min_months):
    a=defaultdict(lambda:{"n":0,"months":set(),"dur_n":0,"dur_sum":0.0,"dist_n":0,"dist_sum":0.0,"area_n":0,"obs_n":0,"protocols":set()})
    for r in rows:
        x=a[(str(r["OBJECTID"]),int(r["year"]))];x["n"]+=1;x["months"].add(int(r["month"]))
        if r["duration"] is not None:x["dur_n"]+=1;x["dur_sum"]+=r["duration"]
        if r["distance"] is not None:x["dist_n"]+=1;x["dist_sum"]+=r["distance"]
        if r["area"] is not None:x["area_n"]+=1
        if r["observers"] is not None:x["obs_n"]+=1
        x["protocols"].add((r["observation_type"],r["protocol_name"],r["protocol_code"]))
    out=[]
    for (oid,y),x in sorted(a.items(),key=lambda z:(float(z[0][0]),z[0][1])):
        m=len(x["months"])
        out.append({"OBJECTID":oid,"year":y,"complete_deduplicated_checklists":x["n"],"distinct_months":m,
          "duration_minutes_nonmissing":x["dur_n"],"duration_minutes_sum":x["dur_sum"],
          "effort_distance_km_nonmissing":x["dist_n"],"effort_distance_km_sum":x["dist_sum"],
          "effort_area_ha_nonmissing":x["area_n"],"number_observers_nonmissing":x["obs_n"],
          "protocol_triplets":len(x["protocols"]),"surveyed":int(x["n"]>=min_n and m>=min_months)})
    return out

def write_csv(p,rows):
    fields=["OBJECTID","year","complete_deduplicated_checklists","distinct_months","duration_minutes_nonmissing","duration_minutes_sum",
      "effort_distance_km_nonmissing","effort_distance_km_sum","effort_area_ha_nonmissing","number_observers_nonmissing","protocol_triplets","surveyed"]
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("sed_file",type=Path);ap.add_argument("island_geometry",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT);ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args();c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.ebird_island_year_survey_contract.v1_155":raise Stop("contract schema drift")
    years=set(c["official_sampling_event_source"]["analysis_years"]);out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    try:
        with tempfile.TemporaryDirectory() as td:
            conn=sqlite3.connect(str(Path(td)/"events.sqlite"));init_db(conn)
            variant,counts=ingest_sed(a.sed_file,c,conn);g=load_geometry(a.island_geometry,c["island_geometry"]["id_field"])
            mapped,outside,ambiguous=map_events(conn,g,years)
        q=c["annual_survey_quality_rule"];annual=aggregate(mapped,q["complete_deduplicated_checklists_min"],q["distinct_months_min"])
        surf=out/"ebird_island_year_survey_surface.csv";write_csv(surf,annual)
        receipt={"schema":"structural.ebird_island_year_survey_result.v1_155","status":"RESPONSE_INDEPENDENT_ISLAND_YEAR_SURVEY_SURFACE_FROZEN",
          "candidate_id":c["candidate_id"],"detected_protocol_schema":variant,"sed_sha256":sha256(a.sed_file),"island_geometry_sha256":sha256(a.island_geometry),
          **counts,"mapped_complete_events":len(mapped),"outside_geometry_events":outside,"ambiguous_geometry_events":ambiguous,
          "island_year_rows":len(annual),"surveyed_island_years":sum(r["surveyed"] for r in annual),
          "distinct_surveyed_islands":len({r["OBJECTID"] for r in annual if r["surveyed"]}),
          "survey_surface_sha256":sha256(surf),"species_identity_read":False,"species_detection_read":False,
          "species_nondetection_constructed":False,"annual_species_occupancy_constructed":False,"source_loss_events_constructed":False,
          "response_access_authorized":False,"counts_as_empirical_source_loss_evidence":False};code=0
    except Exception as e:
        if isinstance(e,(KeyboardInterrupt,SystemExit)):raise
        receipt={"schema":"structural.ebird_island_year_survey_result.v1_155","status":"STOP","reason":str(e),
          "species_identity_read":False,"species_detection_read":False,"species_nondetection_constructed":False,
          "annual_species_occupancy_constructed":False,"source_loss_events_constructed":False,"response_access_authorized":False,
          "counts_as_empirical_source_loss_evidence":False};code=2
    (out/"ebird_island_year_survey_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
