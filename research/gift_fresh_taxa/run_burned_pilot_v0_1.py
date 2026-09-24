#!/usr/bin/env python3
"""Spend one frozen fresh-taxon GIFT burned pilot; fit zero models."""
from __future__ import annotations

from collections import defaultdict
import argparse, csv, hashlib, json, math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE="https://gift.uni-goettingen.de/api/extended/"
VERSION="3.2"

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path):
    x=json.loads(Path(path).read_text())
    if not isinstance(x,dict): raise RuntimeError(f"{path} must contain object")
    return x

def fetch(query,**extra):
    url=BASE+f"index{VERSION}.php?"+urlencode({"query":query,**{k:str(v) for k,v in extra.items()}})
    req=Request(url,headers={"User-Agent":"Structural-GIFT-fresh-taxon-burned-pilot/0.1"})
    with urlopen(req,timeout=180) as r: raw=r.read()
    rows=json.loads(raw)
    if not isinstance(rows,list): raise RuntimeError(f"{query}: expected list")
    return rows,{"url":url,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def fetch_checklist(list_id,taxon_id):
    return fetch(
        "checklists",
        listid=str(list_id),
        taxonid=str(taxon_id),
        namesmatched="0",
        filter="native",
    )

def s(x): return "" if x is None else str(x)

def as01(x):
    try:return int(float(x))
    except (TypeError,ValueError):return None

def explicit_true(x): return as01(x)==1

def hav(lon1,lat1,lon2,lat2):
    R=6371.0088
    a1,a2=map(math.radians,(lat1,lat2))
    da=a2-a1; dl=math.radians(lon2-lon1)
    z=math.sin(da/2)**2+math.cos(a1)*math.cos(a2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1,math.sqrt(z)))

def balanced_blocks(ids,lon,lat,k=4):
    ids=sorted(ids,key=int)
    pairs=[]
    for idx,a in enumerate(ids):
        for b in ids[idx+1:]:
            pairs.append((hav(float(lon[a]),float(lat[a]),float(lon[b]),float(lat[b])),-int(a),-int(b),a,b))
    _,_,_,a,b=max(pairs)
    scored=[]
    for eid in ids:
        da=hav(float(lon[eid]),float(lat[eid]),float(lon[a]),float(lat[a]))
        db=hav(float(lon[eid]),float(lat[eid]),float(lon[b]),float(lat[b]))
        scored.append((da-db,int(eid),eid))
    ordered=[row[2] for row in sorted(scored)]
    base,rem=divmod(len(ordered),k)
    sizes=[base+(1 if j<rem else 0) for j in range(k)]
    out={};cur=0
    for j,size in enumerate(sizes,1):
        for eid in ordered[cur:cur+size]: out[eid]=f"B{j}"
        cur+=size
    return out,sizes

def global_tail(ids,dist,fraction):
    ordered=sorted(ids,key=lambda eid:(-float(dist[eid]),int(eid)))
    n=max(1,math.ceil(len(ordered)*fraction))
    return set(ordered[:n])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--universe",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--lock",type=Path,required=True)
    ap.add_argument("--raw-output",type=Path)
    a=ap.parse_args()

    u=load(a.universe); p=load(a.protocol); lock=load(a.lock)
    taxon=p["taxon_name"]
    if p.get("status")!="FROZEN_BEFORE_PILOT_RESPONSE": raise RuntimeError("protocol not frozen")
    if p.get("response_values_accessed") is not False: raise RuntimeError("protocol already opened response")
    if p["protocol_fingerprint"]!=lock["systems"][taxon]["protocol_fingerprint"]: raise RuntimeError("protocol fingerprint drift")
    if u["universe_fingerprint"]!=lock["systems"][taxon]["universe_fingerprint"]: raise RuntimeError("universe fingerprint drift")
    if p["candidate_selection_fingerprint"]!=lock["candidate_selection_fingerprint"]: raise RuntimeError("candidate selection drift")

    pilot_ids=set(p["pilot_selection"]["pilot_archipelagos"])
    confirm_ids=set(p["pilot_selection"]["confirmatory_archipelagos"])
    if pilot_ids & confirm_ids: raise RuntimeError("pilot/confirmatory archipelagos overlap")
    groups={g["archipelago_id"]:g for g in u["groups"]}
    if not pilot_ids <= set(groups): raise RuntimeError("pilot archipelago missing from universe")

    pilot_lists=sorted({str(lid) for gid in pilot_ids for lid in groups[gid]["list_ids"]},key=int)
    confirm_lists=sorted({str(lid) for gid in confirm_ids for lid in groups[gid]["list_ids"]},key=int)
    if set(pilot_lists)&set(confirm_lists): raise RuntimeError("pilot/confirmatory list surfaces overlap")
    if sha(pilot_lists)!=p["pilot_selection"]["pilot_list_set_sha256"]: raise RuntimeError("pilot list hash drift")
    if sha(confirm_lists)!=p["pilot_selection"]["confirmatory_list_set_sha256"]: raise RuntimeError("confirmatory list hash drift")

    # Response-blind metadata replay needed to map list->island and reconstruct
    # frozen block/q75 labels.
    list_rows,list_meta=fetch("lists")
    list_to_entity={}
    for row in list_rows:
        lid=s(row.get("list_ID"))
        if lid in set(pilot_lists):
            eid=s(row.get("entity_ID"))
            if lid in list_to_entity and list_to_entity[lid]!=eid:
                raise RuntimeError(f"list {lid} maps to multiple entity_IDs")
            list_to_entity[lid]=eid
    if set(list_to_entity)!=set(pilot_lists): raise RuntimeError("not all pilot list IDs map to entities")

    lon_rows,lon_meta=fetch("geoentities_env_misc",envvar="longitude")
    lat_rows,lat_meta=fetch("geoentities_env_misc",envvar="latitude")
    dist_rows,dist_meta=fetch("geoentities_env_misc",envvar="dist")
    lon={s(r["entity_ID"]):r.get("longitude") for r in lon_rows}
    lat={s(r["entity_ID"]):r.get("latitude") for r in lat_rows}
    dist={s(r["entity_ID"]):r.get("dist") for r in dist_rows}

    all_entities=sorted({str(eid) for g in u["groups"] for eid in g["entity_ids"]},key=int)
    q75=global_tail(all_entities,dist,0.25)

    pilot_entity_meta={}
    for gid in sorted(pilot_ids):
        g=groups[gid]
        ids=[str(eid) for eid in g["entity_ids"]]
        blocks,sizes=balanced_blocks(ids,lon,lat,4)
        if sizes!=g["block_sizes"]: raise RuntimeError(f"block-size drift: {gid}")
        if sha(sorted((eid,blocks[eid]) for eid in ids))!=g["block_assignment_sha256"]:
            raise RuntimeError(f"block assignment drift: {gid}")
        e=sum(eid in q75 for eid in ids)
        if e!=g["q75_extreme_n"] or len(ids)-e!=g["q75_nonextreme_n"]:
            raise RuntimeError(f"q75 assignment drift: {gid}")
        for eid in ids:
            pilot_entity_meta[eid]={
                "archipelago_id":gid,
                "block":blocks[eid],
                "extreme_q75":eid in q75,
            }

    # Spend only pilot checklist response surfaces.
    present=defaultdict(set)
    uncertain=defaultdict(set)
    raw_records=[]
    response_receipts=[]
    for lid in pilot_lists:
        eid=list_to_entity[lid]
        if eid not in pilot_entity_meta:
            raise RuntimeError(f"pilot list {lid} maps outside pilot archipelagos")
        rows,meta=fetch_checklist(lid,p["taxon_ID"])
        response_receipts.append({"list_ID":lid,**meta})
        for row in rows:
            wid=row.get("work_ID")
            if wid in (None,""): continue
            wid=str(int(float(wid)))
            native=as01(row.get("native"))
            questionable=as01(row.get("questionable"))
            quest_native=as01(row.get("quest_native"))
            raw_records.append((lid,eid,wid,native,questionable,quest_native))
            if native==1 and not explicit_true(row.get("questionable")) and not explicit_true(row.get("quest_native")):
                present[eid].add(wid)
            elif native==1:
                uncertain[eid].add(wid)

    min_pos=p["burned_pilot"]["minimum_training_presences"]
    min_neg=p["burned_pilot"]["minimum_training_absences"]
    min_test=p["burned_pilot"]["minimum_test_rows"]
    audits=[]
    checked=estimable_pairs=0
    for gid in sorted(pilot_ids):
        g=groups[gid]
        ids=sorted((str(eid) for eid in g["entity_ids"]),key=int)
        species=sorted({wid for eid in ids for wid in present[eid]},key=int)
        estimable=0
        hist=defaultdict(int)
        for wid in species:
            checked+=1
            fold_pass=0
            for block in ("B1","B2","B3","B4"):
                test=[eid for eid in ids if pilot_entity_meta[eid]["block"]==block]
                train=[eid for eid in ids if pilot_entity_meta[eid]["block"]!=block]
                def target(eid):
                    if wid in present[eid]: return 1
                    if wid in uncertain[eid]: return None
                    return 0
                tr=[target(eid) for eid in train]
                te=[target(eid) for eid in test]
                tr=[v for v in tr if v in (0,1)]
                te=[v for v in te if v in (0,1)]
                if len(te)>=min_test and sum(v==1 for v in tr)>=min_pos and sum(v==0 for v in tr)>=min_neg:
                    fold_pass+=1
            hist[str(fold_pass)]+=1
            if fold_pass>=3:
                estimable+=1
                estimable_pairs+=1
        arch_pass=estimable>=30
        audits.append({
            "archipelago_id":gid,
            "support_class":g["support_class"],
            "n_islands":len(ids),
            "q75_extreme_islands":g["q75_extreme_n"],
            "q75_nonextreme_islands":g["q75_nonextreme_n"],
            "species_with_presence":len(species),
            "estimable_species":estimable,
            "fold_pass_count_histogram":dict(sorted(hist.items())),
            "archipelago_pass":arch_pass,
        })

    passing=[x for x in audits if x["archipelago_pass"]]
    has_extreme=any(x["support_class"] in {"extreme_only","paired"} for x in passing)
    has_nonextreme=any(x["support_class"] in {"nonextreme_only","paired"} for x in passing)
    passed=len(passing)>=2 and has_extreme and has_nonextreme

    canonical_raw=sorted(raw_records,key=lambda r:(int(r[0]),int(r[2]),int(r[1])))
    if a.raw_output:
        a.raw_output.parent.mkdir(parents=True,exist_ok=True)
        with a.raw_output.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h)
            w.writerow(["list_ID","entity_ID","work_ID","native","questionable","quest_native"])
            w.writerows(canonical_raw)

    out={
        "schema":"structural.gift_fresh_taxon_burned_pilot.v0_1",
        "status":"PILOT_PASS_ESTIMABILITY_ONLY" if passed else "PILOT_STOP_NON_ESTIMABLE",
        "gift_version":VERSION,
        "taxon_name":taxon,
        "taxon_ID":p["taxon_ID"],
        "pre_response_green_commit":lock["pre_response_green_commit"],
        "candidate_selection_fingerprint":lock["candidate_selection_fingerprint"],
        "universe_fingerprint":u["universe_fingerprint"],
        "protocol_fingerprint":p["protocol_fingerprint"],
        "pilot_response_opened":True,
        "confirmatory_response_opened":False,
        "confirmatory_list_query_count":0,
        "pilot_list_count":len(pilot_lists),
        "pilot_list_set_sha256":sha(pilot_lists),
        "confirmatory_list_set_sha256":sha(confirm_lists),
        "metadata_replay_sha256":sha({
            "lists":list_meta["sha256"],
            "longitude":lon_meta["sha256"],
            "latitude":lat_meta["sha256"],
            "dist":dist_meta["sha256"],
        }),
        "response_source_receipt_sha256":sha(response_receipts),
        "raw_response_row_count":len(canonical_raw),
        "raw_response_sha256":sha(canonical_raw),
        "species_names_reported":False,
        "model_fits":0,
        "effect_size":None,
        "prediction_score":None,
        "predictive_denominator_contribution":0,
        "species_archipelago_pairs_checked":checked,
        "species_archipelago_pairs_estimable":estimable_pairs,
        "archipelago_audits":audits,
        "pass_rule":p["burned_pilot"]["study_pass"],
        "pilot_pass":passed,
        "confirmatory_response_authorized":passed,
        "authorization_ceiling":"exact frozen confirmatory analysis for this taxon only; pilot contributes zero predictive evidence",
    }
    out["pilot_receipt_sha256"]=sha(out)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if passed else 2

if __name__=="__main__":
    raise SystemExit(main())
