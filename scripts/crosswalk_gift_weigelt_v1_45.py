#!/usr/bin/env python3
"""Strict response-independent crosswalk from GIFT whole islands to Weigelt islands."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re,unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/gift_weigelt_crosswalk_contract_v1_45.json"
class Stop(RuntimeError): pass
TOKENS={"island","islands","isle","isles","isla","islas","ilha","ilhas","ile","iles","île","îles","isola","isole","pulau","shima","jima"}

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def norm(x):
 s=unicodedata.normalize("NFKD",str(x or ""))
 s="".join(ch for ch in s if not unicodedata.combining(ch)).casefold()
 s=re.sub(r"[^0-9a-z]+"," ",s)
 return " ".join(s.split())

def core(x):
 return " ".join(t for t in norm(x).split() if t not in TOKENS)

def fnum(x):
 try:
  v=float(str(x).strip())
 except Exception:return None
 return v if math.isfinite(v) else None

def hav(lat1,lon1,lat2,lon2):
 r=6371.0088
 p1,p2=math.radians(lat1),math.radians(lat2)
 dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
 a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
 return 2*r*math.asin(min(1.0,math.sqrt(a)))

def ratio(a,b):
 if a is None or b is None or a<=0 or b<=0:return math.inf
 return max(a,b)/min(a,b)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("gift_geo",type=Path);ap.add_argument("weigelt_safe",type=Path)
 ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
 ap.add_argument("--matched",type=Path,required=True);ap.add_argument("--excluded",type=Path,required=True);ap.add_argument("--receipt",type=Path,required=True)
 a=ap.parse_args()
 try:
  c=json.loads(a.contract.read_text())
  if c["schema"]!="structural.gift_weigelt_crosswalk_contract.v1_45":raise Stop("contract schema drift")
  if sha(a.gift_geo)!=c["input_population"]["gift_geography_sha256"]:raise Stop("GIFT geography SHA drift")
  if sha(a.weigelt_safe)!=c["input_population"]["weigelt_safe_csv_sha256"]:raise Stop("Weigelt safe SHA drift")
  with a.gift_geo.open(encoding="utf-8",newline="") as h:gifts=list(csv.DictReader(h))
  with a.weigelt_safe.open(encoding="utf-8",newline="") as h:ws=list(csv.DictReader(h))
  if len(gifts)!=1373 or len(ws)!=17883:raise Stop("input row-count drift")
  W=[]
  for r in ws:
   lat=fnum(r.get("name_lat"));lon=fnum(r.get("name_long"));area=fnum(r.get("area"))
   names={norm(r.get(k)) for k in ("island","gazetteer","name_id","name_alt") if norm(r.get(k))}
   cores={core(r.get(k)) for k in ("island","gazetteer","name_id","name_alt") if core(r.get(k))}
   W.append({"r":r,"lat":lat,"lon":lon,"area":area,"names":names,"cores":cores})
  name_index=defaultdict(list);core_index=defaultdict(list)
  for i,w in enumerate(W):
   for n in w["names"]:name_index[n].append(i)
   for n in w["cores"]:core_index[n].append(i)
  provisional=[]
  excluded=[]
  tier_counts=defaultdict(int)
  for g in gifts:
   gid=str(g["entity_ID"]);gn=norm(g.get("geo_entity"));gc=core(g.get("geo_entity"))
   glat=fnum(g.get("latitude"));glon=fnum(g.get("longitude"));ga=fnum(g.get("area"))
   if None in (glat,glon,ga) or ga<=0:
    excluded.append((gid,"gift_geography_invalid_or_missing","","",""));continue
   chosen=None
   def candidates(indices,maxd,maxr):
    out=[]
    for i in sorted(set(indices)):
     w=W[i]
     if None in (w["lat"],w["lon"],w["area"]):continue
     d=hav(glat,glon,w["lat"],w["lon"]);ar=ratio(ga,w["area"])
     if d<=maxd and ar<=maxr:out.append((i,d,ar))
    return out
   aa=candidates(name_index.get(gn,[]),25.0,2.0) if gn else []
   if len(aa)==1:chosen=("A_full_name_geo_area",)+aa[0]
   if chosen is None and gc:
    bb=candidates(core_index.get(gc,[]),10.0,1.5)
    if len(bb)==1:chosen=("B_core_name_geo_area",)+bb[0]
   if chosen is None:
    ds=[]
    for i,w in enumerate(W):
     if None in (w["lat"],w["lon"],w["area"]):continue
     d=hav(glat,glon,w["lat"],w["lon"])
     ds.append((d,i,ratio(ga,w["area"])))
    ds.sort(key=lambda z:(z[0],str(W[z[1]]["r"].get("id",""))))
    if ds:
     d,i,ar=ds[0]
     second=ds[1][0] if len(ds)>1 else math.inf
     if d<=2.0 and ar<=1.25 and second>=max(5.0,3*d):
      chosen=("C_ultrastrict_coordinate_area",i,d,ar)
   if chosen is None:
    excluded.append((gid,"no_strict_match","","",""));continue
   tier,i,d,ar=chosen;w=W[i];wid=str(w["r"]["id"])
   provisional.append({"gift":g,"w":w["r"],"tier":tier,"distance":d,"area_ratio":ar,"wid":wid})
  bywid=defaultdict(list)
  for p in provisional:bywid[p["wid"]].append(p)
  final=[]
  for p in provisional:
   if len(bywid[p["wid"]])>1:
    excluded.append((str(p["gift"]["entity_ID"]),"one_to_one_collision",p["wid"],p["tier"],f"{p['distance']:.12g}"))
   else:
    final.append(p);tier_counts[p["tier"]]+=1
  a.matched.parent.mkdir(parents=True,exist_ok=True)
  fields=["entity_ID","geo_entity","Weigelt_id","match_tier","distance_km","area_ratio","archip","Weigelt_area","dist","slmp","gmmc","elev","temp","vart","ccvt","prec","varp"]
  with a.matched.open("w",encoding="utf-8",newline="") as h:
   wri=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");wri.writeheader()
   for p in sorted(final,key=lambda z:int(float(z["gift"]["entity_ID"]))):
    wr=p["w"];g=p["gift"]
    wri.writerow({"entity_ID":g["entity_ID"],"geo_entity":g.get("geo_entity",""),"Weigelt_id":p["wid"],"match_tier":p["tier"],"distance_km":f"{p['distance']:.17g}","area_ratio":f"{p['area_ratio']:.17g}","archip":wr.get("archip",""),"Weigelt_area":wr.get("area",""),"dist":wr.get("dist",""),"slmp":wr.get("slmp",""),"gmmc":wr.get("gmmc",""),"elev":wr.get("elev",""),"temp":wr.get("temp",""),"vart":wr.get("vart",""),"ccvt":wr.get("ccvt",""),"prec":wr.get("prec",""),"varp":wr.get("varp","")})
  with a.excluded.open("w",encoding="utf-8",newline="") as h:
   wri=csv.writer(h,lineterminator="\n");wri.writerow(["entity_ID","reason","candidate_Weigelt_id","candidate_tier","candidate_distance_km"]);wri.writerows(sorted(excluded))
  receipt={"schema":"structural.gift_weigelt_crosswalk_result.v1_45","status":"STRICT_GIFT_WEIGELT_CROSSWALK_COMPLETE","input_gift_entities":len(gifts),"matched_primary_entities":len(final),"excluded_entities":len(gifts)-len(final),"match_tier_counts":dict(sorted(tier_counts.items())),"one_to_one":len({p["wid"] for p in final})==len(final),"matched_sha256":sha(a.matched),"excluded_sha256":sha(a.excluded),"species_composition_opened":False,"species_richness_computed":False,"mammal_Appendix1_opened":False,"counts_as_empirical_evidence":False,"species_response_authorized":False}
  a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(receipt,indent=2,sort_keys=True));return 0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
  out={"schema":"structural.gift_weigelt_crosswalk_result.v1_45","status":"STOP","reason":str(e),"species_composition_opened":False,"mammal_Appendix1_opened":False,"counts_as_empirical_evidence":False,"species_response_authorized":False}
  a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2,sort_keys=True));return 2
if __name__=="__main__":raise SystemExit(main())
