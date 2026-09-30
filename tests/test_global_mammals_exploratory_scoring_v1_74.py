from pathlib import Path
import importlib.util,json,struct
ROOT=Path(__file__).resolve().parents[1]

def load_scorer():
    p=ROOT/"scripts/score_global_mammals_exploratory_v1_74.py"
    spec=importlib.util.spec_from_file_location("mm_score",p)
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

def test_scoring_contract_is_block_weighted_and_nonconfirmatory():
    x=json.loads((ROOT/"development/global_mammals_exploratory_scoring_contract_v1_74.json").read_text())
    p=x["primary_exploratory_estimand"]
    assert p["bootstrap_unit"]=="frozen confirmatory spatial block"
    assert p["bootstrap_replicates"]==10000
    assert p["bootstrap_seed"]==20261001
    assert x["interpretation"]["counts_as_fresh_confirmation"] is False
    assert x["interpretation"]["counts_as_primary_confirmatory_evidence"] is False
    assert x["interpretation"]["cannot_rescue_or_reverse_terminal_v165"] is True

def test_router_reads_only_79_focal_confirmatory_values():
    s=(ROOT/"scripts/run_global_mammals_exploratory_confirmatory_v1_74.py").read_text()
    assert "wanted=set(focal_columns)" in s
    assert 'if idx in wanted:' in s
    assert '"confirmatory_nonfocal_values_decoded":0' in s
    assert '"pilot_occurrence_values_decoded":0' in s
    assert '"excluded_occurrence_values_decoded":0' in s

def test_workflow_consumes_then_scores_once():
    s=(ROOT/".github/workflows/global-mammals-exploratory-scoring-v1_75.yml").read_text()
    consume=s.index("Consume 79 focal values on confirmatory islands once")
    score=s.index("Score frozen exploratory primary immediately")
    assert consume < score
    assert "f48ab1f09c825f99bced712a64e7c5f1ff927d024fdbe1aaf80db588b0372ef8" in s
    assert "c15cb86ba0b0bd88e8d22fd566c495adcec113a3c9f7dd65f4b7c3415796335e" in s
    assert "counts_as_primary_confirmatory_evidence" in s

def test_request_is_exact_and_never_confirmatory_evidence():
    x=json.loads((ROOT/"development/global_mammals_exploratory_scoring_request_v1_75.json").read_text())
    assert x["prediction_artifact_id"]==11112450910
    assert x["confirmatory_entities"]==4126
    assert x["confirmatory_blocks"]==168
    assert x["focal_species"]==79
    assert x["expected_target_cells"]==325954
    assert x["exploratory_confirmatory_response_authorized"] is True
    assert x["counts_as_confirmatory_evidence"] is False
    assert x["fresh_status_restored"] is False
    assert x["one_shot"] is True
