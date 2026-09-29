#!/usr/bin/env python3
"""Run the frozen global-mammal routing-ID-only crosswalk v1.19."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Iterable, Mapping

from scripts.fetch_global_mammal_response_opaque_v1_17 import (
    GlobalMammalTransportError,
    transport as transport_v117,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/global_mammals_id_crosswalk_contract_v1_19.json"
)
DIGITS = re.compile(r"^[0-9]+$")


class GlobalMammalIdCrosswalkError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalMammalIdCrosswalkError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_fingerprint(ids: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in ids:
        digest.update(str(value).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def canonicalize_id_text(value: str) -> str:
    text = str(value).strip(" \t\r\n")
    if not text or DIGITS.fullmatch(text) is None:
        raise GlobalMammalIdCrosswalkError(
            f"routing ID is not unsigned base-10 digits: {text!r}"
        )
    return str(int(text, 10))


def canonicalize_id_bytes(value: bytes) -> str:
    raw = value.strip(b" \t\r\n")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GlobalMammalIdCrosswalkError(
            "routing ID field is not valid UTF-8"
        ) from exc
    return canonicalize_id_text(text)


def iter_first_field_bytes(raw: bytes):
    """Yield only each RFC4180-style record's first field as opaque bytes.

    The remainder of each record is scanned only for CSV quote/record boundaries
    and is never retained or Unicode-decoded.
    """
    first = bytearray()
    first_field = True
    in_quotes = False
    at_field_start = True
    record_has_bytes = False
    i = 0

    while i < len(raw):
        b = raw[i]
        record_has_bytes = True

        if in_quotes:
            if b == 34:  # "
                if i + 1 < len(raw) and raw[i + 1] == 34:
                    if first_field:
                        first.append(34)
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            if first_field:
                first.append(b)
            i += 1
            continue

        if at_field_start and b == 34:
            in_quotes = True
            at_field_start = False
            i += 1
            continue

        if b == 44:  # comma
            first_field = False
            at_field_start = True
            i += 1
            continue

        if b == 10:  # LF outside quotes ends record
            value = bytes(first)
            if value.endswith(b"\r"):
                value = value[:-1]
            yield value
            first.clear()
            first_field = True
            in_quotes = False
            at_field_start = True
            record_has_bytes = False
            i += 1
            continue

        if first_field:
            first.append(b)
        at_field_start = False
        i += 1

    if in_quotes:
        raise GlobalMammalIdCrosswalkError(
            "unterminated quoted CSV field"
        )
    if record_has_bytes:
        value = bytes(first)
        if value.endswith(b"\r"):
            value = value[:-1]
        yield value


def load_safe_ids(
    safe_csv: Path,
    safe_receipt: Path,
    *,
    contract: Mapping,
) -> tuple[tuple[str, ...], set[str]]:
    safe = contract["safe_reference_identity"]
    if sha256_file(safe_csv) != safe["safe_csv_sha256"]:
        raise GlobalMammalIdCrosswalkError(
            "Weigelt safe CSV SHA mismatch"
        )
    if sha256_file(safe_receipt) != safe["safe_receipt_sha256"]:
        raise GlobalMammalIdCrosswalkError(
            "Weigelt safe receipt SHA mismatch"
        )
    receipt = _load(safe_receipt)
    if receipt.get("schema") != (
        "structural.global_mammals_weigelt_safe_rows_result.v0_60"
    ):
        raise GlobalMammalIdCrosswalkError(
            "unexpected Weigelt safe receipt schema"
        )
    if receipt.get("status") != "safe_islanddata_rows_extracted":
        raise GlobalMammalIdCrosswalkError(
            "Weigelt safe rows did not qualify"
        )
    if receipt.get("row_count") != safe["safe_row_count"]:
        raise GlobalMammalIdCrosswalkError(
            "Weigelt safe row count drift"
        )
    if receipt.get("distinct_id_count") != safe["safe_distinct_id_count"]:
        raise GlobalMammalIdCrosswalkError(
            "Weigelt distinct ID count drift"
        )
    if receipt.get("mammal_response_values_opened") is not False:
        raise GlobalMammalIdCrosswalkError(
            "Weigelt safe receipt response boundary violated"
        )

    with safe_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or safe["safe_id_column"] not in reader.fieldnames:
            raise GlobalMammalIdCrosswalkError(
                "Weigelt safe ID column missing"
            )
        ordered = tuple(
            canonicalize_id_text(row[safe["safe_id_column"]])
            for row in reader
        )
    if len(ordered) != safe["safe_row_count"]:
        raise GlobalMammalIdCrosswalkError(
            "Weigelt safe CSV row count drift"
        )
    if len(set(ordered)) != safe["safe_distinct_id_count"]:
        raise GlobalMammalIdCrosswalkError(
            "Weigelt canonical IDs are not unique"
        )
    return ordered, set(ordered)


def crosswalk_response_bytes(
    response_bytes: bytes,
    *,
    safe_id_set: set[str],
    contract: Mapping,
) -> tuple[dict, dict]:
    fields = iter_first_field_bytes(response_bytes)
    try:
        header_raw = next(fields)
    except StopIteration as exc:
        raise GlobalMammalIdCrosswalkError(
            "response CSV is empty"
        ) from exc

    try:
        header_first = header_raw.strip(b" \t\r\n").decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GlobalMammalIdCrosswalkError(
            "response routing header first field is not valid UTF-8"
        ) from exc
    if not header_first:
        raise GlobalMammalIdCrosswalkError(
            "response routing header first field is blank"
        )

    ids = []
    for raw_id in fields:
        ids.append(canonicalize_id_bytes(raw_id))

    expected_rows = int(
        contract["response_identity"]["expected_data_row_count"]
    )
    if len(ids) != expected_rows:
        raise GlobalMammalIdCrosswalkError(
            f"response routing row count drift: {len(ids)}"
        )

    distinct = len(set(ids))
    duplicates = len(ids) - distinct
    unmatched = [value for value in ids if value not in safe_id_set]
    matched = len(ids) - len(unmatched)

    unmatched_fingerprint = (
        id_fingerprint(sorted(unmatched))
        if unmatched
        else hashlib.sha256(b"").hexdigest()
    )
    success = (
        len(ids) == expected_rows
        and distinct == expected_rows
        and matched == expected_rows
        and len(unmatched) == 0
        and duplicates == 0
    )
    status = (
        contract["decision_rule"]["success_status"]
        if success
        else contract["decision_rule"]["failure_status"]
    )

    receipt = {
        "schema": "structural.global_mammals_id_crosswalk_result.v1_19",
        "status": status,
        "candidate_id": contract["candidate_id"],
        "routing_header_first_field": header_first,
        "routing_header_first_field_sha256": hashlib.sha256(
            header_first.encode("utf-8")
        ).hexdigest(),
        "response_data_row_count": len(ids),
        "response_distinct_canonical_id_count": distinct,
        "safe_id_universe_count": len(safe_id_set),
        "matched_safe_id_count": matched,
        "unmatched_response_id_count": len(unmatched),
        "duplicate_response_id_count": duplicates,
        "routing_ids_sha256": id_fingerprint(ids),
        "unmatched_ids_sha256": unmatched_fingerprint,
        "header_first_field_decoded": True,
        "routing_ids_decoded": len(ids),
        "species_header_fields_decoded": 0,
        "occurrence_values_decoded": 0,
        "row_remainder_semantics_opened": False,
        "biological_response_values_opened": False,
        "counts_as_empirical_evidence": False,
        "counts_as_fresh_confirmation": False,
        "fresh_system_denominator_contribution": 0,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "safe_population_projection_may_be_built": bool(success),
        "same_revision_fuzzy_rescue_authorized": False,
        "same_revision_population_redefinition_authorized": False,
        "next_action": (
            contract["success_ceiling"]["next_action"]
            if success
            else (
                "HOLD exact ID crosswalk; do not inspect species headers, "
                "occurrence values, names or coordinates to rescue this "
                "protocol revision"
            )
        ),
    }
    ids_payload = {
        "schema": "structural.global_mammals_routing_id_population.v1_19",
        "status": (
            "FROZEN_EXACT_5592_ROUTING_ID_POPULATION"
            if success
            else "HOLD_INCOMPLETE_ROUTING_ID_POPULATION"
        ),
        "candidate_id": contract["candidate_id"],
        "canonicalization": dict(contract["canonicalization"]),
        "routing_header_first_field": header_first,
        "routing_id_count": len(ids),
        "distinct_routing_id_count": distinct,
        "routing_ids_sha256": id_fingerprint(ids),
        "routing_ids_in_response_order": ids if success else [],
        "unmatched_response_id_count": len(unmatched),
        "duplicate_response_id_count": duplicates,
        "species_header_fields_decoded": 0,
        "occurrence_values_decoded": 0,
        "biological_response_values_opened": False,
    }
    return receipt, ids_payload


def execute(
    *,
    safe_csv: Path,
    safe_receipt: Path,
    contract: Mapping,
    token: str,
    opener=None,
) -> tuple[dict, dict]:
    _, safe_id_set = load_safe_ids(
        safe_csv,
        safe_receipt,
        contract=contract,
    )
    response = contract["response_identity"]
    transport_contract = {
        "candidate_id": contract["candidate_id"],
        "target": {
            "name": response["name"],
            "dryad_file_id": response["dryad_file_id"],
            "download_url": response["download_url"],
            "expected_size_bytes": response["expected_size_bytes"],
            "expected_sha256": response["expected_sha256"],
        },
        "attempt_policy": {
            "credentialed_attempt_limit": contract[
                "transport_policy"
            ]["crosswalk_transport_attempt_limit"],
            "blind_endpoint_retry_authorized": contract[
                "transport_policy"
            ]["alternate_endpoint_retry_authorized"],
            "alternate_file_id_retry_authorized": contract[
                "transport_policy"
            ]["alternate_file_id_retry_authorized"],
        },
    }

    with tempfile.TemporaryDirectory() as tmp:
        response_path = Path(tmp) / response["name"]
        transport_receipt = transport_v117(
            response_path,
            contract=transport_contract,
            token=token,
            opener=opener,
        )
        if transport_receipt.get("status") != (
            "EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED"
        ):
            raise GlobalMammalIdCrosswalkError(
                "exact v1.19 response re-download did not qualify"
            )
        response_bytes = response_path.read_bytes()
        receipt, ids_payload = crosswalk_response_bytes(
            response_bytes,
            safe_id_set=safe_id_set,
            contract=contract,
        )

    receipt["transport"] = {
        "response_size_bytes": transport_receipt["target"]["size_bytes"],
        "response_sha256": transport_receipt["target"]["sha256"],
        "crosswalk_transport_attempt_consumed": True,
        "raw_response_retained_after_execution": False,
    }
    return receipt, ids_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--safe-csv", type=Path, required=True)
    parser.add_argument("--safe-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--routing-ids", type=Path)
    args = parser.parse_args()

    semantic_attempted = False
    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.global_mammals_id_crosswalk_contract.v1_19"
        ):
            raise GlobalMammalIdCrosswalkError(
                "unexpected v1.19 crosswalk contract schema"
            )
        if contract.get("status") != (
            "RESPONSE_ROUTING_ID_ONLY_CROSSWALK_PREDECLARED"
        ):
            raise GlobalMammalIdCrosswalkError(
                "v1.19 crosswalk contract status drift"
            )
        semantic_attempted = True
        receipt, ids_payload = execute(
            safe_csv=args.safe_csv,
            safe_receipt=args.safe_receipt,
            contract=contract,
            token=os.environ.get("DRYAD_TOKEN", ""),
        )
        code = 0 if receipt["status"] == (
            "EXACT_ROUTING_ID_CROSSWALK_COMPLETE"
        ) else 2
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        GlobalMammalTransportError,
        GlobalMammalIdCrosswalkError,
    ) as exc:
        receipt = {
            "schema": "structural.global_mammals_id_crosswalk_result.v1_19",
            "status": (
                "TERMINAL_ID_CROSSWALK_STOP_NO_RERUN_UNDER_V1_19"
                if semantic_attempted
                else "HOLD_NO_RETRY_UNDER_V1_19"
            ),
            "reason": str(exc),
            "header_first_field_decoded": False,
            "routing_ids_decoded": 0,
            "species_header_fields_decoded": 0,
            "occurrence_values_decoded": 0,
            "biological_response_values_opened": False,
            "counts_as_empirical_evidence": False,
            "counts_as_fresh_confirmation": False,
            "fresh_system_denominator_contribution": 0,
            "v0_11_intake_authorized": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "safe_population_projection_may_be_built": False,
            "same_revision_fuzzy_rescue_authorized": False,
        }
        ids_payload = None
        code = 2

    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    if ids_payload is not None and args.routing_ids is not None:
        args.routing_ids.parent.mkdir(parents=True, exist_ok=True)
        args.routing_ids.write_text(
            json.dumps(ids_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
