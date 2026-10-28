"""Response-blind v1.307 site selection with exact original-method effort."""
import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from biomoni_spider_eight_site_event_v1_307 import qualify,date_year

def contract():
    return json.loads((ROOT/"development/biomoni_spider_eight_site_source_gate_v1_307.json").read_text())

def build():
    tree=[];spider=[]
    methods=[("M1",2),("M2",3),("M3",3),("M4",4),("M5",11)]
    for k in range(10):
        key=f"TER_NFBF_T{k+1:02}"
        lat=38.7+k/1000;lon=-27.2-k/1000
        tree.append({"source_coreid":f"tree{k}","island":"Terceira",
           "locationID":key,"decimalLatitude":str(lat),"decimalLongitude":str(lon),
           "eventDate":"2012-05-01" if k==0 else "2013-06-01",
           "year":"2012" if k==0 else "2013","samplingProtocol":"woody"})
        seq=0
        for j,(mode,n) in enumerate(methods):
            amount=n+(3 if j==k%5 else 0)
            for q in range(amount):
                bad=((k==6 and seq==0) or k==7)
                offset=0.01144 if k==6 and seq==0 else (0.000803 if k==7 else 0.0001)
                spider.append({"source_coreid":f"spider{k}-{mode}-{q}",
                  "island":"Terceira","locationID":key.replace("_","-"),
                  "decimalLatitude":str(lat+offset),
                  "decimalLongitude":str(lon),
                  "eventDate":"3/7/2012" if len(spider)<145 else "2012-07-03",
                  "year":"2012","samplingProtocol":mode})
                seq+=1
    for j in range(20):
        tree.append({"source_coreid":f"treeOther{j}","island":"Tenerife",
         "locationID":f"OTHER{j}","eventDate":"2013-01-01","year":"2013",
         "decimalLatitude":"28.0","decimalLongitude":"-16.0","samplingProtocol":"woody"})
    for j in range(163):
        spider.append({"source_coreid":f"spiderPico{j}","island":"Pico",
           "locationID":"PICO","eventDate":"2016-07-01","year":"2016",
           "decimalLatitude":"38.4","decimalLongitude":"-28.2","samplingProtocol":"PIT"})
    assert len(tree)==30 and len(spider)==423
    return tree,spider

def test_strict_eight_spatially_valid_sites_and_184_equal_mode_events():
    t,s=build()
    r=qualify(t,s,contract())
    assert r["status"]=="NEW_EXPLORATORY_EIGHT_PHYSICAL_PLOTS_EQUAL_SPIDER_METHODS_RESPONSE_SEALED"
    assert r["nominal_Terceira_site_IDs_shared"]==10
    assert r["spatially_matched_within_0_0003deg_sites"]==8
    assert r["spatially_excluded_site_count"]==2
    assert r["source_site_coordinates_outside_frozen_limit_event_count"]==27
    assert r["spider_common_original_method_count"]==5
    assert r["spider_shared_method_min_multiplicities_sorted"]==[2,3,3,4,11]
    assert r["selected_original_spider_Events_each_eligible_site"]==23
    assert r["selected_original_spider_Events_total"]==184
    assert r["old_v1_303_and_304_full_ten_plot_gate_TERMINAL"]
    assert r["original_spider_Occurrence_rows_opened"]==0
    assert r["original_woody_Occurrence_rows_reopened"]==0
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0
    assert not r["eBird_used"]
    assert "TER_NFBF" not in json.dumps(r)

def test_wrong_calendar_annotation_does_not_relabel_after_exposure():
    t,s=build();s[0]["eventDate"]="2014-05-01"
    with pytest.raises(ValueError,match="date"):
        qualify(t,s,contract())

def test_three_bad_sites_is_scientific_stop_without_species():
    t,s=build()
    s[30]["decimalLatitude"]="42.11"
    r=qualify(t,s,contract())
    assert r["status"]=="STOP_SPATIAL_QUALIFIED_EIGHT_PLOT_FRAME_NOT_FROZEN"
    assert r["original_spider_Occurrence_rows_opened"]==0
    assert r["old_303_GATE_TERMINAL"]

def test_formats_and_method_identity():
    assert date_year("2012-06-01")==2012
    assert date_year("01/07/2012")==2012
    assert date_year("July 2012") is None
