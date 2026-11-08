"""Known-truth source station height trajectories and forest-season fixed effects."""
import importlib.util
from pathlib import Path

p=Path(__file__).with_name("thai_beetle_timevarying_height_response.py")
spec=importlib.util.spec_from_file_location("thai_height_temporal",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture_rows(y_slope=0.05):
    out=[]
    for f in ("forest-1","forest-2"):
        for i in range(9):
            for phase in (0,1):
                h=13+i+(0.8 if phase and i%2==0 else 0)
                y=y_slope*h + (2 if f=="forest-2" else 0)+(1.5 if phase else 0)
                out.append({
                   "forest":f,"station":i,"campaign":phase,
                   "height_m":h,"log_canopy_over_understorey":y,
                   "canopy_individuals":5,"understorey_individuals":2
                })
    return out


def test_temporally_varying_height_not_average_and_exact_block_centering():
    rows=fixture_rows()
    assert len(rows)==36
    assert abs(m.centered_slope(rows,exact=True)-.5)<1e-12
    r=m.inference(rows,permutations=99,bootstraps=300)
    assert r["forest_campaign_centered_log_capture_ratio_slope_per10m"]>.49
    assert r["two_sided_site_trajectory_permutation_p_conditional_on_two_forests"]<=.05
    assert r["within_forest_station_trajectory_bootstrap_95CI_log_ratio_per10m"][0]>.49
    assert r["LOO_site_exclusions_retaining_same_slope_sign"]==18
    assert r["within_study_site_trajectory_permutations_preserve_both_seasons"]


def test_reverse_or_constant_association_does_not_automatically_generate_positive_effect():
    rows=fixture_rows(y_slope=-0.05)
    assert abs(m.centered_slope(rows,exact=True)+.5)<1e-12
    rows=fixture_rows(y_slope=0)
    assert abs(m.centered_slope(rows,exact=True))<1e-12


def test_missing_campaign_not_treated_as_new_station():
    rows=fixture_rows()
    missing=[q for q in rows if not (q["forest"]=="forest-2" and q["station"]==5 and q["campaign"]==1)]
    try:
        m.centered_slope(missing,exact=True)
        assert False
    except ValueError as e:
        assert "original_18_physical_stations_x_two_campaigns_required" in str(e)


def test_actual_slAM_field_shape_with_original_style_source_height_and_two_season_drift():
    fp=Path(__file__).with_name("test_thai_beetle_trap_height_association.py")
    sp=importlib.util.spec_from_file_location("original_height_test_fixture",fp)
    util=importlib.util.module_from_spec(sp)
    sp.loader.exec_module(util)
    events,occ=util.source_fixture()
    target=events[0]
    for e in events:
        if (e["locationID"]==target["locationID"] and
            e["decimalLatitude"]==target["decimalLatitude"] and
            e["decimalLongitude"]==target["decimalLongitude"] and
            e["eventDate"]=="2019-12-01" and "canopy" in e["samplingProtocol"]):
            e["dynamicProperties"]="trap height in meters:18"
    q=m.analyze(events,occ)
    assert q["original_independent_forest_n"]==2
    assert q["original_physical_station_n"]==18
    assert q["original_station_campaign_pairs"]==36
    assert q["original_beetle_individuals"]==1622
    assert q["all_original_stations_included_including_height_movers"]
    assert q["posthoc_exploratory_after_station_fixed_height_STOP"]
    assert q["not_test_of_thermal_refuge_or_climate_warming"]
    assert q["raw_coordinates_tree_station_event_ids_not_exported"]
    assert "SourceX" not in str(q)
