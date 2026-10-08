import importlib.util
import json
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/source_cofailure_known_truth_v1_203.py"
RECEIPT=ROOT/"development/source_cofailure_known_truth_v1_203.json"
META=ROOT/"development/kelp_patch_grain_version_gate_v1_203.json"

def _module():
    spec=importlib.util.spec_from_file_location("source_cofailure_v203",SCRIPT)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_exact_known_truth_three_source_moments():
    m=_module()
    data={name:m.moments(m.scenario(name)) for name in
          ("independent","even_parity","odd_parity")}
    assert data==json.loads(RECEIPT.read_text())["scenarios"]
    for item in data.values():
        assert item["marginal_activity_probabilities"]==["1/2"]*3
        assert item["pairwise_joint_activity"]==["1/4"]*3
        assert item["pairwise_covariance"]==["0"]*3
        assert item["equal_weight_expected_source_input"]=="1/2"
        assert item["equal_weight_source_input_variance"]=="1/12"
    assert [data[n]["zero_active_source_probability"] for n in data]==["1/8","1/4","0"]

def test_full_receipt_replays_without_ecological_data():
    m=_module()
    assert m.build_receipt()==json.loads(RECEIPT.read_text())
    x=m.build_receipt()
    assert x["source_file_access"]["ecological_observations_read"] is False
    assert x["differing_zero_delivery_probability"] is True
    assert "colonization probability" in x["not_established"][1]

def test_no_illicit_469_patch_to_117_cell_join():
    x=json.loads(META.read_text())
    assert x["distinct_study_grains"]["castorani2017"]["focal_units"].startswith("469")
    assert x["distinct_study_grains"]["wanner2024"]["focal_units"].startswith("117")
    g=x["crosswalk_requirements"]
    assert g["direct_join_authorized"] is False
    assert g["all_required_before_join"] is True
    assert g["patch_id_to_ROMS_cell"]=="NOT_VERIFIED"
    assert x["no_new_biological_values_opened"] is True
    assert x["pristine_confirmatory_eligible"] is False
    assert x["original_mammal_heldout_reopened"] is False
