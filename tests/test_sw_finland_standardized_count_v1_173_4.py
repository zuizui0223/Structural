from pathlib import Path
import importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/recover_sw_finland_numeric_counts_v1_173_4.py"
CONTRACT=ROOT/"development/sw_finland_standardized_historical_count_contract_v1_173_4.json"

def load():
    spec=importlib.util.spec_from_file_location("swf1734",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_published_logx_inverse_not_logxplus1():
    m=load();counts=[7,13,23,26,30,66,140,170,300,346,460];mu=1.2;sd=.63
    z=[(math.log10(n)-mu)/sd for n in counts]
    a,b=m.ols_xy(z,[math.log10(n) for n in counts])
    assert abs(a-mu)<1e-12 and abs(b-sd)<1e-12
    assert [round(10**(a+b*x)) for x in z]==counts

def test_added_anchors_are_table_order_not_future_performance_selected():
    c=json.loads(CONTRACT.read_text())
    assert c["anchors"]["additional_table_order_anchors"]=={
      "Angelica archangelica ssp. litoralis":300,
      "Angelica sylvestris":346,
      "Antennaria dioeca":170
    }
    assert c["anchors"]["future_colonization_performance_used_to_select_additional_anchors"] is False
    assert c["anchors"]["expected_numeric_anchor_matches"]==21

def test_thresholds_are_unchanged():
    c=json.loads(CONTRACT.read_text())
    q=c["calibration"]
    assert q["maximum_anchor_count_rounding_error"]==0.01
    assert q["maximum_all_numeric_species_count_rounding_error"]==0.05
    assert q["minimum_exact_source_species"]==30
    assert q["impossible_species_required"]==0
    assert q["thresholds_loosened_from_v1_173"] is False

def test_future_outcome_remains_sealed():
    c=json.loads(CONTRACT.read_text())
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["protected_outcome_values_decoded"]==0
    assert c["response_boundary"]["eBird_enabled"] is False
