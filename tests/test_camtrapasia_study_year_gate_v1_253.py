import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v253",R/"scripts/camtrapasia_four_island_study_year_gate_v1_253.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def test_study_era_eligibility_does_not_read_captures():
    c=json.loads((R/"development/camtrapasia_study_year_eligibility_contract_v1_253.json").read_text())
    assert c["expected_source_survey_count"]==78
    assert c["calendar_rule"]["baseline_IUCN_map_vintage"]==2017
    assert c["limitations"]["retrospective_after_v250_response_exposure"] is True
    assert c["limitations"]["negative_observation_not_established_without_detection_model"] is True
    assert all(z is False for z in c["safeguards"].values())
def test_year_labels():
    assert mod.year("2017")==2017
    assert mod.year("2018")==2018
    assert mod.year("2018.0") is None
    assert mod.year("NA") is None
