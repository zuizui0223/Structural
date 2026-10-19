"""Frozen biological-method provenance after geography-only BioTIME 373/375 screen.

No BioTIME species responses, no original RDS, no external data access.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/"development/biotime_v2_island_study_source_admission_result_v1_257.json"
GIS=ROOT/"development/biotime_v2_gshhg_island_feasibility_result_freeze_v1_256.json"

def test_two_gis_positive_studies_not_two_independent_ecological_archipelago_replications():
    r=json.loads(RESULT.read_text(encoding="utf-8"))
    g=json.loads(GIS.read_text(encoding="utf-8"))
    assert r["schema"]=="structural.biotime_island_study_metadata_gate_result.v1_257"
    assert g["results"]["strict_multi_island_study_proxies"]==2
    assert {x["STUDY_ID"] for x in r["study_method_findings"]}=={"373","375"}
    assert r["pairwise_methods_evaluation"]["same_taxonomic_outcome"] is False
    assert r["pairwise_methods_evaluation"]["independent_archipelago_geographies_verified"] is False
    assert r["pairwise_methods_evaluation"]["source_to_target_movement_measured"] is False
    assert r["numerical_boundaries"]["confirmed_same_taxon_independent_archipelago_replicates_from_those_two"]==0
    assert r["decision"]["confirmatory_transition_authorized"] is False
    assert r["decision"]["GEB_scientific_HOLD"] is True

def test_original_source_provenance_and_outcome_firewalls_preserved():
    r=json.loads(RESULT.read_text(encoding="utf-8"))
    g=json.loads(GIS.read_text(encoding="utf-8"))
    assert r["sources"]["original_study_metadata_md5"]=="3daed71ed554888309f9f2443a847bea"
    assert g["source"]["GSHHG_sha256"]=="8dbbe7e071e77e9e75f2d639239099ebca8d5c16d6a07df8169729d49f15cf41"
    assert r["numerical_boundaries"]["reserved_33_species_site_response_rows_opened"]==0
    assert g["scientific_interpretation"]["new_species_response_accesses"]==0
    assert r["decision"]["eBird_off"] is True
