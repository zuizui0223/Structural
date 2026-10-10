import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/"scripts/run_wolfe_joint_predator_v1_210.py"
spec=importlib.util.spec_from_file_location("v210",S)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_worst_case_missing_binary_outcomes():
    groups={}
    for n,het in m.CONFIG:
        for mat in ("none","low","high"):
            for cor in ("none","low","high"):
                groups[(n,het,mat,cor)]=[(0,0,0)]*4
    groups[(4,"heterogeneous","none","none")]=[(1,1,1)]*3
    out=m.measures(groups,2)
    assert out["observed"]==1/18
    assert out["full_assignment_missing_lower"]==3/(4*18)
    assert out["full_assignment_missing_upper"]==4/(4*18)
def test_metadata_and_nonconfirmatory():
    x=json.loads((ROOT/"development/wolfe_joint_predator_attrition_protocol_v1_210.json").read_text())
    assert x["metadata_known_before_v210_response_scoring"]["no_response_success_values_inspected"] is True
    assert x["fixed_design"]["observed_cell_sizes"]=={"cells_n4":41,"cells_n3":4}
    assert x["contrast"]["planned_n_denominator"]==4
    assert x["safeguards"]["GEB_submission_authorized"] is False
