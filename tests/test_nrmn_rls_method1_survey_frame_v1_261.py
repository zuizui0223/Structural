"""No fish biology is used: Method 1 survey event eligibility and source-locked candidate audit."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from nrmn_rls_method1_survey_frame_v1_261 import parse_method1, tally_method1

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=json.loads((ROOT/"development/nrmn_rls_method1_survey_frame_protocol_v1_261.json").read_text())

def survey(sid:int,site:str,year:int,month:int=7,method:str="1, 2",pg:str="RLS"):
    return {"survey_id":sid,"survey_date":f"{year}-{month:02d}-12",
            "country":"Australia","area":"Western Australia","location":"Rottnest Island",
            "site_code":site,"latitude":-32.0,"longitude":115.5,
            "depth":9.0,"program":pg,"methods":method}

def test_method_1_is_a_standalone_integer_token_not_12_or_13():
    assert parse_method1("1, 2")
    assert parse_method1("0,1,2")
    assert parse_method1("1, 13, 2")
    assert parse_method1("  2 ; 1 ")
    assert not parse_method1("2, 13")
    assert not parse_method1("12, 31")
    assert not parse_method1("")
    assert not parse_method1(None)

def test_strict_method1_site_annual_pairs_and_all_ten_candidate_reporting():
    rows=[];sid=1
    # Six previously sampled sites; five satisfy three consecutive years with two
    # Method1 transects, which yields 5 * 2 = 10 true site-year/month pairs.
    for s in ("R1","R2","R3","R4","R5"):
        for y in (2020,2021,2022):
            for _ in range(2):
                rows.append(survey(sid,s,y));sid+=1
    # Off-transect method 0 or other methods must never supply missing M1 effort.
    for y in (2020,2021,2022):
        for _ in range(2):
            rows.append(survey(sid,"R6",y,method="0, 2"));sid+=1
    for y in (2020,2021):
        for _ in range(2):
            rows.append(survey(sid,"R7",y,method="12, 13"));sid+=1
    result=tally_method1(rows,CONTRACT)
    assert result["source_rows_seen"]==40
    assert result["method1_unique_events_by_program"]["RLS"]==30
    assert result["all_methods_unique_events_by_program"]["RLS"]==40
    assert result["RLS_method1_strict_site_year_month_pairs"]==10
    assert result["method1_qualified_primary_RLS_geographic_groups"]==1
    assert len(result["frozen_RLS_candidate_physical_gate"])==10
    rott=[x for x in result["frozen_RLS_candidate_physical_gate"]
            if x["location"]=="rottnest island"][0]
    assert rott["method1_survey_events"]==30
    assert rott["method1_stable_sites"]==5
    assert rott["method1_sites_3plus_observed_years"]==5
    assert rott["method1_strict_site_month_year_pairs"]==10
    assert rott["method1_distinct_prior_years"]==2
    assert rott["method1_physically_qualified"] is True
    assert rott["original_all_methods_strict_pairs"]==105
    assert result["biological_fish_responses_accessed"] is False
    assert result["eBird_used"] is False
    assert "R7" not in str(result)
    assert "R1" not in str(result)

def test_fewer_than_two_method1_transects_on_one_year_not_eligible():
    data=[
      survey(1,"R1",2020,method="1"),
      survey(2,"R1",2020,method="1"),
      survey(3,"R1",2021,method="1"),
      survey(4,"R1",2021,method="12"),
      survey(5,"R1",2022,method="1"),
      survey(6,"R1",2022,method="1")
    ]
    r=tally_method1(data,CONTRACT)
    assert r["RLS_method1_strict_site_year_month_pairs"]==0

def test_duplicate_survey_id_is_not_inflated_into_two_transects():
    rows=[survey(1,"R1",2020),survey(1,"R1",2020),survey(2,"R1",2021)]
    r=tally_method1(rows,CONTRACT)
    assert r["method1_unique_events_by_program"]["RLS"]==2
    assert r["method1_duplicate_survey_ids_rejected"]==1
    assert r["RLS_method1_strict_site_year_month_pairs"]==0
