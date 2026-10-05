from pathlib import Path
import json,importlib.util,math
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/score_bala_source_loss_t2_v1_141.py"
    spec=importlib.util.spec_from_file_location("bala141",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_implementation_has_no_access_authorization():
    x=json.loads((ROOT/"development/bala_t2_scoring_implementation_v1_141.json").read_text())
    assert x["execution_authorized_now"] is False
    assert x["response_boundary"]["this_file_authorizes_t2_access"] is False
    assert x["response_boundary"]["same_lineage_rerun_after_t2"] is False

def test_primary_is_taxon_macro_C_minus_R2():
    x=json.loads((ROOT/"development/bala_t2_scoring_implementation_v1_141.json").read_text())
    assert x["fold_logic"]["heldout_unit"]=="MF taxon"
    assert x["primary"]["across_taxa"].startswith("equal-weight mean")
    assert x["primary"]["support"]=="point < 0 and bootstrap upper < 0"
    assert x["primary"]["seed"]==20261005

def test_noneligible_t2_quantities_are_not_decoded():
    s=(ROOT/"scripts/score_bala_source_loss_t2_v1_141.py").read_text()
    assert "tok=eligible_bytes.get(tok_raw)" in s
    segment=s.split("tok=eligible_bytes.get(tok_raw)",1)[1].split("eligible_rows_decoded+=1",1)[0]
    assert "organismQuantity" not in segment
    assert '"noneligible_t2_quantity_values_decoded":0' in s

def test_type7_is_deterministic():
    m=load_module()
    assert m.type7([0.0,1.0,2.0],0.5)==1.0
    assert abs(m.logloss(0.8,1)+math.log(0.8))<1e-15

def test_secondaries_cannot_rescue_primary():
    x=json.loads((ROOT/"development/bala_t2_scoring_implementation_v1_141.json").read_text())
    assert x["secondary_nonrescuing"]["may_rescue_primary"] is False
