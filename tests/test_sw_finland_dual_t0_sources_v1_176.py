from pathlib import Path
import importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/validate_sw_finland_dual_t0_sources_v1_176.py"
CONTRACT=ROOT/"development/sw_finland_dual_t0_source_identity_contract_v1_176.json"

def load():
    spec=importlib.util.spec_from_file_location("swf176",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_anchor_table_is_alphabetic_and_response_independent():
    c=json.loads(CONTRACT.read_text())
    a=c["alphabetic_t0_anchor_table"]
    assert len(a["potential_islands"])==33
    assert a["selection_rule"].startswith("first 33 species")
    assert a["future_summary_columns_used"] is False
    assert a["potential_islands"]["Agrostis canina"]==331
    assert a["potential_islands"]["Angelica archangelica ssp. litoralis"]==171

def test_count_tolerance_is_smaller_than_one_island_gap():
    c=json.loads(CONTRACT.read_text())
    tol=c["count_consistency"]["exact_species_max_absolute_log10_residual"]
    gap=math.log10(470)-math.log10(469)
    assert tol==0.0001
    assert tol<gap

def test_distance_gate_is_species_specific_and_strict():
    c=json.loads(CONTRACT.read_text())
    d=c["distance_consistency"]
    assert d["minimum_calibration_species"]==20
    assert d["minimum_calibration_rows"]==1000
    assert d["anchor_max_absolute_log10_residual"]==0.0001
    assert d["exact_species_max_absolute_log10_residual"]==0.0001

def test_future_outcome_is_sealed_and_no_ebird():
    c=json.loads(CONTRACT.read_text())
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["protected_outcome_values_decoded"]==0
    assert c["response_boundary"]["eBird_enabled"] is False
    assert c["exact_source_identity"]["no_threshold_relaxation_after_run"] is True

def test_ols_helper_recovers_affine_relation():
    m=load();xs=[-2,-1,0,1,2];ys=[3+0.7*x for x in xs]
    a,b=m.ols_xy(xs,ys)
    assert abs(a-3)<1e-12 and abs(b-.7)<1e-12
