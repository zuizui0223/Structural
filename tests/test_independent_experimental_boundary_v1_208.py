import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/independent_experimental_boundary_v1_208.json"
def test_byte_schema_technical_stop_not_biological_nonreplication():
    x=json.loads(P.read_text())
    a=x["experimental_systems"]["four_patch_laan_fox"]
    assert a["source_public_metadata"]["status"]=="PASS_EXACT_DRYAD_FILE_METADATA_ONLY"
    assert a["source_byte_header"]["status"]=="STOP_PUBLIC_FILE_HTTP"
    assert a["source_byte_header"]["source_download_http_status"]==401
    assert a["source_byte_header"]["raw_csv_headers_decoded"]==0
    assert a["source_byte_header"]["ecological_scores"]==0
def test_independent_experiment_units_and_final_day_data_grain():
    x=json.loads(P.read_text())
    w=x["experimental_systems"]["wolfe_landscape_2022"]
    assert w["experimental_units"]==180 and w["treatments"]==45
    assert w["independent_replicates_per_treatment"]==4
    assert w["controlled_total_media_volume_ml"]==48
    assert w["observation_time"].startswith("day 21")
    assert w["future_0_to_1_transition_endpoint_available"] is False
    assert "microcosm" in w["readable_header_fields"]
    assert w["biological_rows_opened"]==0
def test_no_cross_paper_biological_claim():
    x=json.loads(P.read_text())
    assert x["cross_system_identifiability"]["no_cross_dataset_pooled_mechanism_effect"] is True
    assert x["cross_system_identifiability"]["source_status"]=="NOT_ESTABLISHED_AS_ONE_COMPLETE_DATASET"
    g=x["hard_boundaries"]
    assert all(g[z]==0 for z in (
        "original_mammal_heldout_values_opened",
        "external_wolfe_outcome_values_opened",
        "external_laan_fox_outcome_values_opened",
        "active_confirmatory_systems"))
    assert all(g[z] is False for z in (
        "BALA_reopened","Hebert_retried","ALA_retried","SW_Finland_retried",
        "eBird_used","GEB_submission_authorized"))
