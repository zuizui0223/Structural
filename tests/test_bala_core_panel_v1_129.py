from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_core_panel_rule_uses_official_three_wave_metadata():
    x=json.loads((ROOT/"development/bala_core_panel_contract_v1_129.json").read_text())
    m=x["official_response_independent_metadata"]
    assert m["core_sampling_events_reported"]==4929
    assert m["core_transects_reported"]==30
    assert m["core_fragments_reported"]==15
    assert m["core_islands_reported"]==7
    assert m["phase_windows"]=={"BALA1":[1997,2004],"BALA2":[2010,2011],"BALA3":[2019,2022]}

def test_coordinate_site_key_is_frozen_because_locationid_does_not_recover_all_30():
    x=json.loads((ROOT/"development/bala_core_panel_contract_v1_129.json").read_text())
    s=x["site_identity"]
    assert s["rule"].startswith("island code plus decimalLatitude")
    assert "locationID yields only 29" in s["why_not_locationID"]
    assert s["expected_core_sites"]==30
    assert s["rounding_decimals"]==5

def test_occurrence_never_defines_core_membership():
    x=json.loads((ROOT/"development/bala_core_panel_contract_v1_129.json").read_text())
    assert x["core_event_rule"]["occurrence_rows_may_not_be_used_to_define_core_membership"] is True
    assert x["response_boundary"]["occurrence_extension_semantically_opened"] is False
    assert x["response_boundary"]["taxon_occurrence_values_opened"]==0

def test_script_uses_only_event_core_for_panel():
    s=(ROOT/"scripts/freeze_bala_core_panel_v1_129.py").read_text()
    assert "parse_event_core(event_bytes,core)" in s
    assert "del occ_bytes" in s
    assert "if ph and k in common" in s
    assert "event_by_taxon_rows_parsed" in s
    assert "taxon_occurrence_values_opened" in s

def test_workflow_requires_exact_30_4929_15_7():
    s=(ROOT/".github/workflows/bala-core-panel-v1_129.yml").read_text()
    assert 'x["core_sites"]==30' in s
    assert 'x["core_event_rows"]==4929' in s
    assert 'x["core_fragments"]==15' in s
    assert 'x["core_islands"]==7' in s
    assert "occurrence.txt" not in s
