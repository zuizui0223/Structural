#!/usr/bin/env python3
"""Response-blind census of fresh non-Angiosperm GIFT taxonomic surfaces.

No checklist/species endpoint is called. The purpose is only to determine
whether an untouched taxonomic response surface has enough island/archipelago
coverage to justify a new prospective protocol after the Angiosperm v0.1 pilot
terminated.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib, json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE="https://gift.uni-goettingen.de/api/extended/"
VERSION="3.2"
TARGETS=("Pteridophyta","Gymnospermae","Bryophyta")
ENTITY_CLASSES={"Island","Island Group","Island Part"}

NATIVE_SCOPE_WIDE={
    "all","native","native and naturalized",
    "native and historically introduced","endangered","endemic","other subset",
}
NATIVE_SCOPE_COMPLETE={
    "all","native","native and naturalized","native and historically introduced",
}

def fetch(query, **extra):
    params={"query":query, **{k:str(v) for k,v in extra.items()}}
    url=BASE+f"index{VERSION}.php?"+urlencode(params)
    req=Request(url,headers={"User-Agent":"Structural-GIFT-fresh-taxa-metadata/0.1"})
    with urlopen(req,timeout=180) as r:
        raw=r.read()
    rows=json.loads(raw)
    if not isinstance(rows,list):
        raise RuntimeError(f"{query}: expected list")
    return rows,{"url":url,"rows":len(rows),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def s(x): return "" if x is None else str(x)

def eligible_rows(lists,taxonomy,target_name,scope):
    target=next((r for r in taxonomy if s(r.get("taxon_name"))==target_name),None)
    if target is None:
        return [],None
    left,right=float(target["lft"]),float(target["rgt"])
    target_span=right-left
    tax_by={s(r["taxon_ID"]):r for r in taxonomy}
    allowed=set()
    for row in taxonomy:
        lft,rgt=float(row["lft"]),float(row["rgt"])
        if (lft>=left and rgt<=right) or (lft<left and rgt>right):
            allowed.add(s(row["taxon_ID"]))
    rows=[]
    for row in lists:
        if s(row.get("taxon_ID")) not in allowed: continue
        if s(row.get("subset")) not in scope: continue
        if s(row.get("entity_class")) not in ENTITY_CLASSES: continue
        if s(row.get("native_indicated"))!="1": continue
        if s(row.get("suit_geo"))!="1": continue
        if s(row.get("restricted"))=="1": continue
        tax=tax_by.get(s(row.get("taxon_ID")))
        if tax is None: continue
        rr=dict(row)
        rr["_span"]=float(tax["rgt"])-float(tax["lft"])
        rows.append(rr)
    max_span=defaultdict(float)
    for row in rows:
        max_span[s(row["entity_ID"])]=max(max_span[s(row["entity_ID"])],row["_span"])
    complete_entities={eid for eid,span in max_span.items() if span>=target_span}
    return [r for r in rows if s(r["entity_ID"]) in complete_entities],target

def main():
    lists,lists_meta=fetch("lists")
    taxonomy,tax_meta=fetch("taxonomy")
    species_rows=[]
    species_meta=[]
    for start in range(0,600000,100000):
        page,meta=fetch("species",startat=start)
        species_rows.extend(page)
        species_meta.append(meta)
        if len(page)<100000:
            break
    arch={}
    arch_meta={}
    for var in ("arch_lvl_1","arch_lvl_2","arch_lvl_3","dist","GMMC"):
        rows,meta=fetch("geoentities_env_misc",envvar=var)
        arch[var]={s(r["entity_ID"]):r.get(var) for r in rows}
        arch_meta[var]=meta

    results={}
    for target in TARGETS:
        wide,t=eligible_rows(lists,taxonomy,target,NATIVE_SCOPE_WIDE)
        complete,_=eligible_rows(lists,taxonomy,target,NATIVE_SCOPE_COMPLETE)
        if t is None:
            results[target]={"available":False}
            continue
        complete_ids={s(r["entity_ID"]) for r in complete}
        selected=[r for r in wide if s(r["entity_ID"]) in complete_ids]
        island_ids=sorted({
            s(r["entity_ID"]) for r in selected if s(r.get("entity_class"))=="Island"
        },key=int)

        groups=defaultdict(set)
        for eid in island_ids:
            path=tuple(
                s(arch[var].get(eid)).strip()
                for var in ("arch_lvl_1","arch_lvl_2","arch_lvl_3")
                if arch[var].get(eid) not in (None,"")
            )
            if path: groups[path].add(eid)

        g_rows=[]
        for path,ids in groups.items():
            d_non=sum(arch["dist"].get(eid) not in (None,"") for eid in ids)
            g_non=sum(arch["GMMC"].get(eid) not in (None,"") for eid in ids)
            g_rows.append({
                "archipelago_path":list(path),
                "n_islands":len(ids),
                "dist_complete":d_non==len(ids),
                "gmmc_complete":g_non==len(ids),
            })
        g_rows.sort(key=lambda x:(-x["n_islands"],x["archipelago_path"]))
        left,right=float(t["lft"]),float(t["rgt"])
        genus_ids={
            s(row["taxon_ID"]) for row in taxonomy
            if s(row.get("taxon_lvl"))=="genus"
            and float(row["lft"])>=left and float(row["rgt"])<=right
        }
        global_work_ids={
            int(row["work_ID"]) for row in species_rows
            if s(row.get("genus_ID")) in genus_ids
        }
        results[target]={
            "available":True,
            "taxon_ID":s(t["taxon_ID"]),
            "global_taxonomic_work_ids":len(global_work_ids),
            "eligible_individual_islands":len(island_ids),
            "archipelagos_with_any_island":len(g_rows),
            "archipelagos_by_minimum_island_count":{
                str(k):sum(r["n_islands"]>=k for r in g_rows) for k in (8,12,16,20,30)
            },
            "archipelagos_ge16_complete_dist":sum(r["n_islands"]>=16 and r["dist_complete"] for r in g_rows),
            "archipelagos_ge16_complete_gmmc":sum(r["n_islands"]>=16 and r["gmmc_complete"] for r in g_rows),
            "top_archipelagos":g_rows[:40],
        }

    payload={
        "schema":"structural.gift_fresh_taxa_metadata_census.v0_1",
        "status":"RESPONSE_BLIND_CANDIDATE_CENSUS_ONLY",
        "gift_version":VERSION,
        "angiosperm_response_reused":False,
        "species_composition_endpoint_called":False,
        "candidate_targets":list(TARGETS),
        "source_tables":{
            "lists":lists_meta,
            "taxonomy":tax_meta,
            "species_metadata_pages":species_meta,
            "environment":arch_meta,
        },
        "results":results,
    }
    unsigned=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    payload["census_fingerprint"]=hashlib.sha256(unsigned).hexdigest()
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
