#!/usr/bin/env python3
"""Build deterministic eBird three-wave windows from frozen survey support only."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/ebird_three_wave_design_contract_v1_158.json"

class Stop(RuntimeError): pass

def rank_sha(window_id:str)->str:
    return hashlib.sha256(("ebird-three-wave-v1.158|"+window_id).encode("utf-8")).hexdigest()

def file_sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def load_surface(path:Path,required_fields:list[str]):
    with path.open("r",encoding="utf-8",newline="") as h:
        rows=list(csv.DictReader(h))
    if not rows: raise Stop("empty survey surface")
    if list(rows[0].keys()) != required_fields:
        raise Stop("survey surface header/order drift")
    seen=set(); out=[]
    for r in rows:
        oid=str(r["OBJECTID"]).strip()
        if not oid: raise Stop("blank OBJECTID")
        try:
            year=int(r["year"]); surveyed=int(r["surveyed"])
        except Exception as e:
            raise Stop("invalid year/surveyed") from e
        if surveyed not in (0,1): raise Stop("surveyed outside 0/1")
        key=(oid,year)
        if key in seen: raise Stop("duplicate OBJECTID-year")
        seen.add(key); out.append((oid,year,surveyed))
    return out

def build(rows,contract):
    analysis_years=set(int(x) for x in contract["input"]["analysis_years"])
    by_year={y:set() for y in analysis_years}
    for oid,year,surveyed in rows:
        if year in by_year and surveyed==1:
            by_year[year].add(oid)

    floor=int(contract["window_support_rule"]["minimum_common_surveyed_islands"])
    windows=[]; common_by_window={}
    for w in contract["candidate_windows"]:
        t0,t1,t2=int(w["t0"]),int(w["t1"]),int(w["t2"])
        common=by_year[t0] & by_year[t1] & by_year[t2]
        common_by_window[w["window_id"]]=common
        windows.append({
          "window_id":w["window_id"],"t0":t0,"t1":t1,"t2":t2,
          "surveyed_t0":len(by_year[t0]),"surveyed_t1":len(by_year[t1]),"surveyed_t2":len(by_year[t2]),
          "common_surveyed_islands":len(common),
          "eligible":1 if len(common)>=floor else 0,
          "partition":"ineligible",
          "rank_sha256":rank_sha(w["window_id"])
        })

    eligible=[r for r in windows if r["eligible"]==1]
    min_windows=int(contract["window_qualification"]["minimum_eligible_windows"])
    if len(eligible)<min_windows:
        raise Stop(f"eligible windows {len(eligible)} < required {min_windows}")

    eligible=sorted(eligible,key=lambda r:(r["rank_sha256"],r["window_id"]))
    pilot_count=max(1,len(eligible)-4)
    min_confirm=int(contract["partition_rule"]["minimum_confirmatory_windows"])
    if len(eligible)-pilot_count < min_confirm:
        raise Stop("confirmatory window minimum not met")

    pilot_ids={r["window_id"] for r in eligible[:pilot_count]}
    confirm_ids={r["window_id"] for r in eligible[pilot_count:]}
    for r in windows:
        if r["window_id"] in pilot_ids: r["partition"]="pilot"
        elif r["window_id"] in confirm_ids: r["partition"]="confirmatory"

    islands=[]
    for r in windows:
        if r["partition"] not in ("pilot","confirmatory"): continue
        for oid in sorted(common_by_window[r["window_id"]],key=lambda x:(len(x),x)):
            islands.append({"window_id":r["window_id"],"partition":r["partition"],"OBJECTID":oid})
    return windows,islands

def write_csv(path:Path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n")
        w.writeheader();w.writerows(rows)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("survey_surface",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--windows-output",type=Path,required=True)
    ap.add_argument("--islands-output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text(encoding="utf-8"))
        if c.get("schema")!="structural.ebird_three_wave_design_contract.v1_158":
            raise Stop("contract schema drift")
        rows=load_surface(a.survey_surface,c["input"]["required_columns"])
        windows,islands=build(rows,c)
        write_csv(a.windows_output,windows,c["required_window_output_fields"])
        write_csv(a.islands_output,islands,c["required_island_output_fields"])
        pilot=[r for r in windows if r["partition"]=="pilot"]
        confirm=[r for r in windows if r["partition"]=="confirmatory"]
        result={
          "schema":"structural.ebird_three_wave_design_result.v1_158",
          "status":"RESPONSE_INDEPENDENT_THREE_WAVE_DESIGN_FROZEN",
          "candidate_id":c["candidate_id"],
          "candidate_windows":len(windows),
          "eligible_windows":len(pilot)+len(confirm),
          "pilot_windows":len(pilot),
          "confirmatory_windows":len(confirm),
          "pilot_window_ids":[r["window_id"] for r in pilot],
          "confirmatory_window_ids":[r["window_id"] for r in confirm],
          "pilot_window_island_rows":sum(1 for r in islands if r["partition"]=="pilot"),
          "confirmatory_window_island_rows":sum(1 for r in islands if r["partition"]=="confirmatory"),
          "windows_sha256":file_sha(a.windows_output),
          "islands_sha256":file_sha(a.islands_output),
          "species_identity_opened":False,
          "species_detection_opened":False,
          "species_nondetection_constructed":False,
          "annual_species_occupancy_constructed":False,
          "source_loss_events_constructed":False,
          "t2_outcome_opened":False,
          "counts_as_empirical_source_loss_evidence":False
        }
        code=0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,Stop) as e:
        result={
          "schema":"structural.ebird_three_wave_design_result.v1_158",
          "status":"STOP","reason":str(e),
          "species_identity_opened":False,
          "species_detection_opened":False,
          "species_nondetection_constructed":False,
          "annual_species_occupancy_constructed":False,
          "source_loss_events_constructed":False,
          "t2_outcome_opened":False,
          "counts_as_empirical_source_loss_evidence":False
        }
        code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__": raise SystemExit(main())
