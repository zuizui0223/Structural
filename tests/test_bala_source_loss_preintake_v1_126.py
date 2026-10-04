import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def test_bala_v126_is_three_wave_response_unopened_preintake():
    x = load("development/bala_source_loss_preintake_v1_126.json")
    assert x["status"] == "RESPONSE_UNOPENED_THREE_WAVE_CORE_PANEL_PREINTAKE"
    assert x["why_candidate_is_special"]["three_wave_design"] is True
    assert x["three_wave_mapping"]["t0"].startswith("BALA1")
    assert x["three_wave_mapping"]["t1"].startswith("BALA2")
    assert x["three_wave_mapping"]["t2"].startswith("BALA3")
    assert x["evidence_status"]["focal_occurrence_values_opened_by_structural"] is False
    assert x["evidence_status"]["source_loss_effect_computed"] is False

def test_bala_v126_requires_raw_event_resolution_of_metadata_drift():
    x = load("development/bala_source_loss_preintake_v1_126.json")
    g = x["core_panel_gate"]
    assert g["metadata_30_vs_31_discrepancy_must_be_resolved"] is True
    assert g["phase_date_discrepancies_must_be_resolved"] is True
    assert g["if_not_resolved"] == "STOP"

def test_bala_v126_uses_taxon_partition_not_second_time_window():
    x = load("development/bala_source_loss_preintake_v1_126.json")
    p = x["taxon_partition_problem"]
    assert "one three-wave temporal sequence" in p["reason"]
    assert "deterministic disjoint taxon partition" in p["required_solution"]
    assert "no source-leverage effect estimate" in p["pilot_role"]
    assert "remains sealed" in p["confirmatory_role"]

def test_bala_v126_preserves_self_anchor_and_zero_boundary():
    x = load("development/bala_source_loss_preintake_v1_126.json")
    assert x["provisional_endpoint"]["self_anchor_exclusion_required"] is True
    assert "missing or incomparable" in x["stop_conditions"][-1].lower()
