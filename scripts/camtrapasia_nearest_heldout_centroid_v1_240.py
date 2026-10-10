#!/usr/bin/env python3
"""Study center vs original frozen mammal heldout island centroid distances, no species."""
import argparse,csv,hashlib,io,json,math,sys
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
R=6371.0088
def xyz(lat,lon):
    a=math.radians(lat);b=math.radians(lon)
    return (math.cos(a)*math.cos(b),math.cos(a)*math.sin(b),math.sin(a))
def hav(a,b):
    p1,p2=math.radians(a[0]),math.radians(b[0])
    dx=p2-p1;dy=math.radians(b[1]-a[1])
    q=math.sin(dx/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dy/2)**2
    return 2*R*math.asin(min(1.,math.sqrt(q)))

from camtrapasia_sites_vs_mammal_heldout_grid_v1_239 import get_source,source_sites
SOURCE_SHA="b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8"
HELD_SHA="afda05287599110c7248c5cb0c1931689a2aee40f8ff4ff5b76509aff5350715"
def check(path,sha):
 h=hashlib.sha256(path.read_bytes()).hexdigest()
 if h!=sha:raise ValueError("Official original response-safe geographic archive mismatch")
def island_id(x):
 if not x or any(k not in "0123456789" for k in x):raise ValueError("Malformed frozen island ID")
 return str(int(x))
def num(x):
 if x is None or not x.strip():raise ValueError("Missing safe coordinate")
 return float.fromhex(x) if "0x" in x.lower() else float(x)
def load_heldout(original,heldout):
 check(original,SOURCE_SHA);check(heldout,HELD_SHA)
 with heldout.open(encoding="utf-8",newline="") as f:
  r=csv.DictReader(f)
  if not {"ID","block_id","bioregion"}.issubset(r.fieldnames or []):
   raise ValueError("Frozen heldout geography metadata header missing")
  rows=list(r)
 if len(rows)!=4126:raise ValueError("Wrong original island target universe")
 ids={}
 for r in rows:
  iid=island_id(r["ID"])
  if iid in ids or not r["block_id"]:raise ValueError("Duplicate ID or blank block")
  ids[iid]=r["block_id"]
 with original.open(encoding="utf-8",newline="") as f:
  r=csv.DictReader(f)
  if not {"ID","Latitude_centroid","Longitude_centroid"}.issubset(r.fieldnames or []):
   raise ValueError("Wrong response-safe centroid schema")
  rows=list(r)
 if len(rows)!=5592:raise ValueError("Wrong old source universe")
 points={}
 for r in rows:
  iid=island_id(r["ID"])
  if iid not in ids:continue
  lat=num(r["Latitude_centroid"]);lon=num(r["Longitude_centroid"])
  if not math.isfinite(lat) or not math.isfinite(lon) or not (-90<=lat<=90 and -180<=lon<=180):
   raise ValueError("Wrong frozen WGS84 centroid")
  points[iid]=(lat,lon)
 if len(points)!=4126:raise ValueError("Old heldout centroid coverage changed")
 return ids,points
def quantile(vals,q):
 x=sorted(vals);v=(len(x)-1)*q;i=int(v);j=min(i+1,len(x)-1)
 return x[i]*(j-v)+x[j]*(v-i)
def compare(source_sites,ids,point_map):
 if len(source_sites)!=239 or sum(x["coordinates_valid"] for x in source_sites)!=239:
  raise ValueError("Camera survey point universe drift")
 keys=list(point_map)
 points=np.asarray([xyz(*point_map[i]) for i in keys],dtype=float)
 tree=cKDTree(points)
 records=[]
 for src in source_sites:
  loc=(src["lat"],src["lon"])
  pt=np.asarray(xyz(*loc),dtype=float)
  _,index=tree.query(pt,k=1)
  found=keys[int(index)]
  km=hav(loc,point_map[found])
  records.append((km,found,ids[found]))
 if len(records)!=239:raise ValueError("Missing camera study")
 distances=[x[0] for x in records]
 breaks=[0,5,25,100,math.inf]
 counts={}
 for j in range(4):
  n=sum(breaks[j]<=d<breaks[j+1] for d in distances)
  counts[["0_to_less5","5_to_less25","25_to_less100","100plus"][j]]=n
 if sum(counts.values())!=239:raise ValueError("Noninclusive buffer bins")
 radii={}
 for rad in (5,25,100):
  within=[x for x in records if x[0]<rad]
  radii[str(rad)]={"survey_study_centers":len(within),
                   "distinct_original_heldout_nearest_island_candidates":len({x[1] for x in within}),
                   "distinct_original_heldout_nearest_geographic_blocks":len({x[2] for x in within})}
 return {"schema":"structural.camtrapasia_nearest_original_heldout_centroid_result.v1_240",
  "status":"PASS_GEOGRAPHY_ONLY_STUDY_CENTER_DISTANCE_SCREEN",
  "source_study_centers":239,"original_heldout_centroids":4126,
  "nearest_heldout_centroid_distance_km":{"q25":quantile(distances,.25),"median":quantile(distances,.5),"q75":quantile(distances,.75)},
  "distance_category_study_counts":counts,"cumulative_distance_thresholds":radii,
  "center_to_centroid_does_not_establish_island_identity":True,
  "site_species_captures_accessed":0,"original_IUCN_heldout_values_read":0,
  "original_model_predictions_read":0,"external_predictive_validation_admitted":False}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("safe_geography",type=Path);p.add_argument("heldout_ids",type=Path)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
 try:
  ids,points=load_heldout(a.safe_geography,a.heldout_ids)
  result=compare(source_sites(get_source()),ids,points)
 except Exception as e:
  result={"schema":"structural.camtrapasia_nearest_original_heldout_centroid_result.v1_240",
    "status":"STOP_SAFE_SOURCE_OR_NEAREST_ISLAND_IDENTITY","reason_class":type(e).__name__,
    "site_species_captures_accessed":0,"original_IUCN_heldout_values_read":0}
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps(result,sort_keys=True))
 if result["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
