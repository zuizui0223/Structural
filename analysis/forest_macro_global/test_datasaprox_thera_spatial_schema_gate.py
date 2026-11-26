"""Response-unopened THERA source plot spatial support and four-trap effort tests."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import datasaprox_thera_spatial_schema_gate as a

def source(nplot=3,nmonth=2):
    events={};extra={};xy={}
    for pi in range(nplot):
        for mi in range(nmonth):
            for lev in ("upper","lower"):
                for rep in range(2):
                    event="event"+str(pi)+str(mi)+lev+str(rep)
                    k=("EFNO","THERA",event)
                    events[k]=(lev,f"SECRET_PLOT_{pi}","lindgren","funnel",
                               "Lind noir Supra canopee" if lev=="upper"
                               else "Lind noir Infra canopee",
                               "control","black",f"2024-{mi+5:02d}",14.)
                    extra[k]={("", "",lev+str(rep))}
                    xy[k]=(44.0,1+0.001*pi)
    return events,extra,xy

def test_balanced_all_four_trap_support_and_site_dependence():
    events,extra,xy=source()
    cohort=a.balanced_source_plots(events,set(),extra)
    assert len(cohort)==6
    assert len({v[0] for v in cohort})==3
    r=a.study_spatial_qc(cohort,xy,set())
    assert r["source_balanced_four_trap_plot_month_units"]==6
    assert r["source_distinct_balanced_original_field_plot_keys"]==3
    assert r["source_balanced_original_plot_keys_with_coordinate_evidence"]==3
    assert r["source_plot_center_connected_components_at_0p5_1_5_20_km"]["0.5"]==1
    assert r["source_coordinates_alone_do_not_certify_independent_forests"]
    assert "SECRET_PLOT" not in str(r)
    assert "event00upper0" not in str(r)  # require actual ID absence, not a generic key fragment

def test_nonidentical_four_trap_effort_stops_that_period_before_taxon_read():
    events,extra,xy=source(1,1)
    key=("EFNO","THERA","event00upper0")
    v=list(events[key]);v[-1]=30.;events[key]=tuple(v)
    # 30-14 > 7-day; even if 3 other trap durations look balanced
    assert a.balanced_source_plots(events,set(),extra)=={}

def test_unreconciled_coordinate_events_do_not_certify_physical_plot():
    events,extra,xy=source(3,1)
    cohort=a.balanced_source_plots(events,set(),extra)
    invalid={("EFNO","THERA","event10upper0")}
    r=a.study_spatial_qc(cohort,xy,invalid)
    assert r["source_balanced_original_plot_keys_with_conflicting_event_coordinates"]==1
    assert r["source_balanced_original_plot_keys_with_coordinate_evidence"]==2
    assert r["source_original_response_taxon_values_read"] is False
    assert r["source_locations_and_original_site_ids_NOT_EXPORTED"] is True

def test_missing_event_coordinate_cannot_be_interpolated():
    events,extra,xy=source(2,1)
    cohort=a.balanced_source_plots(events,set(),extra)
    xy.pop(("EFNO","THERA","event10upper0"))
    r=a.study_spatial_qc(cohort,xy,set())
    assert r["source_balanced_original_plot_keys_with_missing_event_coordinates"]==1
