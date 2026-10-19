"""No biological data used. Lock the already frozen pilot study×source tier table."""
import csv
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from verify_biotime_v2_pilot_aggregate_v1_252 import audit

ROOT=Path(__file__).resolve().parents[1]
GROUPS=ROOT/"development/biotime_v2_burned_pilot_by_study_source_group_v1_252.csv"
FREEZE=ROOT/"development/biotime_v2_burned_pilot_aggregate_freeze_v1_252.json"
SPLIT=ROOT/"development/biotime_v2_pilot_confirmatory_split_v1_251.json"

def test_study_tier_and_replicated_detection_replay():
    r=audit(GROUPS,FREEZE,SPLIT)
    assert r["aggregate_comparisons"]==123584
    assert r["net_pilot_studies"]==14
    assert r["zero_to_one_detected"]==6274
    assert r["zero_to_one_2plus"]==2266
    assert r["source_5plus_higher_rate_studies"]==13
    assert r["source_5plus_equal_rate_studies"]==1
    assert r["source_5plus_repeated_higher_studies"]==13
    assert r["heldout_taxon_queries"]==0
    assert r["C_minus_CAL_not_scored"]

def test_study_tier_mutation_is_caught(tmp_path):
    text=GROUPS.read_text(encoding="utf-8")
    modified=text.replace("110,1,10677,929,794,439,318,129",
                          "110,1,10677,930,794,439,318,129")
    assert modified!=text
    fake=tmp_path/"altered.csv";fake.write_text(modified,encoding="utf-8")
    try:
        audit(fake,FREEZE,SPLIT)
    except ValueError as exc:
        assert "mismatch" in str(exc).lower() or "changed" in str(exc).lower()
    else:
        raise AssertionError("Aggregate response alteration must be rejected")
