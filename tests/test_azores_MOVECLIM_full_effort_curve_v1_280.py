"""Regression for an aggregate-only sensitivity; do not reopen raw responses."""
import copy
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from azores_MOVECLIM_full_effort_curve_v1_280 import curve_from_freeze


def _source():
    path = ROOT / "development/azores_MOVECLIM_2013_native_plot_field_result_freeze_v1_278.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_full_effort_curve_and_frozen_primary():
    result = curve_from_freeze(_source())
    assert [x["equal_plots_m"] for x in result["curve"]] == list(range(1, 11))
    assert result["richness_dominance_m"] == list(range(1, 11))
    assert result["fraction_dominance_m"] == [1, 5, 6, 7, 8, 9, 10]
    assert result["fraction_not_certified_m"] == [2, 3, 4]
    assert result["curve"][9]["pico_min_focal_richness"]["exact"] == "8/3"
    assert result["curve"][9]["largest_other_max_focal_richness"]["exact"] == "1"
    assert result["no_raw_plant_or_event_rows_reopened"] is True
    assert result["confirmatory_systems_admitted"] == 0
    assert result["GEB_scientific_HOLD"] is True
    assert result["eBird_used"] is False


def test_original_plot_frame_tamper_rejected():
    modified = copy.deepcopy(_source())
    modified["by_island"]["Pico"]["plots"] += 1
    with pytest.raises(ValueError):
        curve_from_freeze(modified)


def test_original_field_source_hash_tamper_rejected():
    modified = copy.deepcopy(_source())
    modified["source"]["original_2013_SHA256"] = "changed"
    with pytest.raises(ValueError):
        curve_from_freeze(modified)
