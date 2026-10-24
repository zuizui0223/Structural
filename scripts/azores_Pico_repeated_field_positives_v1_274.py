#!/usr/bin/env python3
"""Pico 2020–2024 repeated dated field positives of S1 affected Azorean taxa.

Separate longitudinal evidence in published PRIBES field surveys. No sampled
zero, continuous demographic persistence, source migration or extinction risk
is inferred. Event taxon/island/year results are not emitted.
"""
from __future__ import annotations
import argparse
from collections import defaultdict,Counter
import hashlib
import json
from pathlib import Path

from azores_PRIBES_crossisland_field_v1_271 import read_dated_field,get_original
from azores2016_s1_loss_presence_crosswalk_v1_268 import canonical_binomial,normalized_text
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
from macaronesia_extirpation_source_profile_v1_263 import download_original

S1_SHA="767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1"
YEAR_HIST={"2020":171,"2021":1603,"2022":898,"2024":129}

def repeated_pico_detection(sources,losses):
    target=set()
    for r in losses:
        if (normalized_text(r.get("Archipelago")) not in {"azores","acores"}
            or normalized_text(r.get("Extinction category"))!="extirpation (island level)"
            or normalized_text(r.get("Category"))!="well-supported"):
            continue
        name=canonical_binomial(r.get("Species"))
        if name:target.add(name)
    pico=sources.get("Pico PRIBES",{}).get("field_taxa",[])
    bytax=defaultdict(set)
    native_year=defaultdict(set)
    for row in pico:
        if row.get("island")!="Pico":raise ValueError("Pico source contains unapproved island")
        name=canonical_binomial(row.get("name"))
        if not name or name not in target: continue
        yr=int(row["year"])
        if yr not in (2020,2021,2022,2024):
            raise ValueError("Unexpected Pico source year outside independently validated 2020,2021,2022,2024")
        bytax[name].add(yr)
        if row.get("native"):
            native_year[name].add(yr)
    counts=Counter(map(len,bytax.values()))
    year_count=Counter(y for vals in bytax.values() for y in vals)
    return {
       "historically_loss_affected_Azores_taxa":len(target),
       "historically_loss_affected_taxa_seen_on_Pico":len(bytax),
       "historical_loss_affect_pico_positive_taxon_year_pairs":sum(map(len,bytax.values())),
       "historical_loss_taxa_seen_2024":year_count[2024],
       "Pico_positive_taxa_by_number_of_survey_years":{str(k):v for k,v in sorted(counts.items())},
       "per_Pico_year_historic_loss_taxa_positive":{str(k):v for k,v in sorted(year_count.items())},
       "historic_loss_taxa_seen_in_2plus_Pico_years":sum(len(x)>=2 for x in bytax.values()),
       "historic_loss_taxa_seen_in_3plus_Pico_years":sum(len(x)>=3 for x in bytax.values()),
       "historic_loss_taxa_seen_in_4_Pico_years":sum(len(x)==4 for x in bytax.values()),
       "historical_loss_taxa_with_native_status_2plus_Pico_years":sum(len(x)>=2 for x in native_year.values()),
       "missing_Pico_taxa_record_is_not_confirmed_absence":True,
       "not_population_persistence_or_colonization":True,
       "species_names_or_original_observation_IDs_exported":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    cfg=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (cfg["schema"]!="structural.azores_Pico_repeated_year_field_detection_exploratory_contract.v1_274"
        or cfg["status"]!="POST_OUTCOME_EXPLORATORY_ADDITIONAL_REPEATED_POSITIVE_QUESTION"):
        raise ValueError("Pico exploratory analysis contract changed")
    root=Path(__file__).resolve().parents[1]
    published=json.loads((root/cfg["source"]["source_manifest"]).read_text(encoding="utf-8"))
    pi=next((v for v in published["sources"] if v["label"]=="Pico PRIBES"),None)
    out={"schema":"structural.azores_Pico_repeated_field_positive.v1_274",
         "status":"STOP_ORIGINAL_PICO_SOURCE_TRANSPORT",
         "S2_S3_S4_values_opened":0,
         "GEB_scientific_HOLD":True,"eBird_off":True}
    try:
        if pi is None: raise ValueError("Original Pico published source absent from frozen manifest")
        raw=get_original(pi)
        picos=read_dated_field(raw,{"Pico"})
        if (picos["raw_event_rows"]!=2801 or
            picos["source_MDY_recovered_events"]!=2801 or
            picos["field_event_year_counts"]!=YEAR_HIST):
            raise ValueError("Pico author year-month-day counts changed from response-free date gate")
        hist=cfg["source"]
        s1contract=json.loads((root/hist["source_ID_contract"]).read_text(encoding="utf-8"))
        s1=download_original(s1contract["S1"]["CSIC_original_url"],332776,5_000_000)
        if hashlib.sha256(s1).hexdigest()!=S1_SHA:
            raise ValueError("Original CSIC historical case source checksum mismatch")
        original=parse_sheet_s1(s1)
        if len(original)!=168:raise ValueError("Original S1 168-record universe changed")
        comp=repeated_pico_detection({"Pico PRIBES":picos},original)
        if (comp["historically_loss_affected_Azores_taxa"]!=20 or
            comp["historically_loss_affected_taxa_seen_on_Pico"]!=11):
            raise ValueError("Earlier original field 20-S1/11-Pico confirmed-case result changed")
        out.update({"status":"VERIFIED_REPEATED_PICO_DATED_FIELD_POSITIVES_ONLY",
            "source_Pico_SHA256":pi["sha256"],
            "source_Pico_event_rows":2801,
            "source_Pico_year_events":picos["field_event_year_counts"],
            "source_Pico_unique_species_island_pairs":picos["unique_species_island_positive_pairs"],
            "historical_strict_S1_Azores_taxa":20,
            "comparison":comp})
    except Exception as exc:
        out["stop_reason"]=str(exc)[:450]
        out["stop_error_type"]=type(exc).__name__
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],
        "S1_Pico_taxa_2plus_years":out.get("comparison",{}).get("historic_loss_taxa_seen_in_2plus_Pico_years"),
        "error":out.get("stop_reason")},sort_keys=True))
    if out["status"]!="VERIFIED_REPEATED_PICO_DATED_FIELD_POSITIVES_ONLY":
        raise SystemExit(2)


if __name__=="__main__":
    main()
