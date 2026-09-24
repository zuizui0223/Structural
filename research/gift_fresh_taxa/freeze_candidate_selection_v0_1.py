#!/usr/bin/env python3
"""Freeze response-blind selection of fresh GIFT taxonomic panels.

This is a new macro-study family, not Structural v0.10 independent-system intake.
All candidate screening is metadata-only and every candidate passing the frozen
metadata rule is retained.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

CANDIDATES=("Pteridophyta","Gymnospermae","Bryophyta")
MIN_PRELIM_ARCHIPELAGOS_GE20=8
MIN_GLOBAL_WORK_IDS=1000
MIN_FINAL_ARCHIPELAGOS=8
REQUIRED_SUPPORT_CLASSES=("extreme_only","paired","nonextreme_only")

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path):
    x=json.loads(Path(path).read_text())
    if not isinstance(x,dict): raise RuntimeError(f"{path} must be object")
    return x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--census",required=True)
    ap.add_argument("--pteridophyta-universe",required=True)
    ap.add_argument("--gymnospermae-universe",required=True)
    a=ap.parse_args()

    census=load(a.census)
    if census.get("species_composition_endpoint_called") is not False:
        raise RuntimeError("candidate census opened species composition")
    if census.get("angiosperm_response_reused") is not False:
        raise RuntimeError("candidate census reused consumed Angiosperm response")
    if tuple(census.get("candidate_targets",()))!=CANDIDATES:
        raise RuntimeError("candidate target set drift")

    universes={
        "Pteridophyta":load(a.pteridophyta_universe),
        "Gymnospermae":load(a.gymnospermae_universe),
    }

    stage1={}
    for taxon in CANDIDATES:
        r=census["results"][taxon]
        ge20=int(r["archipelagos_by_minimum_island_count"]["20"])
        work=int(r["global_taxonomic_work_ids"])
        stage1[taxon]={
            "archipelagos_ge20":ge20,
            "global_taxonomic_work_ids":work,
            "pass": ge20>=MIN_PRELIM_ARCHIPELAGOS_GE20 and work>=MIN_GLOBAL_WORK_IDS,
        }

    prelim=[t for t in CANDIDATES if stage1[t]["pass"]]
    if set(prelim)!=set(universes):
        raise RuntimeError(f"unexpected preliminary pass set: {prelim}")

    final={}
    for taxon,u in universes.items():
        if u.get("response_values_accessed") is not False or u.get("species_composition_endpoint_called") is not False:
            raise RuntimeError(f"{taxon} universe opened response")
        support=u["support_class_counts"]
        pass_final=(
            int(u["n_final_archipelagos"])>=MIN_FINAL_ARCHIPELAGOS
            and all(int(support.get(k,0))>=1 for k in REQUIRED_SUPPORT_CLASSES)
        )
        final[taxon]={
            "universe_fingerprint":u["universe_fingerprint"],
            "n_final_archipelagos":u["n_final_archipelagos"],
            "n_final_islands":u["n_final_islands"],
            "support_class_counts":support,
            "pass":pass_final,
        }

    selected=[t for t in prelim if final[t]["pass"]]
    payload={
        "schema":"structural.gift_fresh_taxa_selection.v0_1",
        "status":"FROZEN_RESPONSE_BLIND_CANDIDATE_SELECTION",
        "gift_version":"3.2",
        "candidate_set":list(CANDIDATES),
        "candidate_set_rule":"predeclared broad non-angiosperm land-plant groups available in GIFT; no response values used",
        "selection_rule":{
            "stage1":"retain every candidate with >=8 metadata-census archipelagos containing >=20 eligible islands and >=1000 global taxonomic work_IDs",
            "stage2":"retain every stage1 candidate whose predictor-complete, A-Islands-clean universe has >=8 archipelagos and at least one extreme_only, paired, and nonextreme_only q75 support class",
            "no_result_based_choice":True,
            "all_passing_candidates_retained":True,
        },
        "angiosperm_pilot_response_used_for_selection":False,
        "species_composition_endpoint_called":False,
        "stage1":stage1,
        "stage2":final,
        "selected_taxa":selected,
        "excluded_taxa":[t for t in CANDIDATES if t not in selected],
        "cross_taxon_comparison_authorized_only_if_each_taxon_passes_its_own_burned_pilot":True,
    }
    payload["selection_fingerprint"]=sha(payload)
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
