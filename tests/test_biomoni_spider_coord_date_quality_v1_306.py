"""Source-only v1.306 plot discrepancy/date-grammar regression (no taxa)."""
import json,sys,copy
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from biomoni_spider_coord_date_quality_v1_306 import audit,date_format
from test_biomoni_spider_terceira_event_postmortem_v1_305 import make_fixture

def test_plot_coordinate_error_is_detected_without_spider_taxon_names():
    sources=make_fixture()
    sources["spider"][0]["decimalLatitude"]="38.725"
    result=audit(sources)
    assert result["status"]=="SOURCE_ONLY_LOCATION_DATE_QUALITY_DIAGNOSTIC_V1_303_REMAINS_TERMINAL"
    assert result["original_exact_Terceira_shared_site_IDs"]==10
    assert result["original_Terceira_spider_Event_count"]==240
    assert result["number_Terceira_sites_failing_any_original_Event_coordinate_limit"]==1
    assert result["total_spider_Terceira_Event_coordinate_mismatches_over_0_0003"]==1
    assert result["total_spider_Terceira_Event_coordinate_mismatches_over_0_01"]==1
    assert result["old_v1_303_original_time_and_coordinate_gate_status"]=="TERMINAL"
    assert result["original_spider_Occurrence_rows_opened"]==0
    assert result["original_woody_Occurrence_rows_reopened"]==0
    assert result["GEB_scientific_HOLD"] and not result["eBird_used"]
    assert "TER_NFBF" not in json.dumps(result)
    assert "sp_other" not in json.dumps(result)
    assert "38.725" not in json.dumps(result)

def test_date_grammar_never_invents_a_calendar_year():
    assert date_format("2012-07-04")=="four_digit_year_prefix"
    assert date_format("05/07/2012")=="day_month_year"
    assert date_format("")=="empty"
    assert date_format("Unknown 2012")=="nonstandard"

def test_malformed_original_site_identity_refuses_to_rejoin_from_proximity():
    sources=make_fixture()
    sources["spider"][0]["locationID"]="UNSEEN ORIGINAL SITE"
    with pytest.raises(ValueError,match="crosswalk"):
        audit(sources)

def test_raw_frozen_event_row_grain_is_not_site_replication():
    res=audit(make_fixture())
    assert res["original_tree_Event_rows_examined"]==30
    assert res["original_spider_Event_rows_examined"]==423
    assert res["original_exact_Terceira_shared_site_IDs"]==10
    assert res["original_Terceira_spider_Event_count"]==240
    assert res["number_Terceira_sites_failing_any_original_Event_coordinate_limit"]==0
    assert res["original_spider_Occurrence_rows_opened"]==0
