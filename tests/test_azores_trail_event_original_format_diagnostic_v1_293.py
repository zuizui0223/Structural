"""No plant data: test v1.293 terminal original Event code grammar diagnostic."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tests"))
from azores_trail_event_original_format_diagnostic_v1_293 import audit_syntax
from test_azores_trail_plants_event_hierarchy_v1_292 import records

def test_unknown_sample_area_diagnostic_not_ecological_scoring():
    e=records()
    e[0]["eventID"]=e[0]["eventID"].replace(".0.1.50",".entrance.1.50")
    r=audit_syntax(e)
    assert r["status"]=="RESPONSE_UNOPENED_EVENT_FORMAT_DIAGNOSED_OLD_V1_292_TERMINAL"
    assert r["source_year_or_code_mismatch_counts"]["unrecognized_area"]==1
    assert {"code_kind":"area","value":"entrance","count":1} in r["unrecognized_published_area_plot_line_code_vocabulary_counts"]
    assert r["original_Occurrence_data_rows_opened"]==0
    assert r["old_v1_292_remains_terminal"]
    assert r["source_Event_or_site_full_identifier_exported"] is False
    assert "mist.negros" not in json.dumps(r)

def test_valid_syntax_zero_error_counts_does_not_reauthorize_terminal_v292():
    r=audit_syntax(records())
    assert r["source_year_or_code_mismatch_counts"]=={}
    assert r["old_v1_292_remains_terminal"]
    assert r["new_confirmatory_systems"]==0
    assert not r["eBird_used"]
