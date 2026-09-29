#!/usr/bin/env python3
"""Build response-independent global mammal R0-R2 state and source graph."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from collections import defaultdict,deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_reference_operator_contract_v1_33.json"
class Stop(RuntimeError): pass

def file_sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()

def num(x):
 s=str(x).strip()
 return float.fromhex(s) if s.lower().startswith(("0x","+0x","-0x")) else float(s)

def hav(lat1,lon1,lat2,lon2):
 r=6371.0088
 p1,p2=math.radians(lat1),math.radians(lat2)
 dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
 a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
 return 2*r*math.asin(min(1.0,math.sqrt(a)))

def connected(n,edges):
 if n<=1:return True
 adj=[[] for _ in range(n)]
 for i,j,_ in edges:
  adj[i].append(j); adj[j].append(i)
 seen={0}; q=deque([0])
 while q:
  i=q.popleft()
  for j in adj[i]:
   if j not in seen: seen.add(j); q.append(j)
 return len(seen)==n

def sym_knn(points,k):
 # points=(id,lat,lon)
 all_neighbors=[]
 for i,(_,lat,lon) in enumerate(points):
  ds=[]
  for j,(_,lat2,lon2) in enumerate(points):
   if i==j: continue
   ds.append((hav(lat,lon,lat2,lon2),j))
  ds.sort(key=lambda x:(x[0],points[x[1]][0]))
  all_neighbors.append(ds[:k])
 edges={}
 for i,ns in enumerate(all_neighbors):
  for d,j in ns:
   a,b=sorted((i,j)); edges[(a,b)]=min(d,edges.get((a,b),d))
 return [(a,b,d) for (a,b),d in sorted(edges.items())]

def zvals(vals,label):
 m=sum(vals)/len(vals); v=sum((x-m)**2 for x in vals)/len(vals); sd=math.sqrt(v)
 if not sd>0: raise Stop(f"zero variance predictor: {label}")
 return [(x-m)/sd for x in vals],m,sd

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("safe_csv",type=Path); ap.add_argument("partition",type=Path)
 ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
 ap.add_argument("--state-output",type=Path,required=True)
 ap.add_argument("--edge-output",type=Path,required=True)
 ap.add_argument("--receipt",type=Path,required=True)
 a=ap.parse_args()
 try:
  c=json.loads(a.contract.read_text())
  if c["schema"]!="structural.global_mammals_reference_operator_contract.v1_33": raise Stop("contract schema drift")
  with a.safe_csv.open("r",encoding="utf-8",newline="") as h: safe=list(csv.DictReader(h))
  with a.partition.open("r",encoding="utf-8",newline="") as h: part=list(csv.DictReader(h))
  pids={r["ID"] for r in part}
  safe=[r for r in safe if r["ID"] in pids]
  if len(safe)!=len(part): raise Stop("safe/partition retained population mismatch")
  prow={r["ID"]:r for r in part}
  fields=["Climate_velocity","Temperature_mean","Temperature_sd","Precipitation_mean","Precipitation_sd","Elevation_sd","Current_isolation","Past_isolation"]
  data=[]
  for r in safe:
   vals={f:num(r[f]) for f in fields}
   area=num(r["Area"])
   if not area>0: raise Stop("nonpositive Area")
   data.append({"ID":r["ID"],"bioregion":r["bioregion"],"lat":num(r["Latitude_centroid"]),"lon":num(r["Longitude_centroid"]),"log_Area":math.log(area),**vals})
  # graph per bioregion; a single common k is chosen as the smallest k connecting every region
  byreg=defaultdict(list)
  for row in data: byreg[row["bioregion"]].append(row)
  chosen=None; region_edges=None
  for k in range(1,21):
   candidate={}
   ok=True
   for reg,rows in byreg.items():
    pts=[(r["ID"],r["lat"],r["lon"]) for r in sorted(rows,key=lambda x:x["ID"])]
    es=sym_knn(pts,k)
    if not connected(len(pts),es): ok=False; break
    candidate[reg]=(pts,es)
   if ok: chosen=k; region_edges=candidate; break
  if chosen is None: raise Stop("no common k<=20 connects every retained bioregion")
  nearest={}; pressure={}; edges_out=[]; scales={}
  for reg,(pts,es) in region_edges.items():
   lengths=[d for _,_,d in es]
   h=statistics.median(lengths)
   if not h>0: raise Stop(f"nonpositive graph scale: {reg}")
   scales[reg]=h
   inc=defaultdict(list)
   for i,j,d in es:
    ida,idb=pts[i][0],pts[j][0]
    inc[ida].append(d); inc[idb].append(d)
    edges_out.append((reg,ida,idb,d))
   for iid,_,_ in pts:
    if not inc[iid]: raise Stop("isolated graph node")
    nearest[iid]=min(inc[iid])
    pressure[iid]=sum(math.exp(-d/h) for d in inc[iid])
  # response-independent standardization across retained population
  rawcols={
   "Climate_velocity":[r["Climate_velocity"] for r in data],
   "Temperature_mean":[r["Temperature_mean"] for r in data],
   "Temperature_sd":[r["Temperature_sd"] for r in data],
   "Precipitation_mean":[r["Precipitation_mean"] for r in data],
   "Precipitation_sd":[r["Precipitation_sd"] for r in data],
   "Elevation_sd":[r["Elevation_sd"] for r in data],
   "log_Area":[r["log_Area"] for r in data],
   "Current_isolation":[r["Current_isolation"] for r in data],
   "Past_isolation":[r["Past_isolation"] for r in data],
   "log1p_nearest_island_km":[math.log1p(nearest[r["ID"]]) for r in data],
   "generic_neighbor_pressure":[pressure[r["ID"]] for r in data]
  }
  zs={}; stats={}
  for name,vals in rawcols.items():
   z,m,sd=zvals(vals,name); zs[name]=z; stats[name]={"mean_hex":m.hex(),"sd_hex":sd.hex()}
  a.state_output.parent.mkdir(parents=True,exist_ok=True)
  header=["ID","bioregion","split","block_id"]+[f"z_{x}" for x in rawcols]
  with a.state_output.open("w",encoding="utf-8",newline="") as h:
   w=csv.writer(h,lineterminator="\n"); w.writerow(header)
   for idx,r in enumerate(data):
    p=prow[r["ID"]]
    w.writerow([r["ID"],r["bioregion"],p["split"],p["block_id"]]+[zs[x][idx].hex() for x in rawcols])
  with a.edge_output.open("w",encoding="utf-8",newline="") as h:
   w=csv.writer(h,lineterminator="\n"); w.writerow(["bioregion","from_ID","to_ID","distance_km_hex"])
   for reg,a1,b1,d in sorted(edges_out): w.writerow([reg,a1,b1,d.hex()])
  receipt={
   "schema":"structural.global_mammals_reference_operator_result.v1_33",
   "status":"R0_R2_STATE_AND_SOURCE_GRAPH_FROZEN_RESPONSE_INDEPENDENTLY",
   "retained_islands":len(data),"bioregions":len(byreg),"selected_common_k":chosen,
   "edge_count":len(edges_out),"bioregion_edge_scale_hex":{k:v.hex() for k,v in sorted(scales.items())},
   "standardization":stats,
   "state_sha256":file_sha(a.state_output),"edge_sha256":file_sha(a.edge_output),
   "Appendix1_opened":False,"species_headers_opened":False,"occurrence_values_opened":False,
   "counts_as_empirical_evidence":False,"fresh_system_denominator_contribution":0,
   "next_action":"freeze pilot-response firewall and cross-fitted R3/C species-conditioned feature formulas before any Appendix 1 access"
  }
  a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  print(json.dumps(receipt,indent=2,sort_keys=True)); return 0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
  result={"schema":"structural.global_mammals_reference_operator_result.v1_33","status":"STOP","reason":str(e),"Appendix1_opened":False,"species_headers_opened":False,"occurrence_values_opened":False,"counts_as_empirical_evidence":False,"fresh_system_denominator_contribution":0}
  a.receipt.parent.mkdir(parents=True,exist_ok=True); a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  print(json.dumps(result,indent=2,sort_keys=True)); return 2
if __name__=="__main__": raise SystemExit(main())
