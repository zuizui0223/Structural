#!/usr/bin/env python3
"""Response-independent audit of eBird Sampling Event Data.

Accepts current (EBD/SED v1.16+) and legacy pre-v1.16 protocol headers without
changing ecological semantics. Species-response columns are still forbidden.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/ebird_sampling_event_metadata_audit_contract_v1_154.json"

class Stop(RuntimeError):
    pass

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

def parse_optional_float(x:str,label:str,minimum:float|None=None):
    s=str(x).strip()
    if s=="": return None
    try: v=float(s)
    except ValueError as e: raise Stop(f"invalid {label}: {s!r}") from e
    if not math.isfinite(v): raise Stop(f"nonfinite {label}")
    if minimum is not None and v<minimum: raise Stop(f"{label} below minimum")
    return v

def parse_optional_int(x:str,label:str,minimum:int|None=None):
    s=str(x).strip()
    if s=="": return None
    try:
        if any(ch in s for ch in ".eE"):
            v0=float(s)
            if not v0.is_integer(): raise ValueError
            v=int(v0)
        else:
            v=int(s)
    except ValueError as e: raise Stop(f"invalid {label}: {s!r}") from e
    if minimum is not None and v<minimum: raise Stop(f"{label} below minimum")
    return v

def duration_bin(v):
    if v is None:return "missing"
    if v<=5:return "0-5"
    if v<=15:return "6-15"
    if v<=30:return "16-30"
    if v<=60:return "31-60"
    if v<=120:return "61-120"
    return ">120"

def distance_bin(v):
    if v is None:return "missing"
    if v==0:return "0"
    if v<=1:return "(0,1]"
    if v<=5:return "(1,5]"
    if v<=10:return "(5,10]"
    return ">10"

def observers_bin(v):
    if v is None:return "missing"
    if v==1:return "1"
    if v==2:return "2"
    if v<=5:return "3-5"
    return ">5"

def write_csv(path:Path,fieldnames:list[str],rows:list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fieldnames,lineterminator="\n")
        w.writeheader();w.writerows(rows)

def resolve_protocol_schema(contract:dict,col:dict[str,str]):
    variants=contract["input"]["protocol_schema_variants"]
    matched=[]
    for name,spec in variants.items():
        if set(spec["required_headers"]) <= set(col):
            matched.append(name)
    if not matched:
        expected={name:spec["required_headers"] for name,spec in variants.items()}
        raise Stop(f"no supported SED protocol-header schema matched: {expected}")
    if len(matched)>1:
        raise Stop(f"ambiguous SED protocol-header schema: {matched}")
    name=matched[0]
    spec=variants[name]
    obs_header=spec["observation_type_header"]
    pname_header=spec["protocol_name_header"]
    return name,col[obs_header],(None if pname_header is None else col[pname_header])

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("sed_file",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()

    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    if contract.get("schema")!="structural.ebird_sampling_event_metadata_audit_contract.v1_154":
        raise Stop("contract schema drift")
    years=set(contract["input"]["analysis_years"])

    total=complete=incomplete=outside=0
    seen=set()
    group_counts=Counter()
    protocol_counts=Counter()
    year_rows=defaultdict(lambda:{"rows":0,"complete":0,"incomplete":0,"months":set()})
    year_month=defaultdict(lambda:{"rows":0,"complete":0})
    effort_counts=Counter()
    blank_observation_type=blank_protocol_name=blank_protocol_code=0
    detected_protocol_schema=None

    with open_text(args.sed_file) as h:
        reader=csv.DictReader(h,delimiter="\t")
        if reader.fieldnames is None: raise Stop("missing header")
        original=list(reader.fieldnames)
        normalized=[norm_header(x) for x in original]
        if len(normalized)!=len(set(normalized)): raise Stop("duplicate normalized headers")
        col={norm_header(k):k for k in original}
        required=set(contract["input"]["required_common_headers"])
        forbidden=set(contract["input"]["forbidden_species_headers"])
        missing=sorted(required-set(col))
        if missing: raise Stop(f"missing required SED headers: {missing}")
        present_forbidden=sorted(forbidden & set(col))
        if present_forbidden:
            raise Stop(f"species-response headers found; expected Sampling Event Data only: {present_forbidden}")
        detected_protocol_schema,observation_type_col,protocol_name_col=resolve_protocol_schema(contract,col)

        for row in reader:
            total+=1
            sid=str(row[col["SAMPLING EVENT IDENTIFIER"]]).strip()
            if not sid: raise Stop("blank sampling event identifier")
            if sid in seen: raise Stop(f"duplicate sampling event identifier: {sid}")
            seen.add(sid)

            ds=str(row[col["OBSERVATION DATE"]]).strip()
            try: d=date.fromisoformat(ds)
            except ValueError as e: raise Stop(f"invalid observation date: {ds!r}") from e

            lat=parse_optional_float(row[col["LATITUDE"]],"latitude")
            lon=parse_optional_float(row[col["LONGITUDE"]],"longitude")
            if lat is None or lon is None: raise Stop("blank checklist coordinates")
            if not (-90<=lat<=90): raise Stop("latitude out of range")
            if not (-180<=lon<=180): raise Stop("longitude out of range")

            comp=parse_bool(row[col["ALL SPECIES REPORTED"]])
            if comp: complete+=1
            else: incomplete+=1

            otype=str(row[observation_type_col]).strip()
            pname="" if protocol_name_col is None else str(row[protocol_name_col]).strip()
            pcode=str(row[col["PROTOCOL CODE"]]).strip()
            if not otype: blank_observation_type+=1
            if protocol_name_col is not None and not pname: blank_protocol_name+=1
            if not pcode: blank_protocol_code+=1
            protocol_counts[(otype,pname,pcode,comp)]+=1

            dur=parse_optional_float(row[col["DURATION MINUTES"]],"duration minutes",0)
            dist=parse_optional_float(row[col["EFFORT DISTANCE KM"]],"effort distance km",0)
            area=parse_optional_float(row[col["EFFORT AREA HA"]],"effort area ha",0)
            obs=parse_optional_int(row[col["NUMBER OBSERVERS"]],"number observers",1)
            effort_counts[("duration_minutes",duration_bin(dur),comp)]+=1
            effort_counts[("effort_distance_km",distance_bin(dist),comp)]+=1
            effort_counts[("number_observers",observers_bin(obs),comp)]+=1
            effort_counts[("effort_area_ha","missing" if area is None else "present",comp)]+=1

            gid=str(row[col["GROUP IDENTIFIER"]]).strip()
            if gid: group_counts[gid]+=1

            if d.year in years:
                yr=year_rows[d.year]
                yr["rows"]+=1;yr["complete"]+=int(comp);yr["incomplete"]+=int(not comp);yr["months"].add(d.month)
                ym=year_month[(d.year,d.month)]
                ym["rows"]+=1;ym["complete"]+=int(comp)
            else:
                outside+=1

    if total==0: raise Stop("SED contains zero checklist rows")

    repeated_groups=sum(1 for n in group_counts.values() if n>1)
    rows_in_repeated_groups=sum(n for n in group_counts.values() if n>1)

    yrows=[]
    for y in sorted(years):
        r=year_rows[y]
        yrows.append({
          "year":y,"checklists":r["rows"],"complete_checklists":r["complete"],
          "incomplete_checklists":r["incomplete"],"distinct_months":len(r["months"])
        })
    ymrows=[{
      "year":y,"month":m,"checklists":year_month[(y,m)]["rows"],
      "complete_checklists":year_month[(y,m)]["complete"]
    } for y in sorted(years) for m in range(1,13)]

    prows=[{
      "observation_type":k[0],"protocol_name":k[1],"protocol_code":k[2],
      "all_species_reported":str(k[3]).upper(),"checklists":n
    } for k,n in sorted(protocol_counts.items(),key=lambda z:(z[0][0],z[0][1],z[0][2],z[0][3]))]

    erows=[{
      "field":k[0],"bin":k[1],"all_species_reported":str(k[2]).upper(),"checklists":n
    } for k,n in sorted(effort_counts.items())]

    out=args.output_dir
    write_csv(out/"ebird_sed_year_support.csv",
              ["year","checklists","complete_checklists","incomplete_checklists","distinct_months"],yrows)
    write_csv(out/"ebird_sed_year_month_support.csv",
              ["year","month","checklists","complete_checklists"],ymrows)
    write_csv(out/"ebird_sed_protocol_counts.csv",
              ["observation_type","protocol_name","protocol_code","all_species_reported","checklists"],prows)
    write_csv(out/"ebird_sed_effort_bins.csv",
              ["field","bin","all_species_reported","checklists"],erows)

    receipt={
      "schema":"structural.ebird_sampling_event_metadata_audit_result.v1_154",
      "status":"SED_SCHEMA_AND_COVERAGE_AUDIT_COMPLETE_RESPONSE_INDEPENDENTLY",
      "candidate_id":contract["candidate_id"],
      "detected_protocol_schema":detected_protocol_schema,
      "checklist_rows":total,
      "unique_sampling_event_identifiers":len(seen),
      "complete_checklists":complete,
      "incomplete_checklists":incomplete,
      "rows_outside_2002_2019":outside,
      "years_with_any_checklists":sum(year_rows[y]["rows"]>0 for y in years),
      "years_with_complete_checklists":sum(year_rows[y]["complete"]>0 for y in years),
      "nonblank_group_identifiers":len(group_counts),
      "repeated_group_identifiers":repeated_groups,
      "rows_in_repeated_groups":rows_in_repeated_groups,
      "blank_observation_type_rows":blank_observation_type,
      "blank_protocol_name_rows":blank_protocol_name,
      "blank_protocol_code_rows":blank_protocol_code,
      "species_headers_seen":0,
      "species_values_read":0,
      "species_nondetections_constructed":0,
      "raw_sampling_event_rows_persisted":False,
      "final_island_year_quality_rule_frozen":False,
      "response_access_authorized":False,
      "counts_as_empirical_evidence":False
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"ebird_sed_schema_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
