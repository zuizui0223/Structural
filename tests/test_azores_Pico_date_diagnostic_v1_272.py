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
