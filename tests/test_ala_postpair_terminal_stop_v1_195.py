from pathlib import Path
import json
import re
import struct

ROOT=Path(__file__).resolve().parents[1]
AUD=ROOT/"development/ala_external_positive_technical_stop_v1_195.json"
WRITER=ROOT/"scripts/freeze_global_mammals_ultrarare_predictions_v1_113.py"
READER=ROOT/"scripts/score_global_mammals_ala_positive_locations_v1_194.py"

def test_freeze_matches_technical_stop_and_no_response_rescue():
    a=json.loads(AUD.read_text())
    r=json.loads((ROOT/"development/global_mammals_ala_positive_only_result_v1_194.json").read_text())
    assert a["source_execution"]["error_reason"]=="prediction shape drift"
    assert r["status"]=="STOP_ALA_EXTERNAL_PAIR_SCHEMA_OR_FROZEN_INPUT_DRIFT"
    assert r["scores_computed"] is False
    assert r["original_heldout_labels_read"]==0
    assert a["boundary_at_failure"]["primary_P1"] is None
    assert a["boundary_at_failure"]["topology_P2"] is None
    assert a["frozen_preregistered_policy"]["same_lineage_rerun_authorized"] is False
    assert a["frozen_preregistered_policy"]["no_technical_score_recovery_authorized"] is True

def test_original_two_integer_header_not_three():
    s=WRITER.read_text()
    reader=READER.read_text()
    assert 'struct.pack("<II",4126,S)' in s
    assert 'read_predictions(actual_file,ACTUAL_MAGIC,(4126,529,2))' in reader
    assert "len(shape)*4" in reader
    header=struct.pack("<II",4126,529)
    assert struct.unpack("<II",header)==(4126,529)
    assert len(header)==8
    assert len(header)!=3*4

def test_gate_chronology_is_after_external_pair_access():
    s=READER.read_text()
    assert s.index("pos,record_audit=extract_positive_pairs(") < s.index("actual=read_predictions(")
    assert s.index('support["pairs"]>=minimum["minimum_distinct_positive_pairs"]') < s.index("actual=read_predictions(")

def test_original_evidence_unchanged():
    a=json.loads(AUD.read_text())
    assert a["boundary_at_failure"]["biological_negative_result"] is False
    assert a["boundary_at_failure"]["external_score_computed"] is False
    assert a["eBird_enabled"] is False
