from pathlib import Path
import json,importlib.util,math
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/build_bala_preoutcome_features_v1_140.py"
    spec=importlib.util.spec_from_file_location("bala140",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_protocol_has_no_execution_authorization():
    x=json.loads((ROOT/"development/bala_preoutcome_feature_protocol_v1_140.json").read_text())
    assert x["execution_authorized_now"] is False
    assert x["response_boundary"]["t0_t1_semantic_access_authorized_by_this_file"] is False
    assert x["response_boundary"]["t2_semantic_access_authorized"] is False

def test_primary_feature_is_Ei_with_self_anchor_exclusion():
    x=json.loads((ROOT/"development/bala_preoutcome_feature_protocol_v1_140.json").read_text())
    assert "E_i_lost_access_fraction" in x["target_feature_rows"]["features"]
    assert x["target_feature_rows"]["self_anchor_exclusion"] is True

def test_graph_effective_source_number_behaves():
    m=load_module()
    islands=["A","B","C"]
    g={"A":{"A":0.0,"B":1.0,"C":2.0},"B":{"A":1.0,"B":0.0,"C":1.0},"C":{"A":2.0,"B":1.0,"C":0.0}}
    n,shares=m.effective_source_number({"A","C"},islands,g,1.0)
    assert 1.0 <= n <= 2.0
    assert abs(sum(shares.values())-1.0)<1e-12

def test_pre_t2_gate_is_fixed_and_nontrivial():
    x=json.loads((ROOT/"development/bala_preoutcome_feature_protocol_v1_140.json").read_text())
    g=x["pre_t2_gate"]
    assert g["minimum_exactly_one_loss_taxa"]==10
    assert g["minimum_exactly_one_loss_target_rows"]==30
    assert g["minimum_prefeature_estimable_taxon_folds"]==10
    assert g["if_failed"].startswith("STOP before any BALA3")

def test_script_has_no_t2_surface_input():
    s=(ROOT/"scripts/build_bala_preoutcome_features_v1_140.py").read_text()
    assert "preoutcome_surface" in s
    assert 'ap.add_argument("t2' not in s
    assert '"t2_rows_opened":0' in s
    assert "candidate_minus_reference_effects_computed" in s
