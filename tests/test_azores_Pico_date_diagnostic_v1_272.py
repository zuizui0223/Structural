"""Pico source-only field-event date semantic diagnostics; no species values."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_Pico_date_diagnostic_v1_272 import date_kind, event_date_diagnostic


def test_date_categories_do_not_invent_day_from_year_or_ranges():
    assert date_kind("2020-07-01")=="full_day"
    assert date_kind("2020-07-01T13:05:00")=="day_and_time"
    assert date_kind("2020-07-01/2020-07-03")=="interval"
    assert date_kind("2020-07")=="month_only"
    assert date_kind("2020")=="year_only"
    assert date_kind("2020-XX-XX")=="other"
    assert date_kind("")=="missing"


def test_source_components_and_published_dates_have_conflicts_not_midpoint():
    rows=[
       {"eventDate":"2019-05-06","year":"2019","month":"5","day":"6","scientificName":"DO_NOT_TOUCH_SPECIES"},
       {"eventDate":"2020-06-02T12:00:00","year":"2020","month":"6","day":"2"},
       {"eventDate":"2021-07-01/2021-07-03","year":"2021","month":"7","day":""},
       {"eventDate":"2018-01-01","year":"2018","month":"1","day":"2"},
       {"eventDate":"2020","year":"2020","month":"","day":""},
    ]
    a=event_date_diagnostic(rows)
    assert a["event_rows"]==5
    assert a["full_date_eventDate_rows"]==3
    assert a["component_complete_and_valid_dates"]==3
    assert a["source_field_date_component_conflicts"]==1
    assert a["event_date_classes"]["interval"]==1
    assert a["event_date_classes"]["year_only"]==1
    assert a["reliable_full_day_rows"]==2
    assert "DO_NOT_TOUCH" not in str(a)


def test_source_invalid_date_components_never_counted_as_full_days():
    rows=[{"eventDate":"2020-06/2020-07","year":"2020","month":"6","day":"0"},
          {"eventDate":"2019-13-03","year":"2019","month":"13","day":"3"}]
    a=event_date_diagnostic(rows)
    assert a["reliable_full_day_rows"]==0
    assert a["component_complete_and_valid_dates"]==0


def test_slash_numeric_field_date_disambiguates_against_author_year_month_day():
    from azores_Pico_date_diagnostic_v1_272 import slash_date_matches_author_components
    assert date_kind("8/11/2020")=="slash_numeric_day"
    assert date_kind("2020-08-11/2020-08-15")=="interval"
    assert slash_date_matches_author_components("8/11/2020",{"year":"2020","month":"8","day":"11"})=="MDY"
    assert slash_date_matches_author_components("8/11/2020",{"year":"2020","month":"11","day":"8"})=="DMY"
    assert slash_date_matches_author_components("8/8/2020",{"year":"2020","month":"8","day":"8"})=="BOTH_SAME_DAY"
    assert slash_date_matches_author_components("8/11/2020",{"year":"2020","month":"3","day":"4"})=="CONFLICT"
    assert slash_date_matches_author_components("8/11/2020",{"year":"2020","month":"8","day":""})=="NO_VALID_COMPONENTS"


def test_slash_numeric_records_are_recovered_only_with_matching_original_components():
    records=[
      {"eventDate":"8/11/2020","year":"2020","month":"8","day":"11"},
      {"eventDate":"8/12/2020","year":"2020","month":"8","day":"12"},
      {"eventDate":"11/8/2020","year":"2020","month":"8","day":"11"},
      {"eventDate":"8/8/2020","year":"2020","month":"8","day":"8"},
      {"eventDate":"8/11/2020","year":"2020","month":"3","day":"4"},
      {"eventDate":"2020-06-01/2020-07-01","year":"2020","month":"6","day":"1"}
    ]
    result=event_date_diagnostic(records)
    assert result["event_date_classes"]["slash_numeric_day"]==5
    assert result["event_date_classes"]["interval"]==1
    assert result["slash_MDY_source_component_match"]==2
    assert result["slash_DMY_source_component_match"]==1
    assert result["slash_both_same_day"]==1
    assert result["slash_component_conflicts"]==1
    assert result["reliable_full_day_rows"]==4
