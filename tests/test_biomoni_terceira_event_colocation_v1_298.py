"""Synthetic Terceira paired BioMonI beetle×tree Event-only plot/effort gates."""
import copy,json,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from biomoni_terceira_event_colocation_v1_298 import normalized_site, qualify

def contract():
    return json.loads((ROOT/"development/biomoni_terceira_colocated_event_gate_v1_298.json").read_text(encoding="utf-8"))

def fixtures():
    tree=[];beetle=[]
    for n in range(10):
        tsite=f"TER_NFBF_T{n+1:02}"
        bsite=f"TER-NFBF-T-{n+1:02}"
        lat=38.7+n/1000
        lon=-27.2-n/1000
        tree.append({"source_coreid":f"tree-ter-{n}","island":"Terceira",
            "locationID":tsite,"decimalLatitude":str(lat),
            "decimalLongitude":str(lon),"eventDate":"2013-06-01",
            "year":"2013","samplingProtocol":"woody dbh 1cm"})
        for mode in ("AAS","FSD","FSN","PIT","GWS"):
            for rep in range(4):
                beetle.append({"source_coreid":f"b-ter-{n}-{mode}-{rep}",
                   "island":"Terceira","locationID":bsite,
                   "decimalLatitude":str(lat+0.0001),
                   "decimalLongitude":str(lon-0.0001),"eventDate":"2012-07-01",
                   "year":"2012","samplingProtocol":mode})
    for n in range(10):
        tree.append({"source_coreid":f"tree-ten-{n}","island":"Tenerife",
            "locationID":f"TEN_{n}","decimalLatitude":"28.5",
            "decimalLongitude":"-16.3","eventDate":"2013-01-01","year":"2013",
            "samplingProtocol":"woody dbh 1cm"})
        tree.append({"source_coreid":f"tree-reu-{n}","island":"Réunion",
            "locationID":f"REU_{n}","decimalLatitude":"-21.1",
            "decimalLongitude":"55.7","eventDate":"2013-01-01","year":"2013",
            "samplingProtocol":"woody dbh 1cm"})
    for n in range(108):
        beetle.append({"source_coreid":f"b-pic-{n}","island":"Pico",
           "locationID":f"PIC_{n%6}","decimalLatitude":"38.4",
           "decimalLongitude":"-28.2","eventDate":"2016-07-01",
           "year":"2016","samplingProtocol":"PIT"})
    return tree,beetle

def test_normalization_is_punctuation_only_and_author_id_colocation():
    assert normalized_site("TER-NFBF-T-01")==normalized_site("TER_NFBF_T01")
    assert normalized_site("TER-NFBF-T-18")!=normalized_site("TER_NFBF_T01")
    t,b=fixtures()
    r=qualify(t,b,contract())
    assert r["status"]=="EXACT_TEN_COLOCATED_PLOTS_METHODS_COMPARABLE_RESPONSES_SEALED"
    assert r["original_woody_Event_rows_examined"]==30
    assert r["original_beetle_Event_rows_examined"]==308
    assert r["unique_tree_Terceira_sites"]==10 and r["unique_beetle_Terceira_sites"]==10
    assert r["exact_author_plot_bijection"] and r["paired_coordinate_difference_below_0_0003_deg"]
    assert r["beetle_sampling_modes_common_to_all_plots"]==5
    assert r["minimum_beetle_sample_events_per_plot"]==20
    assert r["maximum_beetle_sample_events_per_plot"]==20
    assert r["Original_tree_Occurrence_rows_opened"]==0
    assert r["Original_beetle_Occurrence_rows_opened"]==0
    assert r["independent_physical_plots"]==10
    assert r["independent_geographies"]==1
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]
    assert "TERNFBFT01" not in json.dumps(r)
    assert "b-ter-" not in json.dumps(r)

def test_one_author_site_name_mismatch_is_hard_stop_even_when_coordinates_match():
    t,b=fixtures()
    b[0]["locationID"]="TER-NFBF-OTHER"
    with pytest.raises(ValueError,match="plot keys"):
        qualify(t,b,contract())

def test_coordinate_disagreement_at_same_nominal_site_yields_terminal_stop():
    t,b=fixtures()
    b[0]["decimalLatitude"]="38.9000"
    r=qualify(t,b,contract())
    assert r["status"]=="TERMINAL_COORDINATES_DATES_OR_METHOD_EFFORT_NOT_COMPARABLE"
    assert not r["paired_coordinate_difference_below_0_0003_deg"]
    assert not r["source_only_qualified_to_freeze_new_response_scoring"]

def test_common_methods_insufficient_is_terminal_before_any_beetle_labels():
    t,b=fixtures()
    for item in b:
        if item["source_coreid"].startswith("b-ter-0-"):
            item["samplingProtocol"]="uniform"
    r=qualify(t,b,contract())
    assert r["status"]=="TERMINAL_COORDINATES_DATES_OR_METHOD_EFFORT_NOT_COMPARABLE"
    assert not r["methods_effort_meet_source_only_gate"]
    assert r["Original_tree_Occurrence_rows_opened"]==0
    assert r["Original_beetle_Occurrence_rows_opened"]==0

def test_wrong_orig_event_denominator_or_duplicated_core_rejected():
    t,b=fixtures()
    with pytest.raises(ValueError,match="source size"):
        qualify(t,b[:-1],contract())
    b[1]["source_coreid"]=b[0]["source_coreid"]
    with pytest.raises(ValueError,match="duplicate"):
        qualify(t,b,contract())
