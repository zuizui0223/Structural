#!/usr/bin/env python3
"""Freeze response-blind predictor universes for untouched GIFT taxonomic panels."""
from __future__ import annotations

from collections import defaultdict
import argparse, hashlib, json, math, tempfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import shapefile
from shapely.geometry import Point, shape
from shapely.ops import unary_union

BASE="https://gift.uni-goettingen.de/api/extended/"
VERSION="3.2"
ENTITY_CLASSES={"Island","Island Group","Island Part"}
NATIVE_SCOPE_WIDE={
    "all","native","native and naturalized","native and historically introduced",
    "endangered","endemic","other subset",
}
NATIVE_SCOPE_COMPLETE={
    "all","native","native and naturalized","native and historically introduced",
}
AIS_RECORD="10775810"
AIS_BASE=f"https://zenodo.org/records/{AIS_RECORD}/files/"
AIS_FILES={
    "A-Island_shape.shp":"5d79c86181abd3db43690e0832962ca518339b350465c5d87bb066695711d251",
    "A-Island_shape.shx":"3d5a60a0057cf4476a25ae2e69fc12146a082f82dc9c8b798300544026312d4d",
    "A-Island_shape.dbf":"75210dad46b516a3ff93168e9569910169dd5f0c946da4666970792d46b5e4ee",
    "A-Island_shape.prj":"a02a27b1d1982c8516d83398e85a3c8b1aef1713c13ef4d84d7bde17430c07c4",
}
CLIMATE=[
    "wc2.0_bio_30s_01","wc2.0_bio_30s_05","wc2.0_bio_30s_06",
    "wc2.0_bio_30s_12","wc2.0_bio_30s_15",
]
MISC=("area","dist","SLMP","GMMC","longitude","latitude","arch_lvl_1","arch_lvl_2","arch_lvl_3")
MIN_ARCHIPELAGO_ISLANDS=20
N_BLOCKS=4

def sha(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def s(x): return "" if x is None else str(x)
def fetch(query,**extra):
    url=BASE+f"index{VERSION}.php?"+urlencode({"query":query,**{k:str(v) for k,v in extra.items()}})
    req=Request(url,headers={"User-Agent":"Structural-GIFT-fresh-taxon-universe/0.1"})
    with urlopen(req,timeout=180) as r: raw=r.read()
    rows=json.loads(raw)
    if not isinstance(rows,list): raise RuntimeError(f"{query}: expected list")
    return rows,{"url":url,"rows":len(rows),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def eligible(lists,taxonomy,target_name,scope):
    target=next((r for r in taxonomy if s(r.get("taxon_name"))==target_name),None)
    if target is None: raise RuntimeError(f"target absent: {target_name}")
    left,right=float(target["lft"]),float(target["rgt"]); span=right-left
    tax_by={s(r["taxon_ID"]):r for r in taxonomy}
    allowed=set()
    for r in taxonomy:
        lft,rgt=float(r["lft"]),float(r["rgt"])
        if (lft>=left and rgt<=right) or (lft<left and rgt>right): allowed.add(s(r["taxon_ID"]))
    rows=[]
    for r in lists:
        if s(r.get("taxon_ID")) not in allowed: continue
        if s(r.get("subset")) not in scope: continue
        if s(r.get("entity_class")) not in ENTITY_CLASSES: continue
        if s(r.get("native_indicated"))!="1" or s(r.get("suit_geo"))!="1": continue
        if s(r.get("restricted"))=="1": continue
        tax=tax_by[s(r["taxon_ID"])]
        rr=dict(r); rr["_span"]=float(tax["rgt"])-float(tax["lft"]); rows.append(rr)
    mx=defaultdict(float)
    for r in rows: mx[s(r["entity_ID"])]=max(mx[s(r["entity_ID"])],r["_span"])
    complete={eid for eid,v in mx.items() if v>=span}
    return [r for r in rows if s(r["entity_ID"]) in complete],target
def fetch_bytes(url):
    req=Request(url,headers={"User-Agent":"Structural-GIFT-fresh-taxon-universe/0.1"})
    with urlopen(req,timeout=180) as r:return r.read()
def ais_union():
    meta={}
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for name,digest in AIS_FILES.items():
            b=fetch_bytes(AIS_BASE+name+"?download=1")
            got=hashlib.sha256(b).hexdigest()
            if got!=digest: raise RuntimeError(f"A-Islands geometry drift: {name}")
            (root/name).write_bytes(b); meta[name]={"bytes":len(b),"sha256":got}
        reader=shapefile.Reader(str(root/"A-Island_shape.shp"))
        geoms=[]
        for shp in reader.shapes():
            g=shape(shp.__geo_interface__)
            if not g.is_valid:g=g.buffer(0)
            if not g.is_empty:geoms.append(g)
        return unary_union(geoms),{"record_id":int(AIS_RECORD),"polygon_count":len(geoms),"files":meta}
def hav(lon1,lat1,lon2,lat2):
    R=6371.0088;a1,a2=map(math.radians,(lat1,lat2)); da=a2-a1;dl=math.radians(lon2-lon1)
    x=math.sin(da/2)**2+math.cos(a1)*math.cos(a2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1,math.sqrt(x)))
def balanced_blocks(ids,lon,lat,k=4):
    ids=sorted(ids,key=int); pairs=[]
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            pairs.append((hav(float(lon[a]),float(lat[a]),float(lon[b]),float(lat[b])),-int(a),-int(b),a,b))
    _,_,_,a,b=max(pairs)
    scored=[]
    for eid in ids:
        da=hav(float(lon[eid]),float(lat[eid]),float(lon[a]),float(lat[a]))
        db=hav(float(lon[eid]),float(lat[eid]),float(lon[b]),float(lat[b]))
        scored.append((da-db,int(eid),eid))
    ordered=[x[2] for x in sorted(scored)]
    base,rem=divmod(len(ordered),k);sizes=[base+(i<rem) for i in range(k)]
    out={};cur=0
    for j,size in enumerate(sizes,1):
        for eid in ordered[cur:cur+size]:out[eid]=f"B{j}"
        cur+=size
    return out,[int(x) for x in sizes]
def tail(ids,dist,f):
    ordered=sorted(ids,key=lambda eid:(-float(dist[eid]),int(eid)))
    return set(ordered[:max(1,math.ceil(len(ordered)*f))])

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--taxon-name",required=True);args=ap.parse_args()
    taxon=args.taxon_name
    lists,lm=fetch("lists"); taxonomy,tm=fetch("taxonomy")
    wide,target=eligible(lists,taxonomy,taxon,NATIVE_SCOPE_WIDE)
    comp,_=eligible(lists,taxonomy,taxon,NATIVE_SCOPE_COMPLETE)
    compids={s(r["entity_ID"]) for r in comp}
    sel=[r for r in wide if s(r["entity_ID"]) in compids and s(r.get("entity_class"))=="Island"]
    islands={s(r["entity_ID"]) for r in sel}
    lists_by=defaultdict(set)
    for r in sel:lists_by[s(r["entity_ID"])].add(s(r["list_ID"]))

    misc={};mm={}
    for var in MISC:
        rows,m=fetch("geoentities_env_misc",envvar=var);misc[var]={s(r["entity_ID"]):r.get(var) for r in rows};mm[var]=m
    climate={};cm={}
    for layer in CLIMATE:
        rows,m=fetch("geoentities_env_raster",layername=layer,sumstat="mean")
        climate[layer]={s(r["entity_ID"]):r.get("mean") for r in rows};cm[layer]=m
    complete={
        eid for eid in islands
        if all(misc[v].get(eid) not in (None,"") for v in ("area","dist","SLMP","GMMC","longitude","latitude"))
        and all(climate[l].get(eid) not in (None,"") for l in CLIMATE)
        and any(misc[v].get(eid) not in (None,"") for v in ("arch_lvl_1","arch_lvl_2","arch_lvl_3"))
    }
    paths={}
    for eid in complete:
        p=tuple(s(misc[v].get(eid)).strip() for v in ("arch_lvl_1","arch_lvl_2","arch_lvl_3") if misc[v].get(eid) not in (None,""))
        if p:paths[eid]=p

    union,ais=ais_union()
    overlap={eid for eid in complete if union.covers(Point(float(misc["longitude"][eid]),float(misc["latitude"][eid])))}
    contaminated={paths[eid] for eid in overlap if eid in paths}
    clean={eid for eid in complete if paths.get(eid) not in contaminated}

    groups=defaultdict(list)
    for eid in clean:
        if eid in paths:groups[paths[eid]].append(eid)
    groups={p:sorted(ids,key=int) for p,ids in groups.items() if len(ids)>=MIN_ARCHIPELAGO_ISLANDS}
    final_ids=sorted({eid for ids in groups.values() for eid in ids},key=int)
    q75=tail(final_ids,misc["dist"],0.25);q70=tail(final_ids,misc["dist"],0.30);q80=tail(final_ids,misc["dist"],0.20)

    grows=[]
    for path,ids in sorted(groups.items()):
        blocks,sizes=balanced_blocks(ids,misc["longitude"],misc["latitude"],N_BLOCKS)
        e=sum(eid in q75 for eid in ids); ne=len(ids)-e
        grows.append({
            "archipelago_id":" / ".join(path),"archipelago_path":list(path),"n_islands":len(ids),
            "entity_ids":ids,
            "q75_extreme_n":e,"q75_nonextreme_n":ne,
            "support_class":"paired" if e>=3 and ne>=3 else "extreme_only" if e>=3 else "nonextreme_only" if ne>=3 else "neither",
            "gmmc_connected_fraction":sum(int(float(misc["GMMC"][eid])) for eid in ids)/len(ids),
            "block_sizes":sizes,
            "list_ids":sorted({lid for eid in ids for lid in lists_by[eid]},key=int),
            "membership_sha256":sha(ids),
            "block_assignment_sha256":sha(sorted((eid,blocks[eid]) for eid in ids)),
        })
    sc=defaultdict(int)
    for r in grows:sc[r["support_class"]]+=1

    payload={
        "schema":"structural.gift_fresh_taxon_universe.v0_1",
        "status":"RESPONSE_SEALED_PREDICTOR_UNIVERSE",
        "gift_version":VERSION,"taxon_name":taxon,"taxon_ID":s(target["taxon_ID"]),
        "species_composition_endpoint_called":False,"response_values_accessed":False,
        "filters":{"complete_taxon":True,"complete_floristic":True,"native_indicated":True,"suit_geo":True,"public_only":True,"minimum_archipelago_islands":MIN_ARCHIPELAGO_ISLANDS},
        "closed_aislands_exclusion":{"exact_overlap_islands":len(overlap),"contaminated_archipelago_paths":[list(x) for x in sorted(contaminated)],"geometry":ais},
        "extreme_rule":{"primary":"global upper 25% of final eligible islands by GIFT dist","q70_nonrescuing":len(q70),"q75":len(q75),"q80_nonrescuing":len(q80)},
        "n_final_archipelagos":len(grows),"n_final_islands":len(final_ids),"support_class_counts":dict(sorted(sc.items())),
        "groups":grows,
        "source_sha256":{"lists":lm["sha256"],"taxonomy":tm["sha256"],"misc":{k:v["sha256"] for k,v in mm.items()},"climate":{k:v["sha256"] for k,v in cm.items()}},
    }
    payload["universe_fingerprint"]=sha({
        "taxon_name":taxon,"filters":payload["filters"],"closed":payload["closed_aislands_exclusion"],
        "extreme_rule":payload["extreme_rule"],"groups":[(g["archipelago_id"],g["membership_sha256"],g["block_assignment_sha256"]) for g in grows],
        "source_sha256":payload["source_sha256"],
    })
    print(json.dumps(payload,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
