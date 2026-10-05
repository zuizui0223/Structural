from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_inventory_freeze_has_one_mixed_file_only():
    x=json.loads((ROOT/"development/finnish_eider_zenodo_inventory_freeze_v1_152.json").read_text())
    inv=x["inventory"]
    assert inv["file_count"]==1
    assert inv["separate_pos2_file_present"] is False
    assert inv["separate_distance_file_present"] is False
    assert inv["only_file"]["md5"] if "md5" in inv["only_file"] else inv["only_file"]["zenodo_checksum"]=="md5:4f48d8faf2b6dbb8c967449356beab87"

def test_header_contract_allows_only_first_line_semantics():
    x=json.loads((ROOT/"development/finnish_eider_mixed_header_contract_v1_152.json").read_text())
    assert "first physical line only" in x["allowed_semantic_access"]
    assert "decode any byte after the first line terminator" in x["forbidden_semantic_access"]
    assert "Eider_pairs" in x["published_expected_headers"]
    assert "pos2" in x["published_expected_headers"]
    assert x["evidence_boundary"]["may_count_as_confirmation"] is False

def test_header_script_decodes_only_header_bytes():
    s=(ROOT/"scripts/audit_finnish_eider_mixed_header_v1_152.py").read_text()
    assert "first_line_bytes" in s
    assert "Decode only the header bytes" in s
    assert 'first.decode("utf-8-sig")' in s
    assert "Eider_pairs_values_opened" in s
    assert "pos2_values_opened" in s

def test_workflow_deletes_raw_file_before_artifact():
    s=(ROOT/".github/workflows/finnish-eider-mixed-header-v1_152.yml").read_text()
    assert "Delete raw mixed response file" in s
    assert "rm -f build/finnish_eider_v152/raw_mixed_file.tmp" in s
    upload=s.split("Upload header-only audit",1)[1]
    assert "raw_mixed_file.tmp" not in upload
    assert "header_manifest.json" in upload
