"""Original 562 Madeira/Porto Santo spider Event-only plot/time forensics."""
import json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from madeira_spider_original_event_code_diagnostic_v1_343 import diagnose,codes,nonbiological_time_class

def contract():
    return json.loads((ROOT/"development/madeira_spider_original_event_identity_diagnostic_protocol_v1_343.json").read_text())

def fake(with_codes=True,with_time=True):
    rows=[]
    plots=[f"MF{i}" for i in range(1,13)]+[f"MD{i}" for i in range(1,6)]+[f"PSD{i}" for i in range(1,6)]
    for i,code in enumerate(plots):
        for j in range(4):
            rows.append({
               "__source_coreid":f"COBRA_{code}_sweep{j}",
               "eventID":f"COBRA_{code}_sweep{j}" if with_codes else f"event_{i}_{j}",
               "fieldNumber":f"{code} swept" if with_codes else "no plot ID",
               "locationID":"region1",
               "locationRemarks":"",
               "habitat":"native forest" if i<12 else "dry open habitat",
               "samplingProtocol":"sweeping",
               "eventTime":("Day" if j<2 else "Night") if with_time else "",
               "sampleSizeValue":"1",
               "sampleSizeUnit":"hour",
               "samplingEffort":"1 hour",
               "eventDate":"2016-08-15" if i<12 else "2017-04-20"
            })
    for k in range(474):
        i=k%22;code=plots[i]
        rows.append({
            "__source_coreid":f"extra_{k}",
            "eventID":f"other_{k}" if not with_codes else f"OTHER-{code}-{k}",
            "fieldNumber":code if with_codes else "",
            "locationID":"region1","locationRemarks":"",
            "habitat":"native forest" if i<12 else "dry open habitat",
            "samplingProtocol":"pitfall","eventTime":"",
            "sampleSizeValue":"1","sampleSizeUnit":"trap",
            "samplingEffort":"","eventDate":"2016-08-15" if i<12 else "2017-04-20"
        })
    assert len(rows)==562
    return rows

def test_published_MF_MD_PSD_code_and_daynight_extra_metadata_are_detectable():
    r=diagnose(fake(),contract())
    assert r["status"]=="SOURCE_EVENT_DESIGN_POTENTIAL_ALTERNATE_CROSSWALK_DIAGNOSTIC_ONLY"
    assert r["published_plot_source_code_candidate_counts"]=={
      "published_MF_plot_n":12,"published_MD_plot_n":5,"published_PSD_plot_n":5}
    assert r["source_sweeping_author_time_counts"]=={"DAY":44,"NIGHT":44}
    assert r["original_Occurrence_rows_inspected"]==0
    assert r["previous_v342_strict_source_gate_TERMINAL"]
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]
    assert "COBRA_MF" not in json.dumps(r)

def test_published_codes_absent_means_stop_regardless_of_source_taxa():
    r=diagnose(fake(with_codes=False),contract())
    assert r["status"]=="TERMINAL_NO_AUTHOR_PLOT_AND_DIURNAL_SWEEP_FIELD_CROSSWALK"
    assert r["plot_codes_uniquely_assigned_event_n"]==0
    assert r["original_Occurrence_rows_inspected"]==0

def test_method_daynight_missing_means_no_common_equal_effort_assumption():
    r=diagnose(fake(with_time=False),contract())
    assert r["status"]=="TERMINAL_NO_AUTHOR_PLOT_AND_DIURNAL_SWEEP_FIELD_CROSSWALK"
    assert r["source_sweeping_author_time_counts"]=={"UNSPECIFIED":88}
    assert r["previous_v342_strict_source_gate_TERMINAL"]

def test_author_plot_code_does_not_fuzzily_misparse_and_prior_stop_immutable():
    assert codes("MF-03, day sweeping")=={"MF3"}
    assert codes("MD5")=={"MD5"}
    assert codes("PSD5")=={"PSD5"}
    assert codes("MF13")==set()
    assert codes("sweeMF2ping")==set()
    assert codes("MF1 and MD2")=={"MF1","MD2"}
    assert nonbiological_time_class({"eventTime":"Night","samplingProtocol":"sweeping"})=="NIGHT"
    assert nonbiological_time_class({"eventTime":"Day","samplingProtocol":"sweeping"})=="DAY"
    assert nonbiological_time_class({"eventTime":"Night Day","samplingProtocol":"sweeping"})=="AMBIGUOUS"
    with pytest.raises(ValueError,match="562"):
        diagnose(fake()[:-1],contract())
