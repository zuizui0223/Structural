#!/usr/bin/env python3
"""Response-opaque geospatial search index of frozen 4,126 heldout island centroids."""
import argparse,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
HASH={
 "safe":"b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8",
 "selected":"5a04e8b64682979ee708f281418c017ff34c930bc8e51d7eff3d3437929b74b0",
 "heldout":"afda05287599110c7248c5cb0c1931689a2aee40f8ff4ff5b76509aff5350715"
}
def check(path,identity):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
 if h.hexdigest()!=HASH[identity]:raise ValueError("Frozen SHA mismatch: "+identity)
def canonical(value):
 if not value or any(c not in "0123456789" for c in value):
  raise ValueError("Invalid geography island ID")
 return str(int(value))
def geo_number(value):
 if value is None or not value.strip():raise ValueError("Absent coordinate")
 return float.fromhex(value) if "0x" in value.lower() else float(value)
def bin_coordinate(x,minimum,maximum,offset):
 if not math.isfinite(x) or not minimum<=x<=maximum:raise ValueError("Coordinate out of range")
 if x==maximum:
  x=math.nextafter(x,-math.inf)
 if minimum==-180 and x==180:x=-180
 lo=math.floor((x-minimum-offset)/10)*10+minimum+offset
 return (max(minimum,lo),min(maximum,lo+10))
def tile(lat,lon,shift):
 return (bin_coordinate(lat,-90,90,shift),bin_coordinate(lon,-180,180,shift))
def load(safe,selected,heldout):
 for path,k in ((safe,"safe"),(selected,"selected"),(heldout,"heldout")):check(path,k)
 with selected.open(encoding="utf-8",newline="") as f:
  r=csv.DictReader(f)
  if "ID" not in (r.fieldnames or []):raise ValueError("Selected ID absent")
  chosen={canonical(z["ID"]) for z in r}
 if len(chosen)!=5401:raise ValueError("Selected population changed")
 with heldout.open(encoding="utf-8",newline="") as f:
  r=csv.DictReader(f)
  if not {"ID","block_id","bioregion"}.issubset(r.fieldnames or []):
   raise ValueError("Heldout block metadata absent")
  routing={canonical(z["ID"]):z["block_id"] for z in r}
 if len(routing)!=4126 or not set(routing).issubset(chosen) or not all(routing.values()):
  raise ValueError("Heldout routing identity changed")
 with safe.open(encoding="utf-8",newline="") as f:
  r=csv.DictReader(f)
  if not {"ID","Latitude_centroid","Longitude_centroid"}.issubset(r.fieldnames or []):
   raise ValueError("Only response-safe coordinate schema is accepted")
  rows=list(r)
 if len(rows)!=5592:raise ValueError("Physical reference row count changed")
 loc={}
 for z in rows:
  iid=canonical(z["ID"])
  if iid in loc:raise ValueError("Duplicate safe island ID")
  lat=geo_number(z["Latitude_centroid"]);lon=geo_number(z["Longitude_centroid"])
  if not(-90<=lat<=90 and -180<=lon<=180):raise ValueError("Invalid frozen lat/lon")
  loc[iid]=(lat,lon)
 if not chosen.issubset(loc):raise ValueError("Safe geography has no selected island")
 return chosen,routing,loc
def summarize(chosen,routing,loc,shift):
 bins=defaultdict(lambda:{"selected":0,"heldout":0,"blocks":set()})
 for iid in chosen:
  lat,lon=loc[iid];key=tile(lat,lon,shift)
  r=bins[key];r["selected"]+=1
  if iid in routing:
   r["heldout"]+=1;r["blocks"].add(routing[iid])
 out=[]
 for (lat,lon),v in bins.items():
  if not v["heldout"]:continue
  out.append({"lat_min":lat[0],"lat_max":lat[1],"lon_min":lon[0],"lon_max":lon[1],
              "heldout_islands":v["heldout"],"distinct_heldout_blocks":len(v["blocks"]),
              "selected_model_islands":v["selected"]})
 out.sort(key=lambda v:(-v["distinct_heldout_blocks"],-v["heldout_islands"],v["lat_min"],v["lon_min"]))
 if sum(v["heldout_islands"] for v in out)!=4126:raise ValueError("Incomplete global heldout coverage")
 return out
def execute(safe,selected,heldout):
 ch,rt,geog=load(safe,selected,heldout)
 a=summarize(ch,rt,geog,0)
 b=summarize(ch,rt,geog,5)
 n_global=len(set(rt.values()))
 return {
  "schema":"structural.global_mammal_heldout_geographic_search_index_result.v1_235",
  "status":"PASS_GEOGRAPHY_ONLY_INDEPENDENT_SURVEY_SEARCH_INDEX",
  "original_heldout_islands":4126,
  "original_selected_model_islands":5401,
  "global_distinct_heldout_blocks":n_global,
  "primary_10deg_nonempty_tiles":len(a),
  "shifted_10deg_nonempty_tiles":len(b),
  "primary_top25":a[:25],
  "shifted_top25":b[:25],
  "primary_all_nonempty_tiles":a,
  "shifted_all_nonempty_tiles":b,
  "source_taxon_presence_values_opened":0,
  "original_IUCN_heldout_values_opened":0,
  "model_predictions_or_edges_read":0,
  "not_an_external_validated_mammal_prediction":True
 }
def main():
 p=argparse.ArgumentParser()
 p.add_argument("safe",type=Path);p.add_argument("selected",type=Path);p.add_argument("heldout",type=Path)
 p.add_argument("--out",type=Path,required=True);args=p.parse_args()
 args.out.parent.mkdir(parents=True,exist_ok=True)
 try:out=execute(args.safe,args.selected,args.heldout)
 except Exception as exc:
  out={"schema":"structural.global_mammal_heldout_geographic_search_index_result.v1_235",
       "status":"STOP_SOURCE_GEOGRAPHY_OR_ROUTING","reason_class":type(exc).__name__,
       "source_taxon_presence_values_opened":0,
       "original_IUCN_heldout_values_opened":0,"model_predictions_or_edges_read":0}
 args.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:v for k,v in out.items() if k not in ("primary_all_nonempty_tiles","shifted_all_nonempty_tiles")},sort_keys=True))
 if out["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
