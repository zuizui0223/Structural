from pathlib import Path
import json,importlib.util

ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/split_bala_confirmatory_temporal_v1_138.py"
    spec=importlib.util.spec_from_file_location("bala138",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_pilot_freeze_passes_without_effect_evidence():
    x=json.loads((ROOT/"development/bala_pilot_estimability_freeze_v1_138.json").read_text())
    assert x["pilot_result"]["advance_authorized"] is True
    assert x["pilot_result"]["exactly_one_loss_target_rows"]==22
    assert x["pilot_result"]["t2_contractions_across_exactly_one_loss_targets"]==13
    assert x["pilot_result"]["t2_persistences_across_exactly_one_loss_targets"]==9
    assert x["response_boundary"]["source_leverage_values_computed"]==0
    assert x["response_boundary"]["confirmatory_occurrence_values_opened"]==0

def test_temporal_firewall_authorizes_only_coreid_phase_routing():
    x=json.loads((ROOT/"development/bala_confirmatory_temporal_firewall_contract_v1_138.json").read_text())
    a=x["authorized_semantics"]
    assert a["coreid_routing_match"] is True
    assert a["phase_label_from_safe_Event_map"] is True
    for key in ("identificationRemarks_MF_token","organismQuantity","eventID_occurrence_field","scientificName","order","family","taxonRank","event_by_taxon_combinations"):
        assert a[key] is False

def test_splitter_does_not_decode_nonrouting_fields():
    s=(ROOT/"scripts/split_bala_confirmatory_temporal_v1_138.py").read_text()
    assert 'coreid=fields[coreidx].strip()' in s
    assert "identificationRemarks" not in s
    assert "organismQuantity" not in s
    assert "scientificName" not in s
    assert "taxonRank" not in s

def test_request_keeps_t2_and_source_effect_sealed():
    x=json.loads((ROOT/"development/bala_confirmatory_temporal_firewall_request_v1_138.json").read_text())
    assert x["confirmatory_semantic_access_authorized"] is False
    assert x["t2_semantic_access_authorized"] is False
    assert x["source_leverage_computation_authorized"] is False
    assert x["one_shot"] is True

def test_workflow_has_no_response_effect_scoring():
    s=(ROOT/".github/workflows/bala-confirmatory-temporal-firewall-v1_138.yml").read_text()
    assert "split_bala_confirmatory_temporal_v1_138.py" in s
    assert "confirmatory_t2_rows.sealed.tsv" in s
    assert "source_leverage_values_computed" in s
    assert "logloss" not in s.lower()
