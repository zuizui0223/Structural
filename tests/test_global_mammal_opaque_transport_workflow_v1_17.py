from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "development/global_mammals_credentialed_opaque_transport_contract_v1_17.json"
)
REQUEST = (
    ROOT / "development/global_mammals_opaque_transport_request_v1_17.json"
)
WORKFLOW = (
    ROOT / ".github/workflows/global-mammals-opaque-transport-v1_17.yml"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_request_exactly_matches_frozen_transport_identity():
    contract = load(CONTRACT)
    request = load(REQUEST)
    target = contract["target"]

    assert request["dryad_file_id"] == target["dryad_file_id"] == 3242161
    assert request["expected_size_bytes"] == target["expected_size_bytes"] == 60486843
    assert request["expected_sha256"] == target["expected_sha256"] == (
        "32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6"
    )
    assert request["credentialed_attempt_limit"] == 1
    assert request["blind_endpoint_retry_authorized"] is False
    assert request["alternate_file_id_retry_authorized"] is False
    assert request["header_access_authorized"] is False
    assert request["routing_id_access_authorized"] is False
    assert request["species_header_access_authorized"] is False
    assert request["occurrence_value_access_authorized"] is False
    assert request["semantic_crosswalk_authorized_in_same_revision"] is False
    assert request["raw_response_artifact_authorized"] is False
    assert request["fresh_system_denominator_contribution"] == 0
    assert request["one_shot"] is True


def test_workflow_uses_oauth_helper_and_never_uploads_raw_response():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "prepare_dryad_token_v0_73.py" in text
    assert "secrets.DRYAD_CLIENT_ID" in text
    assert "secrets.DRYAD_CLIENT_SECRET" in text
    assert "fetch_global_mammal_response_opaque_v1_17.py" in text
    assert "rm -rf build/global_mammals_v117/raw" in text

    upload = text.split("Upload transport receipts only", 1)[1]
    assert "raw/Appendix_1_presence_absence.csv" not in upload
    assert "transport_receipt.json" in upload
    assert "token_receipt.json" in upload
    assert "retention-days: 30" in upload

    assert "workflow_dispatch:" not in text
    assert "paths:" in text
    assert "global_mammals_opaque_transport_request_v1_17.json" in text


def test_workflow_enforces_semantics_unopened_after_transport():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'receipt["header_decoded"] is False' in text
    assert 'receipt["routing_ids_decoded"] == 0' in text
    assert 'receipt["species_header_fields_decoded"] == 0' in text
    assert 'receipt["occurrence_values_decoded"] == 0' in text
    assert 'receipt["biological_response_values_opened"] is False' in text
    assert 'receipt["semantic_crosswalk_authorized_in_same_revision"] is False' in text
    assert 'receipt["raw_response_artifact_authorized"] is False' in text
