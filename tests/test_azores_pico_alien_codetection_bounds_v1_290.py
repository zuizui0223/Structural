"""Exact source-free bounds for biological co-occurrence; no new data opening."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from azores_pico_alien_codetection_bounds_v1_290 import calculate

def fixture():
    d=json.loads((ROOT/"development/azores_pico_source_aggregates_v1_290.json").read_text(encoding="utf-8"))
    p=json.loads((ROOT/"development/azores_pico_alien_binary_partial_id_protocol_v1_290.json").read_text(encoding="utf-8"))
    return d,p

def test_exact_complete_binary_alien_codetection_gap_is_forced_negative():
    a,b=fixture()
    r=calculate(a,b)
    assert r["status"]=="AGGREGATE_ONLY_EXACT_CO_DETECTION_PARTIAL_IDENTIFICATION"
    assert r["feasible_binary_alien_codetection_count_pairs"]==[[6,5],[7,4],[8,3]]
    assert r["alien_codetection_frequency_difference_lower_bound"]["exact"]=="-13/19"
    assert r["alien_codetection_frequency_difference_upper_bound"]["exact"]=="-17/95"
    assert r["alien_codetection_ratio_lower_bound"]["exact"]=="6/19"
    assert r["alien_codetection_ratio_upper_bound"]["exact"]=="40/57"
    assert r["all_feasible_codetection_gap_negative"] is True

def test_every_synthetic_feasible_extreme_reconciles_27_cells_12_taxa_and_11_alien_bearing_plots():
    a,b=fixture()
    r=calculate(a,b)
    all_possible=r["possible_synthetic_witnesses_not_observed_plot_values"]
    assert len(all_possible)==3
    for row in all_possible:
        f=row["synthetic_feasible_plot_richness_focal"]
        other=row["synthetic_feasible_plot_richness_nondetected"]
        assert len(f)==19 and len(other)==5
        assert sum(f)==15 and sum(other)==12
        assert sum(k>0 for k in f+other)==11
        assert max(f+other)==5
        assert sum(f+other)==27
        assert row["synthetic_feasibility_only_not_original_sites"]
        # Independently test that 12 unique taxa can be allocated across
        # the 27 incidence cells without repeating one taxon in one plot.
        found=set()
        global_index=0
        for k in f+other:
            ids={((global_index+j)%12) for j in range(k)}
            assert len(ids)==k
            found.update(ids)
            global_index+=k
        assert len(found)==12

def test_indigenous_species_co_detection_is_not_focal_self_counting():
    a,b=fixture()
    r=calculate(a,b)
    assert r["nonfocal_native_taxa_in_focal_detected_plots"]==246
    assert r["nonfocal_native_taxa_in_focal_nondetected_plots"]==20
    assert r["mean_nonfocal_native_taxa_per_focal_detected_plot"]["exact"]=="246/19"
    assert r["mean_nonfocal_native_taxa_per_focal_nondetected_plot"]["exact"]=="4"
    assert r["ratio_mean_nonfocal_native_richness_detected_vs_nondetected"]["exact"]=="123/38"
    assert r["no_original_biological_rows_reopened"]
    assert r["source_free_posthoc_accounting_not_confirmatory"]
    assert r["native_focal_plot_nondetection_not_species_absence"]
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]
    assert r["new_confirmatory_systems"]==0

def test_modified_historical_species_max_or_artifact_identity_must_stop():
    a,b=fixture()
    altered=deepcopy(a)
    altered["pico"]["maximum_distinct_introduced_taxa_per_original_plot"]=6
    with pytest.raises(ValueError,match="frozen prior-aggregate"):
        calculate(altered,b)
    altered=deepcopy(a)
    altered["source_sha256"]["v281_extracted"]="wrong"
    with pytest.raises(ValueError,match="fingerprint"):
        calculate(altered,b)
    altered=deepcopy(a)
    altered["pico"]["v282_total_native_mean_focal_positive_plot"]=12.0
    with pytest.raises(ValueError,match="focal-positive native"):
        calculate(altered,b)
