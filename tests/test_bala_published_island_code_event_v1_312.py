"""Synthetic 2024 BALA author abbreviated islands v1.312; taxon values sealed."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_published_island_code_event_v1_312 import recode_and_audit
def protocol():
    return json.loads((ROOT/"development/bala_published_island_code_event_protocol_v1_312.json").read_text())
def fixture():
    rows=[]
    for isl in ("flo","fai","pic","sjg","ter","smg","smr"):
        for site in range(3):
            for period,year in (("B1",2001),("B2",2011),("B3",2021)):
                for mode in ("Pitfall solution","Open beating tray (with bag)"):
                    code=f"{isl}-{site}-{period}-{mode}"
                    rows.append({"__original_coreid":code,"eventID":code,"year":str(year),
                        "eventDate":f"{year}-07-01","island":isl,
                        "locationID":f"{isl}-physical-transect{site}",
                        "samplingProtocol":mode,"fieldNumber":f"{site}"})
    for j in range(198):
        code=f"secondary-gra-{j}"
        rows.append({"__original_coreid":code,"eventID":code,"year":"2000",
            "eventDate":"2000-08-01","island":"gra","locationID":f"gra-site-{j}",
            "samplingProtocol":"Pitfall solution","fieldNumber":str(j)})
    while len(rows)<10379:
        j=len(rows)
        code=f"extra-ter-{j}"
        rows.append({"__original_coreid":code,"eventID":code,"year":"2001",
            "eventDate":"2001-07-02","island":"ter","locationID":"ter-physical-transect0",
            "samplingProtocol":"Pitfall solution","fieldNumber":str(j)})
    return rows
def test_published_island_short_codes_restore_original_phase_overlap_without_taxon_data():
    r=recode_and_audit(fixture(),protocol())
    assert r["status"]=="AUTHOR_CODE_CORRECTED_EVENT_REPEATS_QUALIFIED_OCCURRENCE_UNOPENED"
    assert r["same_physical_transect_all_three_phase_site_count"]==21
    assert r["same_physical_transect_paired_site_count_B1_B3"]==21
    assert r["island_count_with_B1_B3_repeated_transects"]==7
    assert r["source_graciosa_secondary_forest_Events_excluded"]==198
    assert r["original_v1_311_source_code_GATE_remains_TERMINAL"]
    assert r["all_matched_site_and_campaign_cutoffs_inherited_unchanged"]
    assert r["original_Occurrence_rows_opened"]==0
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]
    assert "physical-transect0" not in json.dumps(r)
def test_wrong_source_island_codes_do_not_make_new_species_result():
    rows=fixture()
    for record in rows:
        if record["island"]=="flo":
            record["island"]="unknown_source"
    r=recode_and_audit(rows,protocol())
    assert r["status"]=="AUTHOR_CODE_CORRECTED_SITE_OVERLAP_INSUFFICIENT_STOP"
    assert r["original_Occurrence_rows_opened"]==0
    assert r["original_v1_311_source_code_GATE_remains_TERMINAL"]
