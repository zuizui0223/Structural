from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v137_failure_consumed_no_pilot_response():
    x=json.loads((ROOT/"development/bala_pilot_estimability_stop_v1_137_1.json").read_text())
    b=x["response_boundary_at_stop"]
    assert b["pilot_runner_started"] is False
    assert b["pilot_occurrence_rows_decoded"]==0
    assert b["pilot_organismQuantity_values_decoded"]==0
    assert b["pilot_taxonomy_values_decoded"]==0
    assert b["confirmatory_occurrence_values_opened"]==0

def test_retry_changes_no_scientific_gate():
    x=json.loads((ROOT/"development/bala_pilot_estimability_retry_request_v1_137_1.json").read_text())
    assert x["scientific_contract_changed"] is False
    assert x["advance_thresholds_changed"] is False
    assert x["taxonomic_scope_changed"] is False
    assert x["surveyed_zero_rule_changed"] is False
    assert x["taxon_partition_changed"] is False

def test_island_mapping_is_response_independent_and_cross_checked():
    s=(ROOT/"scripts/run_bala_pilot_estimability_v1_137_1.py").read_text()
    assert 'island=lineage[:3]' in s
    assert 'location[:3]!=island' in s
    assert '{"FAI","FLO","PIC","SJG","SMG","SMR","TER"}' in s
    assert 'r["island"]' not in s

def test_retry_uses_exact_correct_pitfall_artifact_name():
    s=(ROOT/".github/workflows/bala-pilot-estimability-v1_137_1.yml").read_text()
    assert "bala-v134-pitfall-quality-771e52a6bda4e6c58c58e7e2625cc709454bfb52-37211022254" in s
    assert "run_bala_pilot_estimability_v1_137_1.py" in s
    assert "confirmatory_occurrence_rows.sealed.tsv" not in s.split("Open pilot taxa once",1)[1].split("Enforce no pilot effect",1)[0]

def test_same_frozen_thresholds_remain_in_force():
    x=json.loads((ROOT/"development/bala_pilot_estimability_contract_v1_137.json").read_text())
    g=x["advance_gate"]
    assert g["minimum_taxonomically_eligible_pilot_taxa"]==30
    assert g["minimum_exactly_one_source_loss_taxa"]==5
    assert g["minimum_exactly_one_loss_target_rows"]==20
    assert g["minimum_t2_contractions_across_exactly_one_loss_targets"]==5
    assert g["minimum_t2_persistences_across_exactly_one_loss_targets"]==5
