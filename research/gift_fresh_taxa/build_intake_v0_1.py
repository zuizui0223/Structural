#!/usr/bin/env python3
"""Build a v0.10 intake for a frozen untouched GIFT taxonomic universe."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED={
    "Pteridophyta":"177b41f45b7bc06b4ec3a79fcbec3b12422bb7db3de06650c2527c7189290f37",
    "Gymnospermae":"42d018ac6713f2b4f72b29f6c27817b60ba8853696a3508ca5a6fa1e1f22ef49",
}
def sha(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--universe",type=Path,required=True);args=ap.parse_args()
    u=json.loads(args.universe.read_text())
    taxon=u["taxon_name"]
    if u["universe_fingerprint"]!=EXPECTED[taxon]:raise RuntimeError("universe fingerprint drift")
    if u["response_values_accessed"] is not False or u["species_composition_endpoint_called"] is not False:raise RuntimeError("response not sealed")
    response_surface=sorted(
        (g["archipelago_id"],str(lid))
        for g in u["groups"] for lid in g["list_ids"]
    )
    response_hash=sha(response_surface)
    geometry_hash=sha(u["closed_aislands_exclusion"])
    source_fp=sha({"taxon":taxon,"universe":u["universe_fingerprint"],"response_surface":response_hash,"geometry":geometry_hash})
    intake={
      "schema":"structural.independent_system_intake.v0_10",
      "status":"response_sealed_intake_draft",
      "system_id":f"gift32_{taxon.lower()}_global_archipelago_v1",
      "source_id":f"GIFT 3.2 {taxon} + A-Islands geometry-only exclusion",
      "source_version":"GIFT-3.2",
      "source_fingerprint":source_fp,
      "origin":"fresh_taxonomic_response_surface_after_angiosperm_terminal_stop",
      "is_prior_closed_system":False,
      "response_firewall_state":"response_sealed",
      "response_values_accessed":False,
      "source_files":[
        {"file_id":f"{taxon}_predictor_universe","sha256":u["universe_fingerprint"],"role":"safe_metadata","opened":True},
        {"file_id":"aislands_geometry_exclusion","sha256":geometry_hash,"role":"geometry","opened":True},
        {"file_id":f"{taxon}_checklist_response_surface","sha256":response_hash,"role":"response","opened":False},
      ],
      "freshness_metadata":{
        "temporal_replication":"no","immutable_source_identity":"yes","spatial_unit_id_documented":"yes",
        "coordinates_or_geometry_documented":"yes","outcome_file_separable":"yes",
        "operator_semantics_declarable":"yes","connectivity_question_already_published":"no",
        "response_result_seen_by_project":"no",
      },
      "selection_firewall":{
        "candidate_hunt_active":False,"system_selected_using_response_direction":False,
        "system_selected_using_connectivity_result":False,"mechanism_lanes_selected_using_response_direction":False,
        "graph_scale_selected_using_response_direction":False,"endpoint_selected_using_response_direction":False,
        "published_effect_direction_used_for_selection":False,
      },
      "requested_mechanism_lanes":["M4_environmental_proxy"],
      "response_blind_data_support":{
        "temporal_transition_metadata_available":False,
        "genetic_sampling_metadata_available":False,
        "environment_predictor_metadata_available":True,
      },
      "hypothesis_bindings":{
        "structural_partition_contract":"development/transition_pilot_protocol_contract_v0_31.json",
        "ecological_hypothesis":"development/prospective_extreme_isolation_topology_hypothesis_v0_3.json",
        "mechanism_framework":"development/prospective_mechanism_discrimination_v0_1.json",
      },
      "study_specific_state":{
        "taxon":taxon,"universe_fingerprint":u["universe_fingerprint"],
        "response_surface_sha256":response_hash,"n_archipelagos":u["n_final_archipelagos"],
        "n_islands":u["n_final_islands"],"primary_extreme_rule":u["extreme_rule"]["primary"],
        "angiosperm_pilot_evidence_contribution":0,
      },
    }
    print(json.dumps(intake,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
