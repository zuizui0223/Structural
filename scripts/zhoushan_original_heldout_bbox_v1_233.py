#!/usr/bin/env python3
"""Frozen Zhoushan rectangle vs original mammal ID/coordinate routing. No 0/1 responses."""
import argparse,csv,hashlib,json,math
from pathlib import Path
EXPECTED={
 "safe":"b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8",
 "selected":"5a04e8b64682979ee708f281418c017ff34c930bc8e51d7eff3d3437929b74b0",
 "heldout":"afda05287599110c7248c5cb0c1931689a2aee40f8ff4ff5b76509aff5350715"
}
LAT_MIN,LAT_MAX=29+31/60,30+4/60
LON_MIN,LON_MAX=121+30/60,123+25/60
def canonical(value):
 if not value or not value.isdecimal() or any(z not in "0123456789" for z in value):
  raise ValueError("Invalid frozen island ID")
 return str(int(value))
def hash_file(path,expected):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
 if h.hexdigest()!=expected:raise ValueError("Frozen archive mismatch")
def read_ids(path,expected_rows):
 with path.open("r",encoding="utf-8",newline="") as f:
  rd=csv.DictReader(f)
  if "ID" not in (rd.fieldnames or []):raise ValueError("ID header absent")
  rows=list(rd)
 if len(rows)!=expected_rows:raise ValueError("Unexpected ID routing count")
 ids=[canonical(r["ID"]) for r in rows]
 if len(set(ids))!=expected_rows:raise ValueError("Duplicate routing IDs")
 return set(ids),rows
def quant(x,p):
 if not x:return None
 a=sorted(x);y=(len(a)-1)*p;i=int(y);j=min(len(a)-1,i+1)
 return a[i]*(j-y)+a[j]*(y-i)
def execute(safe,selected,heldout):
 for path,name in [(safe,"safe"),(selected,"selected"),(heldout,"heldout")]:
  hash_file(path,EXPECTED[name])
 chosen,_=read_ids(selected,5401)
 held,held_rows=read_ids(heldout,4126)
 if not held.issubset(chosen):raise ValueError("Heldout not source selected")
 meta={canonical(r["ID"]):r for r in held_rows}
 with safe.open("r",encoding="utf-8",newline="") as f:
  rd=csv.DictReader(f)
  if not {"ID","Latitude_centroid","Longitude_centroid","Area"}.issubset(rd.fieldnames or []):
   raise ValueError("Source geography header mismatch")
  records=list(rd)
 if len(records)!=5592:raise ValueError("Source geo count drift")
 ids=set();in_rect=[]
 for r in records:
  id=canonical(r["ID"])
  if id in ids:raise ValueError("Duplicate source island ID")
  ids.add(id)
  lat=float(r["Latitude_centroid"]);lon=float(r["Longitude_centroid"]);area=float(r["Area"])
  if not math.isfinite(lat) or not math.isfinite(lon) or not math.isfinite(area):
   raise ValueError("Nonfinite source geographic cell")
  if not (-90<=lat<=90 and -180<=lon<=180 and area>0):
   raise ValueError("Invalid physical geography")
  if LAT_MIN<=lat<=LAT_MAX and LON_MIN<=lon<=LON_MAX:
   in_rect.append((id,area))
 if not chosen.issubset(ids):raise ValueError("Selected model IDs outside original safe source")
 counts={"original_safe_source":len(in_rect),
   "selected_model_nodes":sum(i in chosen for i,_ in in_rect),
   "heldout_prediction_targets":sum(i in held for i,_ in in_rect)}
 eligible=[a for i,a in in_rect if i in held]
 other=[i for i,_ in in_rect if i not in chosen]
 blocks={meta[i]["block_id"] for i,a in in_rect if i in held}
 return {
  "schema":"structural.zhoushan_heldout_geography_footprint_result.v1_233",
  "status":"GEOGRAPHIC_TARGET_UNAVAILABLE_FOR_DIRECT_TEST" if not eligible else "REGION_CANDIDATES_ONLY_NOT_CROSSWALKED_TO_s01_s39",
  "published_rectangle":{"lat_min":LAT_MIN,"lat_max":LAT_MAX,"lon_min":LON_MIN,"lon_max":LON_MAX},
  "archived_total_safe_source_islands":5592,
  "archived_total_selected_nodes":5401,"archived_heldout_islands":4126,
  "within_published_geographic_rectangle":counts,
  "within_rectangle_beyond_selected_nodes":len(other),
  "distinct_heldout_spatial_blocks":len(blocks),
  "heldout_candidate_areas_km2":{
    "n":len(eligible),"q25":quant(eligible,.25),
    "median":quant(eligible,.5),"q75":quant(eligible,.75)
  },
  "surveyed_s01_s39_site_codes_mapped_to_source_IDs":0,
  "independent_field_observation_values_read":0,
  "original_mammal_heldout_values_read":0,
  "original_mammal_predictions_read":0,
  "original_kNN_graph_rebuilt":False,
  "notes":"Region rectangle only. Some source islands may be unsurveyed; sample s01-s39 site codes lack published geodetic identity."
 }
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("source",type=Path);ap.add_argument("selected",type=Path);ap.add_argument("heldout",type=Path)
 ap.add_argument("--out",type=Path,required=True)
 opt=ap.parse_args();opt.out.parent.mkdir(parents=True,exist_ok=True)
 try: result=execute(opt.source,opt.selected,opt.heldout)
 except Exception as e:
  message=str(e)
  reason_category=("SHA" if "archive mismatch" in message else
    "selected_heldout_ID_membership" if "Heldout not source selected" in message else
    "ID_syntax" if "island ID" in message else
    "file_rows_or_columns" if "count" in message or "header" in message else
    "physical_geography_values" if "geograph" in message or "Nonfinite" in message else
    "other_frozen_source_identity")
  result={"schema":"structural.zhoushan_heldout_geography_footprint_result.v1_233",
   "status":"STOP_FROZEN_SOURCE_OR_GEOGRAPHY_SCHEMA",
   "reason_class":type(e).__name__,
   "safe_failure_category":reason_category,
   "independent_field_observation_values_read":0,
   "original_mammal_heldout_values_read":0,
   "original_mammal_predictions_read":0}
 opt.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(result,sort_keys=True))
 if result["status"].startswith("STOP_FROZEN"):raise SystemExit(2)
if __name__=="__main__":main()
