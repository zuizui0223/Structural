#!/usr/bin/env python3
"""Open only frozen pilot GIFT lists and audit estimability; fit zero models."""
from __future__ import annotations

from collections import defaultdict
import argparse
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE="https://gift.uni-goettingen.de/api/extended/"
VERSION="3.2"

def sha(value)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):
        raise RuntimeError(f"{path} must contain an object")
    return x

def fetch_checklist(list_id:str,taxon_id:str):
    url=BASE+"index3.2.php?"+urlencode({
        "query":"checklists",
        "listid":str(list_id),
        "taxonid":str(taxon_id),
        "namesmatched":"0",
        "filter":"native",
    })
    req=Request(url,headers={"User-Agent":"Structural-GIFT-burned-pilot/0.1"})
    with urlopen(req,timeout=180) as response:
        raw=response.read()
    rows=json.loads(raw)
    if not isinstance(rows,list):
        raise RuntimeError(f"list {list_id}: expected JSON list")
    return rows,{"url":url,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def as01(value):
    try:
        return int(float(value))
    except (TypeError,ValueError):
        return None

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--universe",type=Path,required=True)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--raw-output",type=Path)
    a=p.parse_args()

    u=load(a.universe)
    protocol=load(a.protocol)
    if protocol.get("status")!="FROZEN_BEFORE_PILOT_RESPONSE":
        raise RuntimeError("study protocol is not frozen")
    if protocol.get("response_values_accessed") is not False:
        raise RuntimeError("protocol already records response access")
    if u.get("response_values_accessed") is not False:
        raise RuntimeError("universe is not response sealed")

    pilot_ids=set(protocol["evidence_partition"]["pilot_archipelagos"])
    confirm_ids=set(protocol["evidence_partition"]["confirmatory_archipelagos"])
    if pilot_ids & confirm_ids:
        raise RuntimeError("pilot/confirmatory archipelagos overlap")

    pilot_groups=[g for g in u["groups"] if g["archipelago_id"] in pilot_ids]
    confirm_groups=[g for g in u["groups"] if g["archipelago_id"] in confirm_ids]
    if len(pilot_groups)!=len(pilot_ids):
        raise RuntimeError("pilot archipelago set does not replay")

    pilot_lists={}
    confirm_lists=set()
    island_meta={}
    for g in pilot_groups:
        for island in g["islands"]:
            eid=str(island["entity_ID"])
            island_meta[eid]={
                "archipelago_id":g["archipelago_id"],
                "spatial_block":island["spatial_block"],
                "extreme_q75":bool(island["extreme_q75"]),
            }
            for lid in island["list_IDs"]:
                lid=str(lid)
                if lid in pilot_lists and pilot_lists[lid]!=eid:
                    raise RuntimeError(f"pilot list {lid} maps to multiple islands")
                pilot_lists[lid]=eid
    for g in confirm_groups:
        for island in g["islands"]:
            for lid in island["list_IDs"]:
                confirm_lists.add(str(lid))
    if set(pilot_lists)&confirm_lists:
        raise RuntimeError("pilot list set overlaps confirmatory list set")

    taxonomy_url=BASE+"index3.2.php?"+urlencode({"query":"taxonomy"})
    req=Request(taxonomy_url,headers={"User-Agent":"Structural-GIFT-burned-pilot/0.1"})
    with urlopen(req,timeout=180) as response:
        taxonomy_raw=response.read()
    taxonomy=json.loads(taxonomy_raw)
    target=next(row for row in taxonomy if str(row.get("taxon_name"))=="Angiospermae")
    taxon_id=str(target["taxon_ID"])

    present=defaultdict(set)
    uncertain=defaultdict(set)
    raw_records=[]
    source_receipts=[]
    for lid in sorted(pilot_lists,key=int):
        eid=pilot_lists[lid]
        rows,meta=fetch_checklist(lid,taxon_id)
        source_receipts.append({"list_ID":lid,**meta})
        for row in rows:
            wid=row.get("work_ID")
            if wid in (None,""):
                continue
            wid=str(int(float(wid)))
            native=as01(row.get("native"))
            questionable=as01(row.get("questionable"))
            quest_native=as01(row.get("quest_native"))
            raw_records.append((
                lid,eid,wid,native,questionable,quest_native
            ))
            if native==1 and questionable==0 and quest_native==0:
                present[eid].add(wid)
            elif native==1:
                uncertain[eid].add(wid)

    species=sorted(
        {wid for eid in island_meta for wid in present[eid]},
        key=int,
    )
    group_islands=defaultdict(list)
    for eid,meta in island_meta.items():
        group_islands[meta["archipelago_id"]].append(eid)
    for ids in group_islands.values():
        ids.sort(key=int)

    min_pos=protocol["comparison_model"]["minimum_training_presences"]
    min_neg=protocol["comparison_model"]["minimum_training_absences"]
    min_test=protocol["comparison_model"]["minimum_test_rows"]

    group_audits=[]
    total_species_arch=0
    total_estimable_species_arch=0
    for g in pilot_groups:
        gid=g["archipelago_id"]
        ids=group_islands[gid]
        estimable=0
        evaluated=0
        fold_count_hist=defaultdict(int)
        for wid in species:
            if not any(wid in present[eid] for eid in ids):
                continue
            evaluated+=1
            fold_pass=0
            for block in ("B1","B2","B3","B4"):
                test=[eid for eid in ids if island_meta[eid]["spatial_block"]==block]
                train=[eid for eid in ids if island_meta[eid]["spatial_block"]!=block]
                def target(eid):
                    if wid in present[eid]:
                        return 1
                    if wid in uncertain[eid]:
                        return None
                    return 0
                tr=[target(eid) for eid in train]
                te=[target(eid) for eid in test]
                tr=[v for v in tr if v in (0,1)]
                te=[v for v in te if v in (0,1)]
                pos=sum(v==1 for v in tr)
                neg=sum(v==0 for v in tr)
                if len(te)>=min_test and pos>=min_pos and neg>=min_neg:
                    fold_pass+=1
            fold_count_hist[str(fold_pass)]+=1
            if fold_pass>=3:
                estimable+=1
        total_species_arch+=evaluated
        total_estimable_species_arch+=estimable
        group_audits.append({
            "archipelago_id":gid,
            "n_islands":len(ids),
            "q75_extreme_islands":sum(island_meta[eid]["extreme_q75"] for eid in ids),
            "q75_nonextreme_islands":sum(not island_meta[eid]["extreme_q75"] for eid in ids),
            "extreme_contributor":bool(g["h1_extreme_contributor"]),
            "nonextreme_contributor":bool(g["h1_nonextreme_contributor"]),
            "paired_contributor":bool(g["h1_paired_contributor"]),
            "species_with_presence":evaluated,
            "estimable_species":estimable,
            "fold_pass_count_histogram":dict(sorted(fold_count_hist.items())),
            "archipelago_pass":estimable>=50,
        })

    passing=[g for g in group_audits if g["archipelago_pass"]]
    has_extreme=any(g["extreme_contributor"] for g in passing)
    has_nonextreme=any(g["nonextreme_contributor"] for g in passing)
    passed=len(passing)>=3 and has_extreme and has_nonextreme

    canonical_raw=sorted(raw_records,key=lambda x:(int(x[0]),int(x[2]),int(x[1])))
    if a.raw_output:
        a.raw_output.parent.mkdir(parents=True,exist_ok=True)
        with a.raw_output.open("w",encoding="utf-8",newline="") as handle:
            w=csv.writer(handle)
            w.writerow(["list_ID","entity_ID","work_ID","native","questionable","quest_native"])
            w.writerows(canonical_raw)

    out={
        "schema":"structural.gift_global_archipelago_burned_pilot.v0_1",
        "status":"PILOT_PASS_ESTIMABILITY_ONLY" if passed else "PILOT_STOP_NON_ESTIMABLE",
        "gift_version":VERSION,
        "protocol_fingerprint":protocol["protocol_fingerprint"],
        "analysis_universe_fingerprint":u["universe_fingerprint"],
        "pilot_response_opened":True,
        "confirmatory_response_opened":False,
        "confirmatory_list_query_count":0,
        "pilot_archipelago_count":len(pilot_groups),
        "pilot_list_count":len(pilot_lists),
        "pilot_list_set_sha256":sha(sorted(pilot_lists,key=int)),
        "raw_pilot_response_row_count":len(canonical_raw),
        "raw_pilot_response_sha256":sha(canonical_raw),
        "source_receipt_sha256":sha(source_receipts),
        "species_names_reported":False,
        "model_fits":0,
        "effect_size":None,
        "prediction_score":None,
        "predictive_denominator_contribution":0,
        "species_archipelago_pairs_checked":total_species_arch,
        "species_archipelago_pairs_estimable":total_estimable_species_arch,
        "archipelago_audits":group_audits,
        "pass_rule":protocol["burned_pilot_gate"]["pass_rule"],
        "pilot_pass":passed,
        "confirmatory_response_authorized":passed,
        "authorization_ceiling":"construct/run exact frozen confirmatory analysis only; pilot itself contributes zero predictive evidence",
    }
    out["pilot_receipt_sha256"]=sha(out)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if passed else 2

if __name__=="__main__":
    raise SystemExit(main())
