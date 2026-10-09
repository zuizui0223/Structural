import json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("g234",ROOT/"scripts/adjudicate_external_mammal_support_v1_234.py")
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def test_frozen_zhoushan_preoutcome_support_failure():
 folder=ROOT/"development"
 t=json.loads((folder/"zhoushan_published_taxa_corrected_freeze_v1_231.json").read_text())
 s=json.loads((folder/"zhoushan_published_site_identity_freeze_v1_232.json").read_text())
 g=json.loads((folder/"zhoushan_heldout_geography_result_freeze_v1_233.json").read_text())
 r=m.adjudicate(t,s,g)
 assert r["status"]=="STOP_DIRECT_ORIGINAL_529_MAMMAL_FIELD_SCORE_SUPPORT_INSUFFICIENT"
 assert r["maximum_if_all_regional_original_heldout_islands_matched"]==15
 assert r["independent_geographic_heldout_blocks"]==1
 assert r["current_scoring_cells_with_verified_taxon_and_island"]==0
 assert r["can_measure_between_geographic_block_replicability"] is False
 assert r["can_admit_direct_original_model_validation"] is False
def test_guard_no_biological_response_access():
 x=json.loads((ROOT/"development/external_mammal_source_support_gate_v1_234.json").read_text())
 assert x["stop_rule"]["no_source_0_1_outcome_access"] is True
 assert x["stop_rule"]["not_evidence_that_model_prediction_was_wrong"] is True
 assert all(x["policy"].values())
