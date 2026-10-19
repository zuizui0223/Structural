"""Synthetic source-frame tests with no biological response values."""
import csv
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from biotime_v2_siteyear_frame_report_v1_250 import report, COLS

TRANSPORT={"status":"ORIGINAL_RDS_SOURCE_VERIFIED",
           "metadata":{"publisher_md5_verified":True}}


def fake_rows(path:Path):
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["STUDY_ID","REALM",*COLS])
        writer.writeheader()
        for i in range(226):
            realm="Marine" if i<107 else ("Terrestrial" if i<168 else "Freshwater")
            writer.writerow({"STUDY_ID":str(i+1),"REALM":realm,
                             **{x:(10 if x=="coordinate_sites" else
                                    5 if x in ("sites_at_least_three_observed_years",
                                              "sites_with_consecutive_years") else
                                    1 if x in ("sites_at_least_five_observed_years",
                                              "raw_consecutive_pairs",
                                              "same_month_consecutive_pairs",
                                              "same_month_pairs_each_visit_2plus") else
                                    10) for x in COLS}})
    return path


def test_counts_do_not_impersonate_true_species_colonization(tmp_path):
    out=report(fake_rows(tmp_path/"sample.csv"),TRANSPORT)
    assert out["total"]["metadata_screen_studies"]==226
    assert out["total"]["some_same_month_consecutive_site_years"]==226
    assert out["total"]["some_same_month_both_years_two_plus_events"]==226
    assert out["new_confirmatory_systems_admitted"]==0
    assert "No colonization/extinction" in " ".join(out["methodological_limits"])


def test_inconsistent_same_month_frames_fail(tmp_path):
    path=fake_rows(tmp_path/"sample.csv")
    rows=list(csv.DictReader(path.open(encoding="utf-8")))
    rows[0]["raw_consecutive_pairs"]="0"
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    try:
        report(path,TRANSPORT)
    except ValueError as e:
        assert "Same-month" in str(e)
    else:
        raise AssertionError("Inconsistent event frame was accepted")


def test_transport_integrity_is_required(tmp_path):
    path=fake_rows(tmp_path/"sample.csv")
    try:
        report(path,{"status":"TECHNICAL_STOP_NO_SAMPLE_FRAME"})
    except ValueError as e:
        assert "verified publisher" in str(e)
    else:
        raise AssertionError("Unverified RDS got treated as valid")
