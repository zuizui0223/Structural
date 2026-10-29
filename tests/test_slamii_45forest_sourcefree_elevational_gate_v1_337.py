"""45 site SLAM II original source-free site-elevation scientific closure."""
import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from slamii_45forest_sourcefree_elevational_gate_v1_337 import audit
def source():
    return json.loads((ROOT/"development/slamii_habitat_elevation_site_only_conclusion_v1_337.json").read_text())
def test_source_original_three_islands_are_elevationally_segregated_but_not_causal():
    d=audit(source())
    assert d["status"]=="THREE_ISLAND_NATIVE_FOREST_HIGHER_ELEVATION_MATCHED_CAUSAL_GATE_TERMINAL"
    assert d["source_native_minus_altered_median_elevation_by_island_m"]=={
        "FLO":260,"SMR":113,"TER":193.5}
    assert abs(d["source_original_island_equal_native_minus_altered_median_elevation_m"]-188.83333333333334)<1e-12
    assert d["native_higher_original_island_n"]==3
    assert d["source_in_100m_equal_year_effort_matched_original_plot_pair_total_2islands"]==1
    assert not d["source_original_min_2pairs_per_island_rule_passed"]
    assert d["original_Source_Event_and_Occurrence_rows_reopened"]==0
    assert d["GEB_scientific_HOLD"] and d["new_confirmatory_systems"]==0 and not d["eBird_used"]
def test_prior_paper_v18_habitat_discrepancy_cannot_be_retconned():
    s=source()
    s["source"]["source_2023_native_mixed_exotic_classes"]["native"]=8
    with pytest.raises(ValueError,match="original source full"):
        audit(s)
def test_sampling_matched_terceira_stop_not_backfilled():
    s=source()
    s["island_observations"]["TER"]["source_year_effort_100m_pairs"]=2
    with pytest.raises(ValueError,match="pair coverage"):
        audit(s)
def test_original_species_firewall_cannot_be_bypassed():
    s=source()
    s["source"]["Occurrence_rows_read"]=2097
    with pytest.raises(ValueError,match="taxon firewall"):
        audit(s)
    s=source();s["firewall"]["GEB_scientific_HOLD"]=False
    with pytest.raises(ValueError,match="taxon firewall"):
        audit(s)
