import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("w209",ROOT/"scripts/run_wolfe_joint_predator_v1_209.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_strata_and_estimand_on_synthetic_factorial():
    groups={}
    for n,het in [(1,"homogeneous"),(4,"homogeneous"),(4,"heterogeneous"),
                  (6,"homogeneous"),(6,"heterogeneous")]:
        for mat in ("none","low","high"):
            for cor in ("none","low","high"):
                groups[(n,het,mat,cor)]=[(0,0,0)]*4
    for n,mat,cor in m.STRATA:
        groups[(n,"heterogeneous",mat,cor)]=[(1,1,1)]*4
    assert len(m.STRATA)==18
    assert m.estimate(groups,2)==1.0
    a=m.run(groups,B=100,seed=42)
    assert a["primary_joint_heterogeneous_minus_homogeneous"]==1
    assert a["bootstrap_95pct"]==[1,1]
    assert a["independent_mammal_validation"] is False
def test_blob_and_frozen_header_guard():
    try:m.check_git_blob(b"fake")
    except ValueError:pass
    else:raise AssertionError("Did not verify frozen blob")
def test_contract_requires_prospective_qualification():
    import json
    x=json.loads((ROOT/"development/wolfe_joint_predator_contract_v1_209.json").read_text())
    assert x["status"].startswith("SPECIFIED_BEFORE_CSV_")
    assert x["contrast"]["primary"].startswith("joint guild day-21")
    assert x["hard_bounds"]["new_results_are_nonconfirmatory"] is True
    assert x["source"]["semantic_outcome_rows_read_before_contract"] is False
