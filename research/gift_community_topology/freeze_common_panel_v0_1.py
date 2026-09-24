#!/usr/bin/env python3
"""Freeze a common-island predictor panel for a fresh GIFT community-richness study.

No checklist/species-composition endpoint is called. The response surface is
restricted to archipelagos never opened in any prior GIFT burned pilot.
"""
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
TARGETS=("Angiospermae","Pteridophyta","Gymnospermae")
ENTITY_CLASSES={"Island","Island Group","Island Part"}
NATIVE_SCOPE_WIDE={
    "all","native","native and naturalized","native and historically introduced",
    "endangered","endemic","other subset",
}
NATIVE_SCOPE_COMPLETE={
    "all","native","native and naturalized","native and historically introduced",
}
MIN_ARCHIPELAGO_ISLANDS=8
RADII=(25.0,50.0,125.0,250.0)
CLIMATE=(
    "wc2.0_bio_30s_01","wc2.0_bio_30s_05","wc2.0_bio_30s_06",
    "wc2.0_bio_30s_12","wc2.0_bio_30s_15",
)
MISC=("area","dist","SLMP","GMMC","longitude","latitude","arch_lvl_1","arch_lvl_2","arch_lvl_3")

AIS_RECORD="10775810"
AIS_BASE=f"https://zenodo.org/records/{AIS_RECORD}/files/"
AIS_FILES={
    "A-Island_shape.shp":"5d79c86181abd3db43690e0832962ca518339b350465c5d87bb066695711d251",
    "A-Island_shape.shx":"3d5a60a0057cf4476a25ae2e69fc12146a082f82dc9c8b798300544026312d4d",
    "A-Island_shape.dbf":"75210dad46b516a3ff93168e9569910169dd5f0c946da4666970792d46b5e4ee",
    "A-Island_shape.prj":"a02a27b1d1982c8516d83398e85a3c8b1aef1713c13ef4d84d7bde17430c07c4",
}

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def s(x): return "" if x is None else str(x)

def fetch(query,**extra):
    url=BASE+f"index{VERSION}.php?"+urlencode({"query":query,**{k:str(v) for k,v in extra.items()}})
    req=Request(url,headers={"User-Agent":"Structural-GIFT-community-topology/0.1"})
    with urlopen(req,timeout=180) as r: raw=r.read()
    rows=json.loads(raw)
    if not isinstance(rows,list): raise RuntimeError(f"{query}: expected list")
    return rows,{"url":url,"rows":len(rows),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def eligible(lists,taxonomy,target_name,scope,checklist_refs):
    target=next((r for r in taxonomy if s(r.get("taxon_name"))==target_name),None)
    if target is None: raise RuntimeError(f"target absent: {target_name}")
    left,right=float(target["lft"]),float(target["rgt"]); span=right-left
    tax_by={s(r["taxon_ID"]):r for r in taxonomy}
    allowed=set()
    for r in taxonomy:
        lft,rgt=float(r["lft"]),float(r["rgt"])
        if (lft>=left and rgt<=right) or (lft<left and rgt>right):
            allowed.add(s(r["taxon_ID"]))
    rows=[]
    for r in lists:
        if s(r.get("taxon_ID")) not in allowed: continue
        if s(r.get("subset")) not in scope: continue
        if s(r.get("entity_class")) not in ENTITY_CLASSES: continue
        if s(r.get("native_indicated"))!="1" or s(r.get("suit_geo"))!="1": continue
        if s(r.get("restricted"))=="1": continue
        if s(r.get("ref_ID")) not in checklist_refs: continue
        tax=tax_by.get(s(r["taxon_ID"]))
        if tax is None: continue
        rr=dict(r); rr["_span"]=float(tax["rgt"])-float(tax["lft"]); rows.append(rr)
    mx=defaultdict(float)
    for r in rows: mx[s(r["entity_ID"])]=max(mx[s(r["entity_ID"])],r["_span"])
    complete={eid for eid,v in mx.items() if v>=span}
    return [r for r in rows if s(r["entity_ID"]) in complete],target

def fetch_bytes(url):
    req=Request(url,headers={"User-Agent":"Structural-GIFT-community-topology/0.1"})
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
    R=6371.0088
    a1,a2=map(math.radians,(lat1,lat2)); da=a2-a1; dl=math.radians(lon2-lon1)
    x=math.sin(da/2)**2+math.cos(a1)*math.cos(a2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1.0,math.sqrt(x)))

def components(ids,distances,radius):
    parent={x:x for x in ids}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a==b:return
        if int(a)>int(b):a,b=b,a
        parent[b]=a
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            if distances[(a,b)]<=radius: union(a,b)
    out=defaultdict(set)
    for x in ids:out[find(x)].add(x)
    by={}
    for members in out.values():
        frozen=frozenset(members)
        for x in members:by[x]=frozen
    return by

def mean(xs):
    return sum(xs)/len(xs) if xs else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--prior-exclusions",type=Path,required=True)
    args=ap.parse_args()

    prior=json.loads(args.prior_exclusions.read_text())
    if prior.get("status")!="FROZEN_BEFORE_COMMUNITY_RESPONSE": raise RuntimeError("prior exclusions not frozen")
    if prior.get("response_values_used") is not False: raise RuntimeError("prior response values entered exclusion rule")
    prior_paths={tuple(x) for x in prior["excluded_archipelago_paths"]}

    lists,lm=fetch("lists"); taxonomy,tm=fetch("taxonomy"); references,rm=fetch("references")
    checklist_refs=set()
    for rr in references:
        try: checklist=int(float(rr.get("checklist")))
        except (TypeError,ValueError): checklist=None
        try: restricted=int(float(rr.get("restricted")))
        except (TypeError,ValueError): restricted=0
        if checklist==1 and restricted!=1: checklist_refs.add(s(rr.get("ref_ID")))

    target_ids={}
    island_sets={}
    lists_by_target={}
    target_meta={}
    for target in TARGETS:
        wide,t=eligible(lists,taxonomy,target,NATIVE_SCOPE_WIDE,checklist_refs)
        comp,_=eligible(lists,taxonomy,target,NATIVE_SCOPE_COMPLETE,checklist_refs)
        compids={s(r["entity_ID"]) for r in comp}
        sel=[r for r in wide if s(r["entity_ID"]) in compids and s(r.get("entity_class"))=="Island"]
        island_sets[target]={s(r["entity_ID"]) for r in sel}
        target_ids[target]=s(t["taxon_ID"])
        by=defaultdict(set)
        for r in sel:by[s(r["entity_ID"])].add(s(r["list_ID"]))
        lists_by_target[target]=by
        target_meta[target]={
            "taxon_ID":target_ids[target],
            "eligible_individual_islands":len(island_sets[target]),
            "eligible_list_count":len({lid for ids in by.values() for lid in ids}),
        }

    common=set.intersection(*(island_sets[t] for t in TARGETS))

    misc={}; mm={}
    for var in MISC:
        rows,m=fetch("geoentities_env_misc",envvar=var)
        misc[var]={s(r["entity_ID"]):r.get(var) for r in rows}; mm[var]=m
    climate={}; cm={}
    for layer in CLIMATE:
        rows,m=fetch("geoentities_env_raster",layername=layer,sumstat="mean")
        climate[layer]={s(r["entity_ID"]):r.get("mean") for r in rows}; cm[layer]=m

    predictor_complete={
        eid for eid in common
        if all(misc[v].get(eid) not in (None,"") for v in ("area","dist","SLMP","GMMC","longitude","latitude"))
        and all(climate[l].get(eid) not in (None,"") for l in CLIMATE)
        and any(misc[v].get(eid) not in (None,"") for v in ("arch_lvl_1","arch_lvl_2","arch_lvl_3"))
    }
    paths={}
    for eid in predictor_complete:
        path=tuple(s(misc[v].get(eid)).strip() for v in ("arch_lvl_1","arch_lvl_2","arch_lvl_3") if misc[v].get(eid) not in (None,""))
        if path:paths[eid]=path

    union,ais=ais_union()
    exact_overlap={
        eid for eid in predictor_complete
        if union.covers(Point(float(misc["longitude"][eid]),float(misc["latitude"][eid])))
    }
    ais_contaminated={paths[eid] for eid in exact_overlap if eid in paths}
    excluded_paths=prior_paths|ais_contaminated
    clean={
        eid for eid in predictor_complete
        if paths.get(eid) not in excluded_paths
    }

    groups=defaultdict(list)
    for eid in clean:
        if eid in paths:groups[paths[eid]].append(eid)
    groups={p:sorted(ids,key=int) for p,ids in groups.items() if len(ids)>=MIN_ARCHIPELAGO_ISLANDS}
    final_ids=sorted({eid for ids in groups.values() for eid in ids},key=int)

    # Freeze the global extreme-isolation state from predictor-only metadata.
    q75_n=max(1,math.ceil(0.25*len(final_ids)))
    q75_order=sorted(final_ids,key=lambda eid:(-float(misc["dist"][eid]),int(eid)))
    q75=set(q75_order[:q75_n])

    group_rows=[]
    topology_values=[]
    extreme_topology_values=[]
    nonextreme_topology_values=[]
    for path,ids in sorted(groups.items()):
        pair={}
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                pair[(a,b)]=pair[(b,a)]=hav(
                    float(misc["longitude"][a]),float(misc["latitude"][a]),
                    float(misc["longitude"][b]),float(misc["latitude"][b])
                )
        comp_by_radius={r:components(ids,pair,r) for r in RADII}
        islands=[]
        for eid in ids:
            ds=[pair[(eid,j)] for j in ids if j!=eid]
            nearest=min(ds) if ds else None
            island_pressure=mean([
                math.log1p(sum(math.exp(-pair[(eid,j)]/r) for j in ids if j!=eid))
                for r in RADII
            ])
            landmass_pressure=mean([
                math.log1p(sum(float(misc["area"][j])*math.exp(-pair[(eid,j)]/r) for j in ids if j!=eid))
                for r in RADII
            ])
            reach=[]; direct=[]; gain=[]
            for r in RADII:
                comp=comp_by_radius[r][eid]
                rr=any(float(misc["dist"][j])<=r for j in comp)
                dd=float(misc["dist"][eid])<=r
                reach.append(int(rr)); direct.append(int(dd)); gain.append(int(rr)-int(dd))
            topo=sum(gain)/len(gain)
            topology_values.append(topo)
            (extreme_topology_values if eid in q75 else nonextreme_topology_values).append(topo)
            islands.append({
                "entity_ID":eid,
                "longitude":float(misc["longitude"][eid]),
                "latitude":float(misc["latitude"][eid]),
                "area_km2":float(misc["area"][eid]),
                "dist_km":float(misc["dist"][eid]),
                "SLMP":float(misc["SLMP"][eid]),
                "GMMC":int(float(misc["GMMC"][eid])),
                "extreme_q75":eid in q75,
                "nearest_other_island_km":nearest,
                "surrounding_island_pressure":island_pressure,
                "surrounding_landmass_pressure":landmass_pressure,
                "direct_mainland_frequency":sum(direct)/len(direct),
                "mainland_stepping_frequency":sum(reach)/len(reach),
                "topology_gain":topo,
                "climate":{layer:float(climate[layer][eid]) for layer in CLIMATE},
                "list_ids":{target:sorted(lists_by_target[target][eid],key=int) for target in TARGETS},
            })
        group_rows.append({
            "archipelago_id":" / ".join(path),
            "archipelago_path":list(path),
            "n_islands":len(ids),
            "extreme_islands":sum(eid in q75 for eid in ids),
            "nonextreme_islands":sum(eid not in q75 for eid in ids),
            "gmmc_connected_fraction":mean([int(float(misc["GMMC"][eid])) for eid in ids]),
            "topology_gain_nonzero_islands":sum(
                island["topology_gain"]>0 for island in islands
            ),
            "membership_sha256":sha(ids),
            "islands":islands,
        })

    response_surfaces={}
    for target in TARGETS:
        rows=sorted(
            (g["archipelago_id"],i["entity_ID"],lid,target_ids[target])
            for g in group_rows for i in g["islands"] for lid in i["list_ids"][target]
        )
        response_surfaces[target]={
            "taxon_ID":target_ids[target],
            "query_semantics":"GIFT checklists endpoint by frozen list_ID + taxon_ID + filter=native + namesmatched=0",
            "row_count":len(rows),
            "surface_sha256":sha(rows),
            "opened":False,
        }

    support={
        "archipelagos":len(group_rows),
        "islands":len(final_ids),
        "extreme_islands":len(q75),
        "nonextreme_islands":len(final_ids)-len(q75),
        "archipelagos_with_extreme":sum(g["extreme_islands"]>0 for g in group_rows),
        "archipelagos_with_nonextreme":sum(g["nonextreme_islands"]>0 for g in group_rows),
        "archipelagos_with_both":sum(g["extreme_islands"]>0 and g["nonextreme_islands"]>0 for g in group_rows),
        "topology_gain_nonzero_islands":sum(v>0 for v in topology_values),
        "extreme_topology_gain_nonzero_islands":sum(v>0 for v in extreme_topology_values),
        "nonextreme_topology_gain_nonzero_islands":sum(v>0 for v in nonextreme_topology_values),
        "topology_gain_values":sorted(set(topology_values)),
    }

    payload={
        "schema":"structural.gift_community_topology_panel.v0_1",
        "status":"FROZEN_PREDICTOR_PANEL_RESPONSE_SEALED",
        "gift_version":VERSION,
        "targets":list(TARGETS),
        "species_composition_endpoint_called":False,
        "response_values_accessed":False,
        "quality_filters":{
            "complete_taxon":True,"complete_floristic":True,"native_indicated":True,
            "suit_geo":True,"public_only":True,"reference_checklist_flag_required":True,
            "minimum_archipelago_islands":MIN_ARCHIPELAGO_ISLANDS,
        },
        "checklist_quality_boundary":"scope/completeness metadata are quality filters, not proof of perfect biological detection",
        "target_metadata":target_meta,
        "common_islands_before_predictor_filter":len(common),
        "predictor_complete_common_islands":len(predictor_complete),
        "prior_response_exclusion_receipt_sha256":sha(prior),
        "prior_response_excluded_archipelago_paths":[list(x) for x in sorted(prior_paths)],
        "closed_A_Islands_exclusion":{
            "exact_overlap_islands":len(exact_overlap),
            "contaminated_archipelago_paths":[list(x) for x in sorted(ais_contaminated)],
            "geometry":ais,
        },
        "radii_km":list(RADII),
        "topology_gain_definition":"mean across 25/50/125/250 km of [component contains an island with mainland distance <= radius] - [focal island mainland distance <= radius]; range 0..1",
        "reference_predictors":[
            *CLIMATE,"log_area_km2","log1p_mainland_dist_km","SLMP","GMMC",
            "nearest_other_island_km","surrounding_island_pressure","surrounding_landmass_pressure"
        ],
        "primary_structural_predictor":"topology_gain",
        "extreme_rule":"global upper 25% of final common-panel islands by GIFT dist; entity_ID tie-break",
        "support":support,
        "n_final_archipelagos":len(group_rows),
        "n_final_islands":len(final_ids),
        "groups":group_rows,
        "response_surfaces":response_surfaces,
        "source_sha256":{
            "lists":lm["sha256"],"taxonomy":tm["sha256"],"references":rm["sha256"],
            "misc":{k:v["sha256"] for k,v in mm.items()},
            "climate":{k:v["sha256"] for k,v in cm.items()},
        },
    }
    payload["panel_fingerprint"]=sha({
        "gift_version":VERSION,"quality_filters":payload["quality_filters"],
        "prior_response_exclusions":payload["prior_response_excluded_archipelago_paths"],
        "closed_A_Islands_exclusion":payload["closed_A_Islands_exclusion"],
        "radii_km":payload["radii_km"],"topology_gain_definition":payload["topology_gain_definition"],
        "extreme_rule":payload["extreme_rule"],
        "groups":[(g["archipelago_id"],g["membership_sha256"]) for g in group_rows],
        "response_surfaces":response_surfaces,
        "source_sha256":payload["source_sha256"],
    })
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
