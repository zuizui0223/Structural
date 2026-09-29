#!/usr/bin/env python3
"""Project only the frozen 13 safe Appendix 2 columns for 5,592 islands."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from urllib.request import Request, build_opener

from scripts.audit_global_mammals_appendix2_header_v1_21 import (
    StripAuthorizationOnCrossOriginRedirect,
    _selected_shared_strings,
    audit_workbook,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/global_mammals_appendix2_safe_rows_contract_v1_23.json"
)
DEFAULT_FIREWALL = (
    ROOT / "development/global_mammals_appendix2_column_firewall_v1_22.json"
)

ROW_RE = re.compile(
    br"<(?:[A-Za-z_][\w.-]*:)?row\b(?P<attrs>[^>]*)>"
    br"(?P<body>.*?)"
    br"</(?:[A-Za-z_][\w.-]*:)?row\s*>",
    re.DOTALL,
)
CELL_RE = re.compile(
    br"<(?:[A-Za-z_][\w.-]*:)?c\b(?P<attrs>[^>]*)>"
    br"(?P<body>.*?)"
    br"</(?:[A-Za-z_][\w.-]*:)?c\s*>"
    br"|"
    br"<(?:[A-Za-z_][\w.-]*:)?c\b(?P<selfattrs>[^>]*)/>",
    re.DOTALL,
)
ATTR_RE_CACHE: dict[str, re.Pattern[bytes]] = {}
CELL_REF_RE = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")
V_RE = re.compile(
    br"<(?:[A-Za-z_][\w.-]*:)?v(?:\s[^>]*)?>(.*?)"
    br"</(?:[A-Za-z_][\w.-]*:)?v\s*>",
    re.DOTALL,
)
F_RE = re.compile(br"<(?:[A-Za-z_][\w.-]*:)?f(?:\s|>)")


class GlobalMammalSafeRowsError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalMammalSafeRowsError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _attr(attrs: bytes, name: str) -> bytes | None:
    pattern = ATTR_RE_CACHE.get(name)
    if pattern is None:
        pattern = re.compile(
            rb"(?:^|\s)" + re.escape(name.encode("ascii")) + rb'="([^"]*)"'
        )
        ATTR_RE_CACHE[name] = pattern
    match = pattern.search(attrs)
    return None if match is None else match.group(1)


def _column_index_from_ref(ref: str) -> int:
    match = CELL_REF_RE.fullmatch(ref)
    if match is None:
        raise GlobalMammalSafeRowsError(
            f"invalid worksheet cell reference: {ref!r}"
        )
    letters = match.group(1)
    value = 0
    for ch in letters:
        value = value * 26 + (ord(ch) - ord("A") + 1)
    return value - 1


def _decode_ascii_or_utf8(raw: bytes, *, label: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GlobalMammalSafeRowsError(
            f"invalid UTF-8 in opened safe {label}"
        ) from exc


def _extract_v(body: bytes) -> bytes:
    match = V_RE.search(body)
    if match is None:
        return b""
    return match.group(1)


def _decode_inline_string(body: bytes) -> str:
    try:
        root = ET.fromstring(b"<root>" + body + b"</root>")
    except ET.ParseError as exc:
        raise GlobalMammalSafeRowsError(
            "invalid inline-string XML in safe cell"
        ) from exc
    return "".join(
        node.text or ""
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1] == "t"
    )


def _decode_safe_cell_fragment(
    *,
    attrs: bytes,
    body: bytes,
    cell_ref: str,
) -> tuple[str, int | None]:
    if F_RE.search(body):
        raise GlobalMammalSafeRowsError(
            f"formula in safe cell is forbidden: {cell_ref}"
        )
    raw_type = _attr(attrs, "t")
    ctype = (
        ""
        if raw_type is None
        else _decode_ascii_or_utf8(raw_type, label=f"{cell_ref}.type").strip()
    )
    if ctype == "s":
        text = _decode_ascii_or_utf8(
            _extract_v(body),
            label=f"{cell_ref}.shared_string_index",
        ).strip()
        try:
            index = int(text)
        except ValueError as exc:
            raise GlobalMammalSafeRowsError(
                f"invalid shared-string index in safe cell: {cell_ref}"
            ) from exc
        if index < 0:
            raise GlobalMammalSafeRowsError(
                f"negative shared-string index in safe cell: {cell_ref}"
            )
        return "", index
    if ctype == "inlineStr":
        return _decode_inline_string(body), None
    if ctype in {"", "n", "str", "b"}:
        return _decode_ascii_or_utf8(
            _extract_v(body),
            label=f"{cell_ref}.value",
        ), None
    raise GlobalMammalSafeRowsError(
        f"unsupported safe cell type {ctype!r} at {cell_ref}"
    )


def _parse_number(value: str, *, column: str) -> float:
    text = value.strip()
    if not text:
        raise GlobalMammalSafeRowsError(
            f"blank numeric safe value: {column}"
        )
    try:
        number = float(text)
    except ValueError as exc:
        raise GlobalMammalSafeRowsError(
            f"nonnumeric safe value: {column}"
        ) from exc
    if not math.isfinite(number):
        raise GlobalMammalSafeRowsError(
            f"nonfinite safe value: {column}"
        )
    return number


def _validate_and_encode_row(
    row: dict[str, str],
    *,
    safe_columns: tuple[str, ...],
) -> list[str]:
    out = []
    for column in safe_columns:
        value = str(row[column]).strip()
        if column == "ID":
            if not value:
                raise GlobalMammalSafeRowsError("blank ID")
            out.append(value)
            continue
        if column == "bioregion":
            if not value:
                raise GlobalMammalSafeRowsError("blank bioregion")
            out.append(value)
            continue

        number = _parse_number(value, column=column)
        if column == "Longitude_centroid" and not -180.0 <= number <= 180.0:
            raise GlobalMammalSafeRowsError(
                "Longitude_centroid outside [-180,180]"
            )
        if column == "Latitude_centroid" and not -90.0 <= number <= 90.0:
            raise GlobalMammalSafeRowsError(
                "Latitude_centroid outside [-90,90]"
            )
        if column == "Area" and not number > 0.0:
            raise GlobalMammalSafeRowsError("Area must be positive")
        if column in {
            "Temperature_sd",
            "Precipitation_sd",
            "Elevation_sd",
        } and number < 0.0:
            raise GlobalMammalSafeRowsError(
                f"{column} must be nonnegative"
            )
        out.append(float(number).hex())
    return out


def _download_exact(
    destination: Path,
    *,
    contract: dict,
    token: str,
    opener=None,
) -> None:
    source = contract["source"]
    policy = contract["transport_policy"]
    if not token or "\n" in token or "\r" in token:
        raise GlobalMammalSafeRowsError(
            "DRYAD_TOKEN is missing or malformed"
        )
    if policy["exact_file_only"] is not True:
        raise GlobalMammalSafeRowsError(
            "exact-file-only transport invariant drift"
        )
    if policy["alternate_file_id_retry_authorized"] is not False:
        raise GlobalMammalSafeRowsError(
            "alternate file-id retry became authorized"
        )
    if policy["alternate_endpoint_retry_authorized"] is not False:
        raise GlobalMammalSafeRowsError(
            "alternate endpoint retry became authorized"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name("." + destination.name + ".part")
    if destination.exists() or part.exists():
        raise GlobalMammalSafeRowsError(
            "refusing to overwrite prior Appendix 2 bytes"
        )

    request = Request(
        source["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-global-mammals-v1.23",
        },
    )
    opener = opener or build_opener(
        StripAuthorizationOnCrossOriginRedirect()
    )
    digest = hashlib.sha256()
    count = 0
    try:
        with opener.open(request, timeout=180) as response, part.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                count += len(chunk)
    except Exception as exc:
        if part.exists():
            part.unlink()
        raise GlobalMammalSafeRowsError(
            f"Appendix 2 exact transport failed: {type(exc).__name__}"
        ) from None

    if (
        count != int(source["expected_size_bytes"])
        or digest.hexdigest() != source["expected_sha256"]
    ):
        if part.exists():
            part.unlink()
        raise GlobalMammalSafeRowsError(
            "Appendix 2 exact byte identity verification failed"
        )
    os.replace(part, destination)


def _validate_firewall(
    firewall: Mapping,
    contract: Mapping,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if firewall.get("schema") != (
        "structural.global_mammals_appendix2_column_firewall.v1_22"
    ):
        raise GlobalMammalSafeRowsError(
            "unexpected v1.22 firewall schema"
        )
    if firewall.get("status") != (
        "APPENDIX2_COLUMNS_CLASSIFIED_BEFORE_ANY_DATA_ROW_ACCESS"
    ):
        raise GlobalMammalSafeRowsError("v1.22 firewall did not qualify")
    if firewall.get("candidate_id") != contract["candidate_id"]:
        raise GlobalMammalSafeRowsError("firewall candidate identity drift")
    if firewall.get("analysis_route") != "contaminated_macro_analysis_only":
        raise GlobalMammalSafeRowsError("firewall analysis-route drift")

    safe = tuple(firewall.get("safe_columns_in_source_order") or ())
    closed = tuple(
        firewall.get("closed_unneeded_columns_in_source_order") or ()
    )
    protected = tuple(
        firewall.get("protected_response_derived_columns_in_source_order")
        or ()
    )
    observed = tuple(firewall.get("observed_headers_in_order") or ())
    if safe != tuple(contract["safe_columns_in_source_order"]):
        raise GlobalMammalSafeRowsError("safe column set drift")
    if closed != tuple(contract["closed_unneeded_columns_in_source_order"]):
        raise GlobalMammalSafeRowsError("closed column set drift")
    if protected != tuple(
        contract["protected_response_derived_columns_in_source_order"]
    ):
        raise GlobalMammalSafeRowsError("protected column set drift")
    if len(observed) != 25 or len(set(observed)) != 25:
        raise GlobalMammalSafeRowsError("observed header universe drift")
    if set(safe) | set(closed) | set(protected) != set(observed):
        raise GlobalMammalSafeRowsError(
            "firewall does not partition exact header universe"
        )
    if set(safe) & (set(closed) | set(protected)):
        raise GlobalMammalSafeRowsError("safe firewall overlap")
    boundary = firewall.get("row_access_boundary") or {}
    if boundary.get(
        "safe_row_projection_authorized_after_this_firewall_is_committed"
    ) is not True:
        raise GlobalMammalSafeRowsError(
            "v1.22 does not authorize safe projection"
        )
    if boundary.get("closed_unneeded_row_values_authorized") is not False:
        raise GlobalMammalSafeRowsError(
            "closed row values became authorized"
        )
    if boundary.get(
        "protected_response_derived_row_values_authorized"
    ) is not False:
        raise GlobalMammalSafeRowsError(
            "protected response-derived row values became authorized"
        )
    if boundary.get("response_file_access_authorized") is not False:
        raise GlobalMammalSafeRowsError(
            "Appendix 1 response access became authorized"
        )
    return safe, closed, protected


def project_safe_rows(
    xlsx_path: Path,
    *,
    contract: Mapping,
    firewall: Mapping,
) -> tuple[str, dict]:
    safe, closed, protected = _validate_firewall(firewall, contract)
    source = contract["source"]

    header_audit = audit_workbook(
        xlsx_path,
        contract={
            "candidate_id": contract["candidate_id"],
            "analysis_route": contract["analysis_route"],
            "source": {
                "file_name": source["file_name"],
                "dryad_file_id": source["dryad_file_id"],
                "expected_size_bytes": source["expected_size_bytes"],
                "expected_sha256": source["expected_sha256"],
            },
            "prospective_safe_column_intent": list(safe),
            "prospective_forbidden_header_patterns": [],
            "header_audit_ceiling": {"next_action": "v1.23"},
        },
    )
    sheets = header_audit.get("sheets") or []
    if len(sheets) != 1:
        raise GlobalMammalSafeRowsError(
            "Appendix 2 workbook is not exact one-sheet support"
        )
    sheet = sheets[0]
    if sheet.get("sheet_name") != source["sheet_name"]:
        raise GlobalMammalSafeRowsError("Appendix 2 sheet name drift")
    if sheet.get("worksheet_member") != source["worksheet_member"]:
        raise GlobalMammalSafeRowsError(
            "Appendix 2 worksheet member drift"
        )
    if sheet.get("header_sha256") != source["expected_header_sha256"]:
        raise GlobalMammalSafeRowsError("Appendix 2 header SHA drift")
    headers = tuple(sheet.get("header_values") or ())
    if headers != tuple(firewall["observed_headers_in_order"]):
        raise GlobalMammalSafeRowsError(
            "Appendix 2 observed header order drift"
        )

    safe_index = {headers.index(column): column for column in safe}
    closed_indexes = {headers.index(column) for column in closed}
    protected_indexes = {headers.index(column) for column in protected}

    try:
        with zipfile.ZipFile(xlsx_path, "r") as zf:
            raw_sheet = zf.read(source["worksheet_member"])
            raw_shared = (
                zf.read("xl/sharedStrings.xml")
                if "xl/sharedStrings.xml" in zf.namelist()
                else b""
            )
    except zipfile.BadZipFile as exc:
        raise GlobalMammalSafeRowsError(
            "Appendix 2 is not a valid XLSX"
        ) from exc

    parsed_rows: list[dict[str, tuple[str, int | None]]] = []
    shared_needed: set[int] = set()
    data_rows_seen = 0
    closed_cells_seen = 0
    protected_cells_seen = 0

    for row_position, match in enumerate(ROW_RE.finditer(raw_sheet)):
        if row_position == 0:
            continue
        data_rows_seen += 1
        values: dict[str, tuple[str, int | None]] = {}
        for cell in CELL_RE.finditer(match.group("body")):
            attrs = (
                cell.group("attrs")
                if cell.group("attrs") is not None
                else cell.group("selfattrs") or b""
            )
            ref_raw = _attr(attrs, "r")
            if ref_raw is None:
                raise GlobalMammalSafeRowsError(
                    "worksheet data cell lacks reference"
                )
            ref = _decode_ascii_or_utf8(
                ref_raw,
                label="cell_reference",
            ).strip()
            column_index = _column_index_from_ref(ref)
            if column_index in closed_indexes:
                closed_cells_seen += 1
                continue
            if column_index in protected_indexes:
                protected_cells_seen += 1
                continue
            column = safe_index.get(column_index)
            if column is None:
                raise GlobalMammalSafeRowsError(
                    f"cell routed outside frozen header universe: {ref}"
                )
            text, shared_index = _decode_safe_cell_fragment(
                attrs=attrs,
                body=cell.group("body") or b"",
                cell_ref=ref,
            )
            if column in values:
                raise GlobalMammalSafeRowsError(
                    f"duplicate safe cell in row: {column}"
                )
            values[column] = (text, shared_index)
            if shared_index is not None:
                shared_needed.add(shared_index)
        parsed_rows.append(values)

    expected_rows = int(source["expected_data_row_count"])
    if data_rows_seen != expected_rows:
        raise GlobalMammalSafeRowsError(
            f"Appendix 2 data row count drift: {data_rows_seen}"
        )

    if shared_needed:
        if not raw_shared:
            raise GlobalMammalSafeRowsError(
                "safe shared-string cells exist but sharedStrings.xml is missing"
            )
        selected_shared = _selected_shared_strings(
            raw_shared,
            shared_needed,
        )
    else:
        selected_shared = {}

    output_rows = []
    null_counts = {column: 0 for column in safe}
    ids = []
    for row in parsed_rows:
        resolved: dict[str, str] = {}
        for column in safe:
            if column not in row:
                resolved[column] = ""
                null_counts[column] += 1
                continue
            text, shared_index = row[column]
            value = (
                selected_shared[shared_index]
                if shared_index is not None
                else text
            )
            resolved[column] = value
            if not str(value).strip():
                null_counts[column] += 1
        encoded = _validate_and_encode_row(
            resolved,
            safe_columns=safe,
        )
        ids.append(encoded[0])
        output_rows.append(encoded)

    if len(set(ids)) != len(ids):
        raise GlobalMammalSafeRowsError(
            "Appendix 2 safe ID values are not unique"
        )

    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(safe)
    writer.writerows(output_rows)
    csv_text = out.getvalue()

    id_digest = hashlib.sha256()
    for value in ids:
        id_digest.update(value.encode("utf-8"))
        id_digest.update(b"\n")

    receipt = {
        "schema": (
            "structural.global_mammals_appendix2_safe_rows_result.v1_23"
        ),
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "analysis_route": contract["analysis_route"],
        "source_file_sha256": source["expected_sha256"],
        "source_header_sha256": source["expected_header_sha256"],
        "safe_columns": list(safe),
        "safe_column_count": len(safe),
        "row_count": len(output_rows),
        "distinct_id_count": len(set(ids)),
        "routing_id_order_sha256": id_digest.hexdigest(),
        "safe_csv_sha256": sha256_text(csv_text),
        "safe_csv_bytes": len(csv_text.encode("utf-8")),
        "null_counts": null_counts,
        "safe_cell_values_decoded": len(output_rows) * len(safe),
        "safe_shared_string_entry_count_decoded": len(shared_needed),
        "closed_unneeded_cells_seen_opaque": closed_cells_seen,
        "closed_unneeded_cell_values_decoded": 0,
        "protected_response_derived_cells_seen_opaque": protected_cells_seen,
        "protected_response_derived_cell_values_decoded": 0,
        "Appendix_1_response_file_reopened": False,
        "biological_response_values_opened_in_v1_23": False,
        "counts_as_empirical_evidence": False,
        "counts_as_fresh_confirmation": False,
        "fresh_system_denominator_contribution": 0,
        "original_global_mammal_fresh_chain_restored": False,
        "safe_spatial_design_may_be_built": True,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return csv_text, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--firewall", type=Path, default=DEFAULT_FIREWALL)
    parser.add_argument("--safe-csv", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.global_mammals_appendix2_safe_rows_contract.v1_23"
        ):
            raise GlobalMammalSafeRowsError(
                "unexpected v1.23 contract schema"
            )
        if contract.get("status") != (
            "SAFE_ROW_PROJECTION_PREDECLARED_AFTER_V122_FIREWALL"
        ):
            raise GlobalMammalSafeRowsError(
                "v1.23 contract status drift"
            )
        with tempfile.TemporaryDirectory() as tmp:
            xlsx = Path(tmp) / contract["source"]["file_name"]
            _download_exact(
                xlsx,
                contract=contract,
                token=os.environ.get("DRYAD_TOKEN", ""),
            )
            safe_csv, receipt = project_safe_rows(
                xlsx,
                contract=contract,
                firewall=_load(args.firewall),
            )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ET.ParseError,
        zipfile.BadZipFile,
        GlobalMammalSafeRowsError,
    ) as exc:
        safe_csv = None
        receipt = {
            "schema": (
                "structural.global_mammals_appendix2_safe_rows_result.v1_23"
            ),
            "status": "HOLD_APPENDIX2_SAFE_ROW_PROJECTION_FAILED",
            "reason": str(exc),
            "closed_unneeded_cell_values_decoded": 0,
            "protected_response_derived_cell_values_decoded": 0,
            "Appendix_1_response_file_reopened": False,
            "biological_response_values_opened_in_v1_23": False,
            "counts_as_empirical_evidence": False,
            "counts_as_fresh_confirmation": False,
            "fresh_system_denominator_contribution": 0,
            "original_global_mammal_fresh_chain_restored": False,
            "safe_spatial_design_may_be_built": False,
        }
        code = 2
    else:
        code = 0

    if safe_csv is not None and args.safe_csv is not None:
        args.safe_csv.parent.mkdir(parents=True, exist_ok=True)
        args.safe_csv.write_text(safe_csv, encoding="utf-8")
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
