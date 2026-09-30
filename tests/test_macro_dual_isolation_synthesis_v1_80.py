from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_macro_synthesis_keeps_evidence_classes_separate():
    x=json.loads((ROOT/"development/macro_dual_isolation_synthesis_v1_80.json").read_text())
    assert x["systems"]["global_5401_mammals"]["evidence_class"]=="nonconfirmatory exploratory macro analysis"
    assert x["systems"]["GIFT_plants"]["fresh_result_available"] is False
    assert x["systems"]["boreal_beetles"]["primary_supported"] is False
    assert x["counts_as_new_confirmatory_evidence"] is False

def test_revised_principle_is_attenuation_not_handoff():
    x=json.loads((ROOT/"development/macro_dual_isolation_synthesis_v1_80.json").read_text())
    assert "opposite direction" in x["revised_general_principle"]["contrast_with_old_handoff"]
    assert x["systems"]["global_5401_mammals"]["Current_isolation_spearman_equal_block"]>0
    assert x["systems"]["historical_318_mammals"]["extreme_minus_nonextreme"]>0

def test_two_taxon_confirmation_is_forbidden():
    x=json.loads((ROOT/"development/macro_dual_isolation_synthesis_v1_80.json").read_text())
    assert "two-taxon confirmatory replication" in x["claim_boundary"]["forbidden"]
    assert "successful confirmation by GIFT" in x["claim_boundary"]["forbidden"]
