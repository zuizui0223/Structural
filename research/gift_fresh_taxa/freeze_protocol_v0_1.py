#!/usr/bin/env python3
"""Freeze fresh-taxonomic GIFT study protocol before any taxon response opens."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED={
    "Pteridophyta":"62824026e819a3f07a642f4babe6a28a2a58d9bf29594ad9fbb572f7fdf60adc",
    "Gymnospermae":"42d018ac6713f2b4f72b29f6c27817b60ba8853696a3508ca5a6fa1e1f22ef49",
}
SALT="gift-fresh-taxonomic-pilot-v1"
SCALES=[25.0,50.0,125.0,250.0]
CLIMATE=["wc2.0_bio_30s_01","wc2.0_bio_30s_05","wc2.0_bio_30s_06","wc2.0_bio_30s_12","wc2.0_bio_30s_15"]
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def rank(taxon,g):
    return hashlib.sha256(f"{taxon}|{g['archipelago_id']}|{SALT}".encode()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--universe",type=Path,required=True);ap.add_argument("--selection-receipt",type=Path,required=True);ap.add_argument("--geology-crosswalk",type=Path,required=True);args=ap.parse_args()
    u=json.loads(args.universe.read_text()); sel=json.loads(args.selection_receipt.read_text()); geo=json.loads(args.geology_crosswalk.read_text()); taxon=u["taxon_name"]
    if geo.get("universe_fingerprint")!=u["universe_fingerprint"] or geo.get("response_values_accessed") is not False:raise RuntimeError("geology crosswalk drift")
    if u["universe_fingerprint"]!=EXPECTED[taxon]:raise RuntimeError("universe drift")
    if sel.get("status")!="FROZEN_RESPONSE_BLIND_CANDIDATE_SELECTION":raise RuntimeError("candidate selection not frozen")
    if sel.get("species_composition_endpoint_called") is not False:raise RuntimeError("candidate selection opened response")
    if taxon not in sel.get("selected_taxa",[]):raise RuntimeError(f"{taxon} not selected by frozen metadata rule")
    by={}
    for g in u["groups"]:by.setdefault(g["support_class"],[]).append(g)
    required=("extreme_only","paired","nonextreme_only")
    if any(not by.get(k) for k in required):raise RuntimeError("missing support class")
    pilot=[sorted(by[k],key=lambda g:(rank(taxon,g),g["archipelago_id"]))[0] for k in required]
    pilot_ids={g["archipelago_id"] for g in pilot}
    confirm=[g for g in u["groups"] if g["archipelago_id"] not in pilot_ids]
    p_lists=sorted({str(lid) for g in pilot for lid in g["list_ids"]},key=int)
    c_lists=sorted({str(lid) for g in confirm for lid in g["list_ids"]},key=int)
    if set(p_lists)&set(c_lists):raise RuntimeError("list response surfaces overlap")
    protocol={
      "schema":"structural.gift_fresh_taxon_protocol.v0_1","status":"FROZEN_BEFORE_PILOT_RESPONSE",
      "study_family":"response-blind two-clade macro-study; not Structural v0.10 independent-system confirmation",
      "gift_version":"3.2","taxon_name":taxon,"taxon_ID":u["taxon_ID"],
      "response_values_accessed":False,"pilot_response_opened":False,"confirmatory_response_opened":False,
      "candidate_selection_fingerprint":sel["selection_fingerprint"],"universe_fingerprint":u["universe_fingerprint"],
      "pilot_selection":{
        "rule":f"one archipelago per support class chosen by lowest SHA256('<taxon>|<archipelago_id>|{SALT}')",
        "selection_uses_response":False,"pilot_archipelagos":[g["archipelago_id"] for g in pilot],
        "confirmatory_archipelagos":[g["archipelago_id"] for g in confirm],
        "pilot_list_set_sha256":sha(p_lists),"confirmatory_list_set_sha256":sha(c_lists),"list_overlap":0,
      },
      "data_quality_boundary":{
        "reference_filter":"only GIFT references with checklist=1 and unrestricted access",
        "complete_scope_interpretation":"complete_taxon and complete_floristic indicate intended scope, not guaranteed exhaustive detection",
        "suit_geo_limitation":"GIFT documents that obvious-incompleteness suit_geo auditing was conducted mainly for native angiosperms",
        "absence_claim":"0 means no unambiguous native record in the declared curated checklist union for that island; it is not asserted to be a perfect biological absence",
      },
      "response_semantics":{
        "endpoint":f"native {taxon} checklist incidence",
        "query":f"checklists listid=<frozen pilot/confirmatory list> taxonid={u['taxon_ID']} filter=native namesmatched=0",
        "presence":"native=1 and questionable!=1 and quest_native!=1",
        "uncertain":"native=1 and (questionable=1 or quest_native=1)",
        "absence":"no returned unambiguous native occurrence and no uncertain native row for work_ID in island checklist union",
      },
      "burned_pilot":{
        "models_allowed":False,"effect_sizes_allowed":False,"prediction_scores_allowed":False,
        "audit_unit":"species x archipelago x frozen spatial block",
        "minimum_training_presences":5,"minimum_training_absences":5,"minimum_test_rows":3,
        "species_archipelago_estimable":"at least 3 of 4 folds pass",
        "archipelago_pass":"at least 30 species are estimable",
        "study_pass":"at least 2 of 3 pilot archipelagos pass, with >=1 passing extreme contributor and >=1 passing non-extreme contributor",
        "pilot_predictive_denominator_contribution":0,
      },
      "graph_operator":{"scope":"within archipelago","distance":"great-circle centroid","radii_km":SCALES,"inherited_from_A_Islands":True},
      "reference":{
        "R0":CLIMATE,
        "R1":CLIMATE+["log_area_km2","log1p_mainland_dist_km","nearest_training_presence_km"],
        "R2":CLIMATE+["log_area_km2","log1p_mainland_dist_km","nearest_training_presence_km","multi_source_pressure","area_weighted_source_pressure"],
        "R3":CLIMATE+["log_area_km2","log1p_mainland_dist_km","nearest_training_presence_km","multi_source_pressure","area_weighted_source_pressure","SLMP","GMMC","nearest_other_island_km","surrounding_island_pressure","surrounding_landmass_pressure","unanchored_component_exposure","mainland_stepping_stone_frequency"],
        "C_addition":"geography_only_eog_connected_frequency",
        "comparison_model":"deterministic L2 logistic, lambda=1, training-only standardization, no tuning, same 5/5 class gate",
      },
      "H1":{"primary_rule":"global upper 25% of frozen eligible islands by GIFT dist","estimand":"archipelago-clustered difference in C-R3 heldout loss: extreme minus non-extreme","favourable_direction":"negative","q70_q80":"non-rescuing sensitivities"},
      "H2":{"primary_moderator":"archipelago GMMC-connected fraction","prediction":"topology increment becomes less favourable as historical mainland connection increases","external_geology_secondary":{"source":"Roeble et al. 2024 Supplementary Data 3","crosswalk_fingerprint":geo["crosswalk_fingerprint"],"quantitative_geology_eligible_all":geo["quantitative_geology_eligible_all"],"rule":"direct oceanic-island fraction when >=80% of GIFT entity_IDs are typed","cannot_rescue_primary":True},"claim_ceiling":"history moderator, not colonization/persistence mechanism"},
      "cross_taxon_secondary":{"authorized_only_if_both_taxa_pass_independently":True,"estimand":"Pteridophyta H1 contrast minus Gymnospermae H1 contrast","prediction":"positive (weaker topology dependence in spore-dispersed Pteridophyta)","cannot_rescue_either_taxon_primary":True},
      "forbidden_after_pilot":["change q75","change radii","weaken R3","change 5/5 gate","change 30-species archipelago pass threshold","change pilot membership","open confirmatory response after failed pilot"],
      "confirmatory_response_authorized":False,
    }
    protocol["protocol_fingerprint"]=sha(protocol)
    print(json.dumps(protocol,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
