from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_scorer():
    p=ROOT/"scripts/score_global_mammals_sealed_species_v1_95.py"
    spec=importlib.util.spec_from_file_location("score2",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_scoring_contract_keeps_one_primary_and_three_secondary_predictions():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_scoring_contract_v1_95.json").read_text())
    assert x["result_interpretation"]["P1_is_the_only_primary"] is True
    assert x["result_interpretation"]["P2_P3_P4_are_preregistered_secondary_signatures"] is True
    assert x["result_interpretation"]["secondary_signatures_cannot_rescue_failed_P1"] is True
    assert x["heldout_response_authorized_now"] is False

def test_secondary_bootstrap_seeds_are_fixed_before_response():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_scoring_contract_v1_95.json").read_text())
    assert x["P1"]["bootstrap_seed"]==20261003
    assert x["P2"]["absence_bootstrap_seed"]==20261004
    assert x["P2"]["presence_bootstrap_seed"]==20261005
    assert x["P3"]["bootstrap_seed"]==20261006
    assert x["P4"]["bootstrap_seed"]==20261007

def test_router_decodes_only_96_heldout_columns():
    s=(ROOT/"scripts/run_global_mammals_sealed_species_response_v1_95.py").read_text()
    assert "wanted=set(cols)" in s
    assert "if idx in wanted:picked[idx]=field" in s
    assert '"heldout_non_second_layer_values_decoded":0' in s
    assert '"pilot_occurrence_values_decoded_during_run":0' in s

def test_scorer_parses_20_null_predictions_and_mask():
    s=(ROOT/"scripts/score_global_mammals_sealed_species_v1_95.py").read_text()
    assert "(ne,ns,K)!=(4126,96,20)" in s
    assert "actual_C_better_than_n_of_20_nulls" in s
    assert "mean_nonempty_minus_empty_C_minus_R3" in s
    assert "secondary_signatures_can_rescue_failed_P1" in s

def test_bootstrap_is_deterministic():
    m=load_scorer()
    vals={"a":-1.0,"b":0.0,"c":1.0}
    assert m.bootstrap(vals,100,123)==m.bootstrap(vals,100,123)
