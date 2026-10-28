"""Source-opaque spider Event date and physical site postmortem v1.305."""
from pathlib import Path
import sys,json,copy
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from biomoni_spider_terceira_event_postmortem_v1_305 import inspect_original_events

def make_fixture():
    trees=[];spiders=[]
    for k in range(10):
        site=f"TER_NFBF_T{k+1:02}"
        trees.append({"source_coreid":f"w_{k}","island":"Terceira",
           "locationID":site,"decimalLatitude":str(38.7+k/1000),
           "decimalLongitude":str(-27.2-k/1000),"year":"2013",
           "eventDate":"2013-05-01","samplingProtocol":"woody"})
        for method in ("PIT","FSN","FSD"):
            for j in range(8):
                spiders.append({"source_coreid":f"s_{k}_{method}_{j}","island":"Terceira",
                   "locationID":site.replace("_","-"),"decimalLatitude":str(38.7+k/1000+0.0001),
                   "decimalLongitude":str(-27.2-k/1000-0.0001),"year":"2014",
                   "eventDate":"2014-06-03","samplingProtocol":method})
    for k in range(20):
        trees.append({"source_coreid":f"wo_other_{k}","island":"Tenerife",
          "locationID":f"TEN_{k}","decimalLatitude":"28","decimalLongitude":"-16",
          "year":"2013","eventDate":"2013-06-01","samplingProtocol":"woody"})
    for k in range(183):
        spiders.append({"source_coreid":f"sp_other_{k}","island":"Pico",
          "locationID":"PICO_TEST","decimalLatitude":"38.4",
          "decimalLongitude":"-28.2","year":"2016","eventDate":"2016-07-01",
          "samplingProtocol":"PIT"})
    assert len(trees)==30 and len(spiders)==423
    return {"woody":trees,"spider":spiders}

def test_event_only_diagnoses_2014_out_of_strict_original_years():
    d=inspect_original_events(make_fixture())
    assert d["status"]=="ORIGINAL_EVENT_ONLY_POSTGATE_DIAGNOSTIC_303_REMAINS_TERMINAL"
    assert d["Terceira_exact_10_tree_and_spider_plots_supported"]
    assert d["Terceira_exact_original_site_overlap_count"]==10
    assert d["source_meta"]["spider"]["source_island_year_Event_counts"]["terceira"]=={"2014":240}
    assert d["Terceira_minimum_nearest_observation_year_gap"]==1
    assert d["Terceira_maximum_nearest_observation_year_gap"]==1
    assert d["Terceira_shared_spider_protocol_modes_count"]==3
    assert d["Terceira_spider_original_Events_per_matched_plot_min_max"]==[24,24]
    assert d["original_spider_Occurrence_rows_opened"]==0
    assert d["old_v1_303_year_gate_status"]=="TERMINAL"
    assert d["new_confirmatory_systems"]==0 and d["GEB_scientific_HOLD"]
    assert not d["eBird_used"]
    assert "TER_NFBF" not in json.dumps(d)
    assert "s_0_" not in json.dumps(d)

def test_site_key_mismatch_does_not_rescue_via_coordinates():
    d=make_fixture()
    for x in d["spider"]:
        if x["locationID"]=="TER-NFBF-T01":
            x["locationID"]="TER-UNMATCHED-ONE"
    v=inspect_original_events(d)
    assert v["Terceira_exact_original_site_overlap_count"]==9
    assert not v["Terceira_exact_10_tree_and_spider_plots_supported"]
    assert v["Terceira_site_mismatch_counts"]=={
       "Terceira_tree_sites_unmatched":1,
       "Terceira_spider_sites_unmatched":1
    }
    assert v["original_spider_Occurrence_rows_opened"]==0

def test_duplicate_original_event_id_stops():
    d=make_fixture()
    d["spider"][1]["source_coreid"]=d["spider"][0]["source_coreid"]
    with pytest.raises(ValueError,match="duplicate"):
        inspect_original_events(d)

def test_year_column_mismatch_counted_not_silently_corrected():
    d=make_fixture()
    d["spider"][0]["year"]="2012"
    receipt=inspect_original_events(d)
    assert receipt["source_meta"]["spider"]["original_year_column_date_disagreement_events"]==1
    assert receipt["source_meta"]["spider"]["source_island_year_Event_counts"]["terceira"]=={"2014":240}
