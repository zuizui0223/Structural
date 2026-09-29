from pathlib import Path
import importlib.util,json,struct
ROOT=Path(__file__).resolve().parents[1]

def load_scorer():
    p=ROOT/"scripts/score_gift_confirmatory_v1_61.py"
    spec=importlib.util.spec_from_file_location("gift_score",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_type7_and_logloss_are_deterministic():
    m=load_scorer()
    assert m.type7([0.0,1.0,2.0],0.5)==1.0
    assert abs(m.logloss(0.8,1)+__import__("math").log(0.8))<1e-15
    assert abs(m.logloss(0.2,0)+__import__("math").log(0.8))<1e-15

def test_prediction_binary_parser(tmp_path):
    m=load_scorer()
    p=tmp_path/"x.bin"
    p.write_bytes(m.MAGIC+struct.pack("<II",2,1)+struct.pack("<dddd",0.2,0.3,0.4,0.5))
    ne,ns,v=m.parse_predictions(p)
    assert (ne,ns)==(2,1)
    assert v==[(0.2,0.3),(0.4,0.5)]

def test_confirmatory_contract_is_irreversible_and_block_weighted():
    x=json.loads((ROOT/"development/gift_confirmatory_scoring_contract_v1_61.json").read_text())
    assert x["primary"]["bootstrap_unit"]=="confirmatory archipelago"
    assert x["primary"]["bootstrap_replicates"]==10000
    assert x["primary"]["bootstrap_seed"]==20260930
    assert x["completion_semantics"]["rerun_after_first_confirmatory_checklist_request"] is False
    assert x["response_boundary"]["confirmatory_response_authorized_now"] is False

def test_confirmatory_router_cannot_request_pilot_lists():
    s=(ROOT/"scripts/run_gift_confirmatory_response_v1_61.R").read_text()
    assert 'if(any(returned_lists %in% pilot_set)) stop("pilot list_ID appeared in confirmatory response")' in s
    assert 'confirmatory_list_IDs_requested=596L' in s
    assert 'pilot_list_IDs_requested=0L' in s
    assert 'raw_species_rows_persisted=FALSE' in s

def test_workflow_replays_predictions_before_response_and_request_is_absent():
    s=(ROOT/".github/workflows/gift-confirmatory-v1_62.yml").read_text()
    replay=s.index("Exact replay predictions before response")
    gate=s.index("Require byte-identical replay before any confirmatory API request")
    access=s.index("Consume the 596-list confirmatory response once")
    score=s.index("Score frozen primary immediately")
    assert replay < gate < access < score
    assert not (ROOT/"development/gift_confirmatory_execution_request_v1_62.json").exists()

def test_preconfirmatory_freeze_has_numerically_distinct_surface():
    x=json.loads((ROOT/"development/gift_preconfirmatory_model_freeze_v1_60.json").read_text())
    a=x["response_independent_prediction_estimability_audit"]
    assert a["cells_with_abs_pC_minus_pR3_gt_1e_12"]==89911
    assert a["blocks_with_nonzero_mean_abs_probability_difference_gt_1e_12"]==59
    assert x["response_boundary"]["confirmatory_species_composition_opened"] is False
