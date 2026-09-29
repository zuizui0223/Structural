from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_global_mammals_id_crosswalk_v1_19.py"
CONTRACT = ROOT / "development/global_mammals_id_crosswalk_contract_v1_19.json"


def load_module():
    spec = importlib.util.spec_from_file_location("global_mammals_v119", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def small_contract(n: int):
    x = load_contract()
    x["response_identity"] = dict(x["response_identity"])
    x["response_identity"]["expected_data_row_count"] = n
    x["decision_rule"] = json.loads(json.dumps(x["decision_rule"]))
    x["decision_rule"]["success_requires"] = {
        "response_data_row_count": n,
        "response_distinct_canonical_id_count": n,
        "matched_safe_id_count": n,
        "unmatched_response_id_count": 0,
        "duplicate_response_id_count": 0,
    }
    return x


def test_contract_freezes_numeric_exact_membership_before_semantic_open():
    x = load_contract()
    assert x["response_identity"]["expected_data_row_count"] == 5592
    assert x["safe_reference_identity"]["safe_distinct_id_count"] == 17883
    assert x["canonicalization"]["accepted_raw_pattern"] == "^[0-9]+$"
    assert x["canonicalization"]["fuzzy_matching_allowed"] is False
    assert x["canonicalization"]["name_matching_allowed"] is False
    assert x["canonicalization"]["coordinate_matching_allowed"] is False
    semantic = x["semantic_access"]
    assert semantic["header_first_field_decoded"] is True
    assert semantic["header_other_fields_decoded"] == 0
    assert semantic["species_header_fields_decoded"] == 0
    assert semantic["occurrence_values_decoded"] == 0
    assert semantic["biological_response_values_opened"] is False


def test_first_field_parser_ignores_invalid_utf8_in_all_other_fields():
    module = load_module()
    raw = (
        b'ID,"species,one",species_two\n'
        b'0007,\xff,\xfe\n'
        b'"8",\xfe,\xff\n'
        b'9,"opaque\nquoted\xff",\xfe\n'
    )
    fields = list(module.iter_first_field_bytes(raw))
    assert fields == [b"ID", b"0007", b"8", b"9"]

    receipt, ids = module.crosswalk_response_bytes(
        raw,
        safe_id_set={"7", "8", "9"},
        contract=small_contract(3),
    )
    assert receipt["status"] == "EXACT_ROUTING_ID_CROSSWALK_COMPLETE"
    assert receipt["routing_header_first_field"] == "ID"
    assert receipt["routing_ids_decoded"] == 3
    assert receipt["matched_safe_id_count"] == 3
    assert receipt["unmatched_response_id_count"] == 0
    assert receipt["duplicate_response_id_count"] == 0
    assert receipt["species_header_fields_decoded"] == 0
    assert receipt["occurrence_values_decoded"] == 0
    assert receipt["biological_response_values_opened"] is False
    assert ids["routing_ids_in_response_order"] == ["7", "8", "9"]


def test_leading_zero_canonicalization_is_identical_for_response_and_safe_ids():
    module = load_module()
    assert module.canonicalize_id_text("000123") == "123"
    assert module.canonicalize_id_bytes(b"\t000123\r") == "123"
    assert module.canonicalize_id_text("0") == "0"
    for value in ("-1", "+1", "1.0", "1e3", "", "  "):
        with pytest.raises(module.GlobalMammalIdCrosswalkError):
            module.canonicalize_id_text(value)


def test_unmatched_id_holds_without_fuzzy_rescue():
    module = load_module()
    raw = b"ID,s1\n7,1\n8,0\n999,1\n"
    receipt, ids = module.crosswalk_response_bytes(
        raw,
        safe_id_set={"7", "8", "9"},
        contract=small_contract(3),
    )
    assert receipt["status"] == "HOLD_ROUTING_ID_CROSSWALK_INCOMPLETE"
    assert receipt["matched_safe_id_count"] == 2
    assert receipt["unmatched_response_id_count"] == 1
    assert receipt["same_revision_fuzzy_rescue_authorized"] is False
    assert receipt["safe_population_projection_may_be_built"] is False
    assert ids["routing_ids_in_response_order"] == []


def test_duplicate_canonical_ids_hold_even_if_raw_strings_differ():
    module = load_module()
    raw = b"ID,s1\n7,1\n007,0\n9,1\n"
    receipt, _ = module.crosswalk_response_bytes(
        raw,
        safe_id_set={"7", "9"},
        contract=small_contract(3),
    )
    assert receipt["status"] == "HOLD_ROUTING_ID_CROSSWALK_INCOMPLETE"
    assert receipt["response_distinct_canonical_id_count"] == 2
    assert receipt["duplicate_response_id_count"] == 1


def test_routing_id_fingerprint_is_order_sensitive():
    module = load_module()
    assert module.id_fingerprint(["7", "8", "9"]) != module.id_fingerprint(
        ["9", "8", "7"]
    )
    expected = hashlib.sha256(b"7\n8\n9\n").hexdigest()
    assert module.id_fingerprint(["7", "8", "9"]) == expected
