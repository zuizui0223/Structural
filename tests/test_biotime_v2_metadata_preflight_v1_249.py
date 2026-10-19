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
