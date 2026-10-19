"""Original 10-region AODN RLS Method 1 physical-event gate; no fish responses.

The synthetic fixture is constrained to the previously frozen ten locality identities.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from nrmn_rls_method1_physical_v1_261 import method_codes, accumulate_method1

def contract():
    return {
        "schema":"structural.nrmn_rls_method1_physical_protocol.v1_261",
        "frozen_RLS_geographic_groups":[
            {"country":"australia","area":"western australia","location":"rottnest island",
             "previous_strict_all_method_pairs":105},
            {"country":"australia","area":"new south wales","location":"lord howe island",
             "previous_strict_all_method_pairs":32}
        ]
    }


def row(i,year,month,site="RT1",location="Rottnest Island",methods="1, 2",program="RLS",lat=-32.0,lon=115.5):
    return {"survey_id":i,"survey_date":f"{year:04d}-{month:02d}-15",
            "country":"Australia","area":"Western Australia",
            "location":location,"site_code":site,
            "latitude":lat,"longitude":lon,"depth":10,
            "program":program,"methods":methods}


def test_numeric_one_is_not_eleven_or_thirteen():
    assert method_codes("1, 2, 13")==(1,2,13)
    assert method_codes("11, 13")== (11,13)
    assert method_codes("1, 2").count(1)==1
    assert method_codes("1, 2 - 3") is None
    assert method_codes("")==tuple()


def test_true_method1_paired_events_require_two_each_year():
    rows=[];k=100
    for ix in range(5):
        for year in (2020,2021,2022):
            for rep in range(2):
                rows.append(row(k,year,8,site=f"R{ix}",lat=-32+ix*.01));k+=1
    # Abundance/species sentinel keys are unreferenced by source-only reader.
    for item in rows:
        item.update({"species_name":"SECRET_DO_NOT_READ","total":9999})
    r=accumulate_method1(rows,contract())
    assert r["source_rows_seen"]==30
    assert r["method1_RLS_surveys_in_fixed_10_groups"]==30
    rr=r["fixed_RLS_group_method1_physical_support"][0]
    assert rr["location"]=="rottnest island"
    assert rr["stable_method1_sites"]==5
    assert rr["sites_with_three_observed_method1_years"]==5
    assert rr["strict_method1_same_month_next_year_site_pairs"]==10
    assert rr["distinct_prior_years_with_method1_pairs"]==2
    assert rr["method1_physical_qualified"] is True
    assert "SECRET_DO_NOT_READ" not in str(r)
    assert "9999" not in str(r)


def test_method11_and_atrc_never_create_method1_RLS_denominators():
    rows=[]
    for ix in range(5):
        for year in (2020,2021,2022):
            rows.append(row(1000+ix*10+year-2020,year,8,site=f"R{ix}",methods="11, 13"))
            rows.append(row(2000+ix*10+year-2020,year,8,site=f"R{ix}",program="ATRC",methods="1, 2"))
    r=accumulate_method1(rows,contract())
    assert r["method1_RLS_surveys_in_fixed_10_groups"]==0
    assert r["strict_method1_pairs_total"]==0
    assert not any(x["method1_physical_qualified"] for x in r["fixed_RLS_group_method1_physical_support"])


def test_duplicate_id_and_unstable_sites_are_not_independent():
    rows=[]
    for yr in (2020,2021,2022):
        rows.append(row(yr*10+1,yr,8,site="A"))
        rows.append(row(yr*10+1,yr,8,site="A")) # duplicate survey ID
        rows.append(row(yr*10+2,yr,8,site="A",lat=-32 + (yr-2020)*.05))
    r=accumulate_method1(rows,contract())
    assert r["duplicate_survey_ids"]==3
    assert r["method1_RLS_surveys_in_fixed_10_groups"]==6
    assert r["strict_method1_pairs_total"]==0
    assert r["geographically_unstable_method1_sites"]==1
