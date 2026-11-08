"""Known truth of 18-station seasonal canopy trap height drift source-only."""
import importlib.util
from pathlib import Path

p=Path(__file__).with_name("thai_beetle_canopy_height_repeatability.py")
spec=importlib.util.spec_from_file_location("thai_beetle_height_repeatability",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def source_fixture(changes=True):
    rows=[]
    for f in ("SECRET_FOREST_1","SECRET_FOREST_2"):
        for i in range(9):
            lat=11.0+(1 if f.endswith("2") else 0)+.003*(i//3)
            lon=100.0+.003*(i%3)
            for phase,date in enumerate(("2019-06-01","2019-12-01")):
                for layer in ("canopy","understory"):
                    h=2 if layer=="understory" else 13+i
                    if changes and layer=="canopy" and i==0 and phase==1:h+=5
                    for jar in ("top","bottom"):
                        rows.append({
                            "locationID":f,"eventDate":date,
                            "samplingProtocol":f"SLAM Trap ({layer} {jar} jar)",
                            "decimalLatitude":str(lat+(.0001 if layer=="canopy" else 0)),
                            "decimalLongitude":str(lon),
                            "dynamicProperties":"trap height in meters:"+str(h),
                            "eventRemarks":"","locationRemarks":""
                        })
                    for protocol in ("light trap","fit with yellow pan"):
                        rows.append({
                            "locationID":f,"eventDate":date,
                            "samplingProtocol":f"{protocol} ({layer})",
                            "decimalLatitude":str(lat),
                            "decimalLongitude":str(lon),
                            "dynamicProperties":"","eventRemarks":"","locationRemarks":""
                        })
    assert len(rows)==288
    return rows


def test_publisher_event_height_drift_gt4_blocks_station_fixed_model():
    q=m.audit(source_fixture())
    assert q["original_Event_rows"]==288
    assert q["SLAM_jar_Event_rows"]==144
    assert q["physical_canopy_station_n"]==18
    assert q["sites_canopy_trap_height_change_gt4m"]==2
    assert q["max_absolute_canopy_height_shift_per_station_m"]==5
    assert not q["constant_canopy_height_per_station_site_level_model_eligible"]
    assert not q["no_thermal_movement_or_causal_effect_scored"] is False
    assert q["original_beetle_Occurrence_extension_rows_read"]==0
    assert "SECRET_FOREST" not in str(q)


def test_stable_height_source_allows_station_level_later_fit():
    q=m.audit(source_fixture(changes=False))
    assert q["sites_canopy_trap_height_change_gt4m"]==0
    assert q["constant_canopy_height_per_station_site_level_model_eligible"]
    assert q["max_absolute_canopy_height_shift_per_station_m"]==0


def test_incomplete_replicate_without_jar_does_not_become_valid_station():
    e=source_fixture()
    e.pop(0)
    try:
        m.audit(e)
        assert False
    except ValueError as exc:
        assert "original_Event_total_drift" in str(exc)
