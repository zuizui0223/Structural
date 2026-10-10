import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("wolfe212",ROOT/"scripts/run_wolfe_ambiguous_row_bounds_v1_212.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_five_source_missingness_bounds_without_ambiguous_row():
    groups={}
    for n,h in mod.CONFIG:
        for m in mod.LEVELS:
            for c in mod.LEVELS:
                groups[(n,h,m,c)]=[(0,0,0)]*4
    groups[(6,"homogeneous","low","none")]=[(0,0,0)]*3
    groups[(4,"homogeneous","high","high")]=[(0,0,0)]*3
    groups[(6,"homogeneous","high","none")]=[(0,0,0)]*3
    groups[(6,"homogeneous","high","high")]=[(0,0,0)]*3
    groups[(6,"heterogeneous","none","high")]=[(0,0,0)]*3
    result=mod.compute(groups)
    assert result["joint"]["missing_in_4_6"]==5
    assert result["joint"]["lower"]==-4/72
    assert result["joint"]["upper"]==1/72

def test_prohibited_source_relabel_and_evidence_claim():
    x=json.loads((ROOT/"development/wolfe_ambiguous_id_sensitivity_contract_v1_212.json").read_text())
    assert x["source_row_relabel_authorized"] is False
    assert x["any_other_row_drop_allowed"] is False
    assert x["preregistered_fresh_claim_allowed"] is False
    assert x["GEB_submission_authorized"] is False
    assert x["eBird"] is False
    assert "DROP 6HoLM1" in x["strategy"]

def test_source_filter_before_focal_value_decode():
    code=(ROOT/"scripts/run_wolfe_ambiguous_row_bounds_v1_212.py").read_text()
    assert 'if r[""]==AMBIGUOUS_ROW:\n            continue' in code
    assert "Never decode the excluded unit" in code
