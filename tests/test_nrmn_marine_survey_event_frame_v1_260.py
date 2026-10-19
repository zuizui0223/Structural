"""Exact source-free RLS survey event frame checks; never fish biological data."""
import copy
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from nrmn_marine_survey_event_frame_v1_260 import accumulate, program_class, physical_row

CONTRACT=json.loads((ROOT/"development/nrmn_marine_survey_event_frame_protocol_v1_260.json").read_text())

def synthetic(sites=5,years=(2020,2021,2022),transects=2,program="RLS"):
    rows=[]
    i=100
    for s in range(sites):
        for year in years:
            for t in range(transects):
                i+=1
                rows.append({
                    "survey_id":i,"survey_date":f"{year}-08-{t+3:02d}",
                    "country":"Australia","area":"Queensland",
                    "location":"Research Reefs","site_code":f"IS{s+1}",
                    "latitude":-18.0-(s/1000),
                    "longitude":146.0+(s/1000),
                    "depth":8 if t==0 else 12,
                    "program":program,
                    "methods":"M1;M2",
                    "species_name":"SECRET_RESPONSE_MUST_NOT_READ",
                    "total":1000000,
                })
    return rows

def test_synthetic_independent_sites_years_and_2_transects():
    result=accumulate(synthetic(),CONTRACT)
    assert result["unique_valid_survey_ids"]==30
    assert result["RLS_strict_same_month_site_year_pairs"]==10
    assert result["qualified_physical_groups_by_program"]["RLS"]==1
    target=result["physical_groups_ranked_by_repetition"][0]
    assert target["stable_site_codes"]==5
    assert target["sites_with_three_observed_years"]==5
    assert target["distinct_prior_years_with_pairs"]==2
    assert target["strict_same_month_consecutive_year_pairs_both_2plus"]==10
    assert target["preoutcome_qualified_physical_group"]
    assert "SECRET_RESPONSE_MUST_NOT_READ" not in str(result)
    assert result["biological_fish_species_or_counts_accessed"] is False

def test_single_transects_do_not_qualify_physical_denominator():
    result=accumulate(synthetic(transects=1),CONTRACT)
    assert result["qualified_physical_groups_by_program"]=={}
    assert result["RLS_strict_same_month_site_year_pairs"]==0

def test_dupe_survey_ids_not_double_counted():
    rows=synthetic()
    rows.append(copy.deepcopy(rows[0]))
    result=accumulate(rows,CONTRACT)
    assert result["unique_valid_survey_ids"]==30
    assert result["count_invalid_by_reason"]["duplicate_survey_id"]==1

def test_coordinate_unstable_record_drops_site_only_from_repetition():
    rows=synthetic()
    rows[0]["latitude"]+=0.02
    result=accumulate(rows,CONTRACT)
    assert result["count_invalid_by_reason"]["site_code_spatially_unstable"]==1
    assert result["qualified_physical_groups_by_program"]=={}
    assert result["RLS_strict_same_month_site_year_pairs"]==8

def test_program_separation_and_methods_not_interpreted_as_presence():
    assert program_class("RLS")=="RLS"
    assert program_class("ATRC")=="ATRC"
    assert program_class("RLS, ATRC")=="MIXED"
    assert program_class("RLS2")=="OTHER"
    result=accumulate(synthetic(program="ATRC"),CONTRACT)
    assert result["qualified_physical_groups_by_program"]=={"ATRC":1}
    assert result["RLS_strict_same_month_site_year_pairs"]==0

def test_frozen_survey_field_whitelist_required():
    mutated=json.loads(json.dumps(CONTRACT))
    mutated["allowed_input_columns"].append("species_name")
    with pytest.raises(ValueError,match="eleven"):
        accumulate(synthetic(),mutated)
