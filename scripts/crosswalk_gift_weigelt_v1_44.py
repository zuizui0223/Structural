#!/usr/bin/env python3
"""Strict response-independent crosswalk from GIFT whole islands to Weigelt islands."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re,unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/gift_weigelt_crosswalk_contract_v1_44.json"
class Stop(RuntimeError): pass

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()

def norm(s):
 s=unicodedata.normalize("NFKD",str(s or ""))
 s="".join(ch for ch in s if not unicodedata.combining(ch)).casefold()
 s=re.sub(r"[^0-9a-z]+"," ",s)
 return " ".join(s.split())

def split_alt(s):
 return [x for x in re.split(r"[;|]",str(s or "")) if norm(x)]

def fnum(x):
 try:
  v=float(str(x).strip())
 except Exception:
  return None
 return v if math.isfinite(v) else None

def area_ratio(a,b):
 if a is None or b is None or a<=0 or b<=0: return math.inf
 return max(a,b)/min(a,b)

def hav(lat1,lon1,lat2,lon2):
 r=6371.0088
 p1,p2=math.radians(lat1),math.radians(lat2)
 dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
 a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
 return 2*r*math.asin(min(1.0,math.sqrt(a)))

def unique_nearest(source,targets,ratio_limit):
 # source has lat/lon/area, targets iterable records with lat/lon/area/id
 vals=[]
 for t in targets:
  if area_ratio(source["area"],t["area"])>ratio_limit: continue
  d=hav(source["lat"],source["lon"],t["lat"],t["lon"])
  vals.append((d,t["id"]))
 if not vals: return None
 vals.sort()
 if len(vals)>1 and abs(vals[0][0]-vals[1][0])<=1e-12: return None
 return vals[0]

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("gift_geo",type=Path); ap.add_argument("weigelt",type=Path)
 ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
 ap.add_argument("--output-crosswalk",type=Path,required=True)
 ap.add_argument("--output-unmatched",type=Path,required=True)
 ap.add_argument("--receipt",type=Path,required=True)
 a=ap.parse_args()
 try:
  c=json.loads(a.contract.read_text())
  if c["schema"]!="structural.gift_weigelt_crosswalk_contract.v1_44": raise Stop("contract schema drift")
  if sha(a.gift_geo)!=c["gift_input"]["geography_sha256"]: raise Stop("GIFT geography SHA mismatch")
  if sha(a.weigelt)!=c["weigelt_input"]["safe_csv_sha256"]: raise Stop("Weigelt safe CSV SHA mismatch")
  with a.gift_geo.open(encoding="utf-8",newline="") as h: grows=list(csv.DictReader(h))
  with a.weigelt.open(encoding="utf-8",newline="") as h: wrows=list(csv.DictReader(h))
  if len(grows)!=c["gift_input"]["islands"]: raise Stop("GIFT island count drift")
  if len(wrows)!=c["weigelt_input"]["islands"]: raise Stop("Weigelt island count drift")

  gifts=[]
  for r in grows:
   lat,lon,area=fnum(r["latitude"]),fnum(r["longitude"]),fnum(r["area"])
   if lat is None or lon is None or area is None or area<=0: raise Stop("invalid frozen GIFT geography")
   gifts.append({"id":str(r["entity_ID"]),"name":str(r["geo_entity"]),"nname":norm(r["geo_entity"]),"lat":lat,"lon":lon,"area":area})

  ws=[]; name_index={}
  for r in wrows:
   wid=str(r["id"])
   area=fnum(r["area"]); lat=fnum(r.get("name_lat","")); lon=fnum(r.get("name_long",""))
   names=[r.get("island","")]+split_alt(r.get("name_alt",""))
   nn=sorted({norm(x) for x in names if norm(x)})
   rec={"id":wid,"area":area,"lat":lat,"lon":lon,"names":nn,"row":r}
   ws.append(rec)
   for n in nn: name_index.setdefault(n,[]).append(rec)

  matches={}; used=set()
  # Tier A: exact normalized name plus area, unique candidate.
  for g in sorted(gifts,key=lambda x:(int(x["id"]) if x["id"].isdigit() else x["id"])):
   cand=[w for w in name_index.get(g["nname"],[]) if area_ratio(g["area"],w["area"])<=2.0 and w["id"] not in used]
   ids={w["id"] for w in cand}
   if len(ids)==1:
    w=next(w for w in cand if w["id"] in ids)
    matches[g["id"]]=(w,"A_exact_name_area",None,area_ratio(g["area"],w["area"]))
    used.add(w["id"])

  # Tier B: strict mutual-nearest geography among unmatched support.
  ug=[g for g in gifts if g["id"] not in matches]
  uw=[w for w in ws if w["id"] not in used and w["lat"] is not None and w["lon"] is not None and w["area"] is not None and w["area"]>0]
  g_to_w={}
  for g in ug:
   z=unique_nearest(g,uw,1.25)
   if z is not None: g_to_w[g["id"]]=z
  # Reverse unique nearest.
  w_to_g={}
  for w in uw:
   src={"lat":w["lat"],"lon":w["lon"],"area":w["area"]}
   targets=[{"id":g["id"],"lat":g["lat"],"lon":g["lon"],"area":g["area"]} for g in ug]
   z=unique_nearest(src,targets,1.25)
   if z is not None: w_to_g[w["id"]]=z
  w_by_id={w["id"]:w for w in uw}
  g_by_id={g["id"]:g for g in ug}
  for gid,(d,wid) in sorted(g_to_w.items()):
   rev=w_to_g.get(wid)
   if rev is None or rev[1]!=gid or d>5.0: continue
   if wid in used: continue
   g=g_by_id[gid]; w=w_by_id[wid]
   matches[gid]=(w,"B_mutual_nearest_strict",d,area_ratio(g["area"],w["area"]))
   used.add(wid)

  if len({m[0]["id"] for m in matches.values()})!=len(matches): raise Stop("crosswalk not one-to-one")
  gift_by={g["id"]:g for g in gifts}
  a.output_crosswalk.parent.mkdir(parents=True,exist_ok=True)
  fields=["entity_ID","geo_entity","weigelt_id","match_tier","distance_km","area_ratio",
          "weigelt_area","dist","slmp","gmmc","elev","temp","vart","ccvt","prec","varp","archip","countryiso"]
  with a.output_crosswalk.open("w",encoding="utf-8",newline="") as h:
   wri=csv.DictWriter(h,fieldnames=fields,lineterminator="\n"); wri.writeheader()
   for gid in sorted(matches,key=lambda x:(int(x) if x.isdigit() else x)):
    wr,tier,d,ratio=matches[gid]; rr=wr["row"]; g=gift_by[gid]
    wri.writerow({"entity_ID":gid,"geo_entity":g["name"],"weigelt_id":wr["id"],"match_tier":tier,
      "distance_km":"" if d is None else format(d,".12g"),"area_ratio":format(ratio,".12g"),
      "weigelt_area":rr["area"],"dist":rr["dist"],"slmp":rr["slmp"],"gmmc":rr["gmmc"],"elev":rr["elev"],
      "temp":rr["temp"],"vart":rr["vart"],"ccvt":rr["ccvt"],"prec":rr["prec"],"varp":rr["varp"],
      "archip":rr["archip"],"countryiso":rr["countryiso"]})
  unmatched=[g for g in gifts if g["id"] not in matches]
  with a.output_unmatched.open("w",encoding="utf-8",newline="") as h:
   wri=csv.DictWriter(h,fieldnames=["entity_ID","geo_entity"],lineterminator="\n"); wri.writeheader()
   for g in sorted(unmatched,key=lambda x:(int(x["id"]) if x["id"].isdigit() else x["id"])):
    wri.writerow({"entity_ID":g["id"],"geo_entity":g["name"]})
  tiers={}
  for _,tier,_,_ in matches.values(): tiers[tier]=tiers.get(tier,0)+1
  result={"schema":"structural.gift_weigelt_crosswalk_result.v1_44","status":"STRICT_COMMON_GEOGRAPHY_CROSSWALK_COMPLETE",
    "input_GIFT_islands":len(gifts),"input_Weigelt_islands":len(ws),"matched_GIFT_islands":len(matches),
    "unmatched_GIFT_islands":len(unmatched),"match_tier_counts":tiers,
    "crosswalk_sha256":sha(a.output_crosswalk),"unmatched_sha256":sha(a.output_unmatched),
    "plant_species_composition_opened":False,"plant_species_richness_computed":False,
    "mammal_Appendix1_reopened":False,"counts_as_empirical_evidence":False}
  code=0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
  result={"schema":"structural.gift_weigelt_crosswalk_result.v1_44","status":"STOP","reason":str(e),
    "plant_species_composition_opened":False,"mammal_Appendix1_reopened":False,"counts_as_empirical_evidence":False}; code=2
 a.receipt.parent.mkdir(parents=True,exist_ok=True); a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps(result,indent=2,sort_keys=True)); return code
if __name__=="__main__": raise SystemExit(main())
