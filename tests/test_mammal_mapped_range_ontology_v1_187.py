from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"development/global_mammals_response_ontology_audit_v1_187.json"
STATUS=ROOT/"development/current_status_v1_187.json"
PRIORITY=ROOT/"development/structural_active_priority_v1_187.json"
CURRENT=ROOT/"manuscript/submission/GEB_CURRENT.json"
INTAKE=ROOT/"development/global_mammals_independent_checklist_preintake_v1_188.json"

def test_source_ontology_requires_independent_occurrence_validation():
    a=json.loads(AUDIT.read_text())
    assert a["empirical_response_origin"]["species_island_field_survey_replicates_in_primary_archive"] is False
    assert "IUCN" in a["empirical_response_origin"]["primary_procedure"]
    assert "historically" in a["empirical_response_origin"]["important_mixed_time_semantics"]
    assert a["structural_model_provenance"]["training_and_validation_share_label_generation_process"] is True
    assert a["claim_adjudication"]["evidence_class"].startswith("within-one-map")

def test_current_hold_does_not_reclassify_results():
    s=json.loads(STATUS.read_text())
    assert s["submission_status"]=="SCIENTIFIC_HOLD_PENDING_INDEPENDENT_SPECIES_ISLAND_VALIDATION"
    assert s["central_empirical_evidence"]["ultrarare_occurrence"]["actual_better_than_nulls"]=="20/20"
    assert s["response_free_source_structure"]["target_space_turnover_v1_181"]["mean_actual_minus_null_beta"] < 0
    assert s["independent_temporal_boundary"]["supported"] is False
    c=json.loads(CURRENT.read_text())
    assert c["submission_authorized"] is False
    assert c["version"]=="v1.185"

def test_external_gate_is_predeclared_before_labels():
    p=json.loads(PRIORITY.read_text())
    x=json.loads(INTAKE.read_text())
    assert any("eBird" in x for x in p["do_not"])
    assert x["preoutcome_thresholds"]["min_exact_focal_species_header_overlap"]==20
    assert x["source"]["reported_islands"]==204
    assert x["allowed_preoutcome_access"]["source_island_species_binary_labels"] is False
    assert x["future_endpoint"]["label_access_now_authorized"] is False
    assert x["policy"]["eBird_used"] is False
