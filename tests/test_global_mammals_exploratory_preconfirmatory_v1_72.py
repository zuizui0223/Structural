from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_pilot_artifact_is_frozen_and_nonconfirmatory():
    x=json.loads((ROOT/"development/global_mammals_exploratory_pilot_freeze_v1_72.json").read_text())
    assert x["source_execution"]["artifact_id"]==11112360652
    assert x["result"]["focal_species"]==79
    assert x["result"]["confirmatory_occurrence_values_decoded"]==0
    assert x["response_boundary"]["counts_as_primary_confirmatory_evidence"] is False

def test_preconfirmatory_contract_is_exact_v167_method():
    x=json.loads((ROOT/"development/global_mammals_exploratory_preconfirmatory_contract_v1_72.json").read_text())
    assert x["dimensions"]["training_rows"]==100725
    assert x["dimensions"]["confirmatory_prediction_cells"]==325954
    assert x["model_method"]=="exactly development/global_mammals_macro_model_contract_v1_67.json"
    assert x["numerics"]["numpy_version"]=="2.3.3"
    assert x["response_boundary"]["confirmatory_occurrence_opened"] is False
    assert x["response_boundary"]["counts_as_primary_confirmatory_evidence"] is False

def test_model_script_uses_block_exclusion_and_pilot_only_confirmatory_sources():
    s=(ROOT/"scripts/freeze_global_mammals_exploratory_preconfirmatory_v1_72.py").read_text()
    assert 'allowed=(pilot_block!=smap[target_id]["block_id"])' in s
    assert 'if training:' in s
    assert 'Dg=np.empty((5401,1275)' in s
    assert 'confirmatory_target_values_used":False' in s
    assert 'MAGIC=b"STRUCTURAL_MAMMAL_PRED_V1\\n"' in s

def test_execution_request_opens_no_confirmatory_response():
    x=json.loads((ROOT/"development/global_mammals_exploratory_preconfirmatory_request_v1_73.json").read_text())
    assert x["focal_species"]==79
    assert x["confirmatory_entities"]==4126
    assert x["expected_prediction_cells"]==325954
    assert x["confirmatory_occurrence_authorized"] is False
    assert x["counts_as_confirmatory_evidence"] is False
