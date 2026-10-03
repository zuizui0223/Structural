from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_execution_request_is_irreversible_and_exact():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_execution_request_v1_118.json").read_text())
    assert x["status"]=="AUTHORIZE_ONE_SHOT_ULTRARARE_HELDOUT_SCORING"
    assert x["actual_preconfirm_artifact_id"]==11284534666
    assert x["null_artifact_id"]==11285972572
    assert x["heldout_species"]==529
    assert x["expected_target_cells"]==2182654
    assert x["decode_only_ultrarare_species"] is True
    assert x["rerun_after_first_decode"] is False

def test_workflow_decodes_then_scores_once():
    s=(ROOT/".github/workflows/global-mammals-ultrarare-execute-v1_118.yml").read_text()
    decode=s.index("Consume exactly the 529 ultrarare heldout species once")
    score=s.index("Score frozen ultrarare hypotheses immediately")
    assert decode < score
    assert "run_global_mammals_ultrarare_response_v1_115.py" in s
    assert "score_global_mammals_ultrarare_v1_115.py" in s
    assert "heldout_non_ultrarare_values_decoded" in s
    assert "rerun_authorized" in s

def test_workflow_binds_exact_preconfirm_surfaces():
    s=(ROOT/".github/workflows/global-mammals-ultrarare-execute-v1_118.yml").read_text()
    assert "3307a2e058f5f8223eaf0c2d69241acd938e96b93cb02643b1b7d63b425fae04" in s
    assert "300f0001d250dde01bc0240be3d20898399300fcac5f405e76bfd0f8524495c3" in s
    assert "11284534666" in s
    assert "11285972572" in s

def test_scientific_contract_keeps_presence_primary():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_scoring_contract_v1_115.json").read_text())
    assert x["primary_presence_opportunity"]["favourable_direction"]=="negative"
    assert x["secondary_topology_specificity"]["may_rescue_primary"] is False
    assert x["evidence_language"]["geographic_independence_claim_authorized"] is False
