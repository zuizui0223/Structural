"""Synthetic-only and metadata-only integrity checks; never reads biological outcomes."""
import csv
import hashlib
import importlib.util
import io
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/"scripts"))
import biotime_v2_metadata_preflight_v1_249 as m


def make_csv(n=708):
    s=io.StringIO()
    w=csv.DictWriter(s,fieldnames=["STUDY_ID","REALM","start_year","end_year","site_count","Latitude"])
    w.writeheader()
    for i in range(n):
        w.writerow({"STUDY_ID":str(i+1),"REALM":"Marine" if i%3==0 else "Terrestrial",
                    "start_year":"2001","end_year":"2019", "site_count":"7","Latitude":"50.5"})
    return s.getvalue().encode("utf-8")


def test_metadata_reader_reports_no_unseen_biology():
    summary=m.study_summary(make_csv())
    assert summary["metadata_rows"] == 708
    assert summary["unique_study_identifiers"] == 708
    assert summary["yearlike_fields"]["start_year"]["min"] == 2001
    assert summary["yearlike_fields"]["end_year"]["max"] == 2019
    assert summary["has_site_year_abundance_response"] is False
    assert summary["has_verified_0_to_1_colonization"] is False


def test_synthetic_invalid_source_rows_rejected():
    try:
        m.study_summary(make_csv(100))
    except m.SourceStop as e:
        assert "rows" in str(e)
    else:
        raise AssertionError("Insufficient number of source rows accepted")


def test_publisher_hash_exact_and_source_route_locked():
    assert m.EXPECTED_MD5 == "3daed71ed554888309f9f2443a847bea"
    assert len(m.URLS)==2
    assert all(m.FILENAME in x and "15222193" in x for x in m.URLS)
    assert m.MAX_BYTES < 10_000_000


def test_no_observation_file_path_in_source_queries():
    for url in m.URLS:
        assert ".rds" not in url
        assert ".sql" not in url
        assert "metadata" in url.lower()


def test_year_field_guard():
    assert m._simple_numeric_year("2023.0") == 2023
    assert m._simple_numeric_year("1893") == 1893
    assert m._simple_numeric_year("2023-08") is None
    assert m._simple_numeric_year("n/a") is None



def test_study_screen_is_candidate_only_not_a_temporal_endpoint():
    rows = [
        {"STUDY_ID":"1","START_YEAR":"2011","END_YEAR":"2020",
         "NUMBER_LAT_LONG":"25","NUMBER_OF_SAMPLES":"400",
         "NUMBER_OF_SPECIES":"35","REALM":"Terrestrial"},
        {"STUDY_ID":"2","START_YEAR":"2019","END_YEAR":"2020",
         "NUMBER_LAT_LONG":"2","NUMBER_OF_SAMPLES":"20",
         "NUMBER_OF_SPECIES":"3","REALM":"Freshwater"},
    ]
    result=m.spatial_temporal_study_screen(rows)
    assert result["status"]=="POTENTIAL_BY_METADATA_NOT_RESPONSE_APPROVED"
    assert result["source_studies_seen"]==2
    assert result["numerical_metadata_screen_counts"]["span5_sites10_samples100_species10"]==1
    assert result["numerical_metadata_screen_counts"].get("span8_sites20_samples1000_species20",0)==0
    assert "the same location was surveyed in at least two or three separate years" in result["not_yet_verified"]


def test_duplicate_study_id_is_not_independent_study():
    row={"STUDY_ID":"1","START_YEAR":"2011","END_YEAR":"2020",
         "NUMBER_LAT_LONG":"25","NUMBER_OF_SAMPLES":"400",
         "NUMBER_OF_SPECIES":"35","REALM":"Terrestrial"}
    try:
        m.spatial_temporal_study_screen([row,row])
    except m.SourceStop as e:
        assert "Duplicate" in str(e)
    else:
        raise AssertionError("Duplicate study ID was treated as independent")
