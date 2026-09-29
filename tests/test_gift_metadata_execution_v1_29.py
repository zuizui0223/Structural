from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_request_is_one_shot_and_response_sealed():
    x=json.loads((ROOT/"development/gift_metadata_execution_request_v1_29.json").read_text())
    assert x["execution_attempt_limit"]==1
    assert x["species_composition_requested"] is False
    assert x["species_response_authorized"] is False

def test_workflow_is_push_request_scoped_and_metadata_only():
    s=(ROOT/".github/workflows/gift-metadata-one-shot-v1_29.yml").read_text()
    assert "paths:" in s
    assert "development/gift_metadata_execution_request_v1_29.json" in s
    assert "GIFT_species" not in s
    assert "freeze_gift_metadata_v0_89.R" in s
    assert "species_composition_opened" in s
    assert "retention-days: 30" in s
