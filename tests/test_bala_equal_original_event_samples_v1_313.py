"""Source-blind BALA repeated Event effort equalization test v1.313."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_equal_original_event_samples_v1_313 import select

def fixture():
    rows=[]
    methods=["Pitfall solution","Open beating tray (with bag)"]
    islands=("flo","fai","pic","sjg","ter","smg","smr")
    for island in islands:
        n=5 if island=="ter" else 4
        for s in range(n):
            for p,year in enumerate((2001,2011,2021)):
                for m in methods:
                    for k in range(2+p):
                        code=f"{island}.{s}.{year}.{m}.{k}"
                        rows.append({"__original_coreid":code,"eventID":code,
                           "year":str(year),"eventDate":str(year)+"-07-01",
                           "locationID":f"site-{s}","island":island,
                           "samplingProtocol":m})
    return rows
def test_all_29_core_sites_58_source_methods_have_equal_sampling_effort():
    d=select(fixture())
    assert d["status"]=="SOURCE_EQUAL_EFFORT_FROZEN_EVENT_ONLY_OCCURRENCE_SEALED"
    assert d["all_three_period_original_sites"]==29
    assert d["site_method_comparable_counts"]==58
    assert d["per_site_method_common_min_sample_Event_count_range"]==[2,2]
    assert d["selected_original_Event_per_campaign"]=={"B1":116,"B2":116,"B3":116}
    assert d["selected_original_Event_row_count_all_3_campaigns"]==348
    assert d["selected_original_Event_by_sampling_method"]["Pitfall solution"]["B2"]==58
    assert d["original_Occurrence_rows_opened"]==0
    assert d["selected_original_author_eventIDs_exported"] is False
    assert d["GEB_scientific_HOLD"] and not d["eBird_used"]
    assert "site-0" not in json.dumps(d)
def test_missing_any_one_site_method_campaign_is_scientific_stop_not_method_imputation():
    rows=[x for x in fixture() if not (
       x["island"]=="flo" and x["locationID"]=="site-0"
       and x["year"]=="2021" and x["samplingProtocol"]=="Pitfall solution")]
    d=select(rows)
    assert d["status"]=="STOP_SAMPLING_METHOD_OR_SITE_SUPPORT_UNESTIMABLE"
    assert d["site_method_comparable_counts"]==57
    assert d["missing_any_period_source_site_method_cells"]==1
    assert d["original_Occurrence_rows_opened"]==0
