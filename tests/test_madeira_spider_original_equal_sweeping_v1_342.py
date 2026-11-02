"""v1.342 Madeira COBRA spider exact common day/night sweeping Event-only controls."""
import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from madeira_spider_original_equal_sweeping_v1_342 import audit,sweep,habitat

def cfg():
    return json.loads((ROOT/"development/madeira_spider_original_equal_sweeping_event_protocol_v1_342.json").read_text())

def synth():
    rows=[]
    for i in range(22):
        if i<12:isl="Madeira";typ="native forest";year=2016
        elif i<17:isl="Madeira";typ="dry habitat";year=2017
        else:isl="Porto Santo";typ="dry habitat";year=2017
        source_id=f"AUTHOR_PLOT_{isl.replace(' ','')}_{i:02}"
        base={
           "island":isl,"locationID":source_id,"habitat":typ,
           "eventDate":f"{year}-08-15" if year==2016 else f"{year}-04-15",
           "year":str(year),"decimalLatitude":str(32.7+i*.003),
           "decimalLongitude":str(-17.1+i*.003),
           "sampleSizeValue":"1","sampleSizeUnit":"hour"
        }
        for m in ("Day sweeping","Night sweeping"):
            for j in range(2):
                rows.append({**base,"__source_coreid":f"sample_{i:02}_{m[:3]}_{j}",
                            "samplingProtocol":m,"samplingEffort":"1 hour"})
        for j in range(21):
            rows.append({**base,"__source_coreid":f"other_{i:02}_{j}",
                         "samplingProtocol":"Beating","sampleSizeValue":"",
                         "sampleSizeUnit":"","samplingEffort":""})
    # 22*(4+21)=550 source Events, plus 12 more noncommon original
    # ground or beating samples do not affect 88 source target.
    for i in range(12):
        r=copy.deepcopy(rows[i*25])
        r["__source_coreid"]=f"extra_{i}"
        r["samplingProtocol"]="Beating"
        rows.append(r)
    assert len(rows)==562
    return rows

def test_original_common_forest_dry_source_selection_from_22_plot_fixture():
    z=audit(synth(),cfg())
    assert z["status"]=="MADEIRA_22_PLOT_88_EQUAL_SWEEP_EVENTS_SOURCE_LOCKED_TAXA_SEALED"
    assert z["original_physical_source_sites"]==22
    assert z["original_physical_sites_by_island_habitat"]=={
        "Madeira_forest":12,"Madeira_dry":5,"Porto_Santo_dry":5}
    assert z["source_selected_22_plot_sweeps_original_Event_n"]==88
    assert len(z["selected_88_original_Event_coreid_SHA256"])==64
    assert not z["source_Event_quality_problem_counts"]
    assert not z["source_physical_site_conflict_counts"]
    assert z["original_Occurrence_rows_opened"]==0
    assert z["forest_2016_dry_2017_temporal_confound_unresolved"]
    assert z["new_confirmatory_systems"]==0 and z["GEB_scientific_HOLD"] and not z["eBird_used"]
    assert "AUTHOR_PLOT" not in json.dumps(z)

def test_two_method_common_effort_missing_in_one_dry_plot_is_scientific_stop():
    rows=synth()
    for r in rows:
        if r["locationID"].endswith("_12") and r["samplingProtocol"]=="Night sweeping":
            r["samplingProtocol"]="Beating"
    v=audit(rows,cfg())
    assert v["status"]=="TERMINAL_MADEIRA_NATURAL_HABITAT_SWEEP_SOURCE_NOT_COMPARABLE"
    assert v["original_Occurrence_rows_opened"]==0
    assert v["source_physical_site_conflict_counts"]["source_plot_insufficient_common_NIGHT_SWEEP"]==1

def test_source_sweep_duration_and_coordinates_fail_closed():
    rows=synth()
    rows[0]["sampleSizeValue"]="2"
    result=audit(rows,cfg())
    assert result["status"]=="TERMINAL_MADEIRA_NATURAL_HABITAT_SWEEP_SOURCE_NOT_COMPARABLE"
    assert result["source_Event_quality_problem_counts"]["sweep_original_duration_different_from_one_hour"]==1
    rows=synth();rows[1]["decimalLatitude"]="30"
    result=audit(rows,cfg())
    assert result["status"]=="TERMINAL_MADEIRA_NATURAL_HABITAT_SWEEP_SOURCE_NOT_COMPARABLE"
    assert result["source_physical_site_conflict_counts"]["within_site_original_coordinates_conflict"]==1

def test_original_forest_is_not_exotic_and_dry_is_not_altered_forest():
    c=cfg()
    assert habitat("native forest",c)=="forest"
    assert habitat("dry habitat",c)=="dry"
    assert habitat("exotic forest",c) is None
    assert sweep("DS",c)=="DAY_SWEEP"
    assert sweep("Night sweeping",c)=="NIGHT_SWEEP"
    assert sweep("Pitfall",c)=="OTHER"

def test_source_raw_562_Event_requirement():
    with pytest.raises(ValueError,match="562"):
        audit(synth()[:-1],cfg())
