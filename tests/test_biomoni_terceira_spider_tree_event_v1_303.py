"""Synthetic cross-taxon plot physical sites, spider Event-only matched effort."""
import sys,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from biomoni_terceira_spider_tree_event_v1_303 import evaluate
from test_biomoni_terceira_event_colocation_v1_298 import fixtures
def scenario():
    tree,_=fixtures()
    spider=[]
    for i in range(10):
        for mode in ("AAS","FSD","FSN","PIT"):
            for n in range(6):
                spider.append({"source_coreid":f"SPIDER-TER-{i}-{mode}-{n}",
                  "island":"Terceira","locationID":f"TER-NFBF-T-{i+1:02}",
                  "decimalLatitude":str(38.7+i/1000+0.0001),
                  "decimalLongitude":str(-27.2-i/1000-0.0001),
                  "eventDate":"2012-07-01","year":"2012",
                  "samplingProtocol":mode})
    for i in range(183):
        spider.append({"source_coreid":f"SPIDER-PICO-{i}",
          "island":"Pico","locationID":"PIC_1",
          "decimalLatitude":"38.4","decimalLongitude":"-28.2",
          "eventDate":"2016-07-01","year":"2016","samplingProtocol":"PIT"})
    assert len(spider)==423
    return tree,spider
def protocol():
    return json.loads((ROOT/"development/biomoni_terceira_spider_tree_event_protocol_v1_303.json").read_text())
def test_response_free_exact_source_10_sites_and_four_methods():
    w,s=scenario();r=evaluate(w,s,protocol())
    assert r["status"]=="TEN_SITE_SPIDER_TREE_EVENT_FRAME_QUALIFIED_RESPONSES_SEALED"
    assert r["selected_equal_mode_spider_Events_per_site"]==24
    assert r["selected_equal_mode_spider_Events_total"]==240
    assert r["common_spider_method_count"]==4
    assert r["max_year_offset"]==1
    assert r["original_spider_Occurrence_rows_opened"]==0
    assert r["original_woody_Occurrence_rows_reopened"]==0
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]
    assert "SPIDER-TER" not in json.dumps(r)
def test_one_misaligned_plot_is_terminal_without_response():
    w,s=scenario()
    for x in s:
        if x["locationID"]=="TER-NFBF-T-01":x["locationID"]="TER-OTHER-ID"
    r=evaluate(w,s,protocol())
    assert r["status"]=="STOP_ORIGINAL_TEN_PHYSICAL_SITE_BIJECTION_MISSING"
    assert r["original_spider_Occurrence_rows_opened"]==0
def test_spatially_different_plot_is_terminal():
    w,s=scenario()
    s[0]["decimalLatitude"]="39.99"
    r=evaluate(w,s,protocol())
    assert r["status"]=="TERMINAL_SITE_COORDINATE_OR_SPIDER_METHOD_EFFORT"
def test_method_incomplete_is_terminal():
    w,s=scenario()
    for x in s:
        if x["locationID"]=="TER-NFBF-T-01" and x["samplingProtocol"] in ("AAS","FSD"):
            x["samplingProtocol"]="plot-only-special"
    r=evaluate(w,s,protocol())
    assert r["status"]=="TERMINAL_SITE_COORDINATE_OR_SPIDER_METHOD_EFFORT"
