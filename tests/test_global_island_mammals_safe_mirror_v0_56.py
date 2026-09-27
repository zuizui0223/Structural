from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
MIRROR=ROOT/"development/global_island_mammals_safe_mirror_v0_56.json"
STATUS=ROOT/"development/current_status_v0_56.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_safe_mirror_is_exact_and_response_independent():
    x=load(MIRROR)

    assert x["status"]=="figshare_weigelt_mirror_resolved_reference_gpkg_extraction_pending"
    assert x["mirror_source"]["source_file"]["size_bytes"]==2617794182
    assert x["mirror_source"]["source_file"]["md5"]=="da14f19b12bae704b9df4e5c380b69fd"
    assert x["zip_directory_probe"]["total_zip_metadata_bytes_read"]==131462
    assert x["zip_directory_probe"]["local_member_payload_bytes_read"]==0
    assert x["zip_directory_probe"]["decompressed_payload_bytes_read"]==0
    assert x["pristine_mammal_response"]["response_opened"] is False
    assert x["pristine_mammal_response"]["response_requests_from_figshare_probes"]==0


def test_reference_gpkg_identity_is_frozen_before_extraction():
    x=load(MIRROR)["reference_gpkg"]

    assert x["member_name"]=="reference.gpkg"
    assert x["compression_method"]==8
    assert x["compressed_size"]==2288242143
    assert x["uncompressed_size"]==3859476480
    assert x["crc32_hex"]=="ff89b951"
    assert x["local_header_offset"]==329551200
    assert x["payload_bytes_read_so_far"]==0
    assert x["decompressed_bytes_read_so_far"]==0


def test_v056_narrows_hold_without_promoting_candidate():
    s=load(STATUS)

    assert s["fresh_empirical_state"]["active_candidates"]==[]
    assert s["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    h=s["pristine_global_mammal_hold"]
    assert h["safe_mirror_resolved"] is True
    assert h["response_opened"] is False
    assert h["response_matrix_requests"]==0
    assert h["status"]=="HOLD_reference_gpkg_safe_geography_extraction_pending"
    assert "reference.gpkg" in s["next_valid_scientific_event"]


def test_mirror_resolution_authorizes_no_response_or_intake():
    x=load(MIRROR)["evidence_boundary"]

    assert x["counts_as_empirical_evidence"] is False
    assert x["counts_as_fresh_confirmation"] is False
    assert x["mammal_response_opened"] is False
    assert x["v0_11_intake_authorized"] is False
    assert x["pilot_response_authorized"] is False
    assert x["confirmatory_response_authorized"] is False
