#!/usr/bin/env python3
"""Exact-download Appendix 2 and audit workbook/sheet/header metadata only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET
import zipfile
from urllib.request import Request, build_opener

from scripts.fetch_global_mammal_response_opaque_v1_17 import (
    StripAuthorizationOnCrossOriginRedirect,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/global_mammals_appendix2_header_audit_contract_v1_21.json"
)

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICE_REL_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
PACKAGE_REL_NS = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)
ROW_START_RE = re.compile(br"<(?:[A-Za-z_][\w.-]*:)?row(?:\s|>)")
ROW_END_RE = re.compile(br"</(?:[A-Za-z_][\w.-]*:)?row\s*>")
SI_START_RE = re.compile(br"<(?:[A-Za-z_][\w.-]*:)?si(?:\s|>)")
SI_END_RE = re.compile(br"</(?:[A-Za-z_][\w.-]*:)?si\s*>")


class GlobalMammalAppendix2AuditError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalMammalAppendix2AuditError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def _exact_download(
    output_path: Path,
    *,
    contract: dict,
    token: str,
    opener=None,
) -> dict:
    source = contract["source"]
    if not token or "\n" in token or "\r" in token:
        raise GlobalMammalAppendix2AuditError(
            "DRYAD_TOKEN is missing or malformed"
        )
    if contract["transport_policy"]["exact_file_only"] is not True:
        raise GlobalMammalAppendix2AuditError(
            "exact-file-only transport invariant drift"
        )
    if contract["transport_policy"][
        "alternate_file_id_retry_authorized"
    ] is not False:
        raise GlobalMammalAppendix2AuditError(
            "alternate file-id retry became authorized"
        )
    if contract["transport_policy"][
        "alternate_endpoint_retry_authorized"
    ] is not False:
        raise GlobalMammalAppendix2AuditError(
            "alternate endpoint retry became authorized"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    part = output_path.with_name("." + output_path.name + ".part")
    if output_path.exists() or part.exists():
        raise GlobalMammalAppendix2AuditError(
            "refusing to overwrite prior Appendix 2 bytes"
        )

    request = Request(
        source["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-global-mammals-v1.21",
        },
    )
    opener = opener or build_opener(
        StripAuthorizationOnCrossOriginRedirect()
    )
    digest = hashlib.sha256()
    count = 0
    try:
        with opener.open(request, timeout=180) as response, part.open(
            "wb"
        ) as out:
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
        raise GlobalMammalAppendix2AuditError(
            f"Appendix 2 exact transport failed: {type(exc).__name__}"
        ) from None

    observed_sha = digest.hexdigest()
    if (
        count != int(source["expected_size_bytes"])
        or observed_sha != source["expected_sha256"]
    ):
        if part.exists():
            part.unlink()
        raise GlobalMammalAppendix2AuditError(
            "Appendix 2 exact byte identity verification failed"
        )
    os.replace(part, output_path)
    return {
        "file_name": source["file_name"],
        "dryad_file_id": source["dryad_file_id"],
        "size_bytes": count,
        "sha256": observed_sha,
    }


def _normalize_sheet_target(target: str) -> str:
    text = str(target).replace("\\", "/")
    if text.startswith("/"):
        text = text.lstrip("/")
    elif not text.startswith("xl/"):
        text = str(PurePosixPath("xl") / text)
    norm = str(PurePosixPath(text))
    if ".." in PurePosixPath(norm).parts:
        raise GlobalMammalAppendix2AuditError(
            "worksheet relationship escapes xl/"
        )
    return norm


def _workbook_sheets(zf: zipfile.ZipFile) -> list[dict[str, str]]:
    required = {
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
    }
    missing = sorted(required - set(zf.namelist()))
    if missing:
        raise GlobalMammalAppendix2AuditError(
            "missing workbook metadata members: " + ", ".join(missing)
        )

    try:
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels_root = ET.fromstring(
            zf.read("xl/_rels/workbook.xml.rels")
        )
    except ET.ParseError as exc:
        raise GlobalMammalAppendix2AuditError(
            "invalid workbook metadata XML"
        ) from exc

    rels = {}
    for rel in rels_root:
        if _local(rel.tag) != "Relationship":
            continue
        rid = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rid and target:
            rels[rid] = _normalize_sheet_target(target)

    out = []
    for elem in workbook.iter():
        if _local(elem.tag) != "sheet":
            continue
        name = str(elem.attrib.get("name", "")).strip()
        rid = elem.attrib.get(f"{{{OFFICE_REL_NS}}}id")
        if rid is None:
            rid = elem.attrib.get("r:id")
        if not name or not rid or rid not in rels:
            raise GlobalMammalAppendix2AuditError(
                "invalid workbook sheet relationship"
            )
        out.append({
            "sheet_name": name,
            "relationship_id": rid,
            "worksheet_member": rels[rid],
        })
    if not out:
        raise GlobalMammalAppendix2AuditError(
            "workbook contains no sheets"
        )
    if len({x["sheet_name"] for x in out}) != len(out):
        raise GlobalMammalAppendix2AuditError(
            "duplicate workbook sheet names"
        )
    return out


def _first_row_bytes(
    zf: zipfile.ZipFile,
    member: str,
    *,
    chunk_size: int = 4096,
    maximum_scan_bytes: int = 4 * 1024 * 1024,
) -> tuple[bytes, int, tuple[bytes, ...]]:
    if member not in zf.namelist():
        raise GlobalMammalAppendix2AuditError(
            f"worksheet member missing: {member}"
        )

    buffer = bytearray()
    total_scanned = 0
    start_found = False

    with zf.open(member, "r") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            total_scanned += len(chunk)
            if total_scanned > maximum_scan_bytes:
                raise GlobalMammalAppendix2AuditError(
                    "first worksheet row not found within frozen scan ceiling"
                )
            buffer.extend(chunk)

            if not start_found:
                match = ROW_START_RE.search(buffer)
                if match is None:
                    if len(buffer) > 8192:
                        del buffer[:-8192]
                    continue
                preamble = bytes(buffer[:match.start()])
                namespace_attrs = tuple(
                    match.group(0)
                    for match in re.finditer(
                        br'xmlns(?::[A-Za-z_][\\w.-]*)?="[^"]+"',
                        preamble,
                    )
                )
                del buffer[:match.start()]
                start_found = True

            # Header rows should be ordinary non-self-closing row elements.
            tag_end = buffer.find(b">")
            if tag_end >= 0 and buffer[:tag_end].rstrip().endswith(b"/"):
                return (
                    bytes(buffer[:tag_end + 1]),
                    total_scanned,
                    namespace_attrs,
                )

            end = ROW_END_RE.search(buffer)
            if end is not None:
                return (
                    bytes(buffer[:end.end()]),
                    total_scanned,
                    namespace_attrs,
                )

    raise GlobalMammalAppendix2AuditError(
        f"worksheet has no complete first row: {member}"
    )


def _parse_row_fragment(
    row_bytes: bytes,
    namespace_attrs: Sequence[bytes],
) -> tuple[dict, set[int]]:
    # Namespace declarations normally live on the worksheet root. Reattach
    # only those declarations around the isolated first-row fragment so
    # prefixed row attributes can be parsed without reading later rows.
    wrapper = (
        b"<auditroot "
        + b" ".join(namespace_attrs)
        + b">"
        + row_bytes
        + b"</auditroot>"
    )
    try:
        root = ET.fromstring(wrapper)
        row = next(iter(root))
    except (ET.ParseError, StopIteration) as exc:
        raise GlobalMammalAppendix2AuditError(
            "first worksheet row XML is invalid"
        ) from exc
    if _local(row.tag) != "row":
        raise GlobalMammalAppendix2AuditError(
            "isolated worksheet fragment is not a row"
        )

    shared_indexes: set[int] = set()
    cells = []
    for cell in row:
        if _local(cell.tag) != "c":
            continue
        ref = str(cell.attrib.get("r", "")).strip()
        ctype = str(cell.attrib.get("t", "")).strip()
        value_elem = next(
            (x for x in cell if _local(x.tag) == "v"),
            None,
        )
        raw_value = (
            "" if value_elem is None or value_elem.text is None
            else value_elem.text
        )

        if ctype == "s":
            try:
                index = int(raw_value)
            except ValueError as exc:
                raise GlobalMammalAppendix2AuditError(
                    f"invalid shared-string header index at {ref}"
                ) from exc
            if index < 0:
                raise GlobalMammalAppendix2AuditError(
                    "negative shared-string header index"
                )
            shared_indexes.add(index)
            cells.append({
                "cell_reference": ref,
                "cell_type": "shared_string",
                "shared_string_index": index,
                "header_value": None,
            })
        elif ctype == "inlineStr":
            text_parts = [
                x.text or ""
                for x in cell.iter()
                if _local(x.tag) == "t"
            ]
            cells.append({
                "cell_reference": ref,
                "cell_type": "inline_string",
                "shared_string_index": None,
                "header_value": "".join(text_parts),
            })
        else:
            cells.append({
                "cell_reference": ref,
                "cell_type": ctype or "numeric_or_general",
                "shared_string_index": None,
                "header_value": raw_value,
            })

    return {
        "row_number": str(row.attrib.get("r", "")),
        "cell_count": len(cells),
        "cells": cells,
    }, shared_indexes


def _selected_shared_strings(
    raw: bytes,
    needed: set[int],
) -> dict[int, str]:
    if not needed:
        return {}

    selected = {}
    index = 0
    pos = 0
    while True:
        start = SI_START_RE.search(raw, pos)
        if start is None:
            break
        end = SI_END_RE.search(raw, start.end())
        if end is None:
            raise GlobalMammalAppendix2AuditError(
                "unterminated shared-string entry"
            )
        if index in needed:
            fragment = raw[start.start():end.end()]
            try:
                node = ET.fromstring(fragment)
            except ET.ParseError as exc:
                raise GlobalMammalAppendix2AuditError(
                    f"invalid selected shared-string XML at index {index}"
                ) from exc
            selected[index] = "".join(
                x.text or ""
                for x in node.iter()
                if _local(x.tag) == "t"
            )
        index += 1
        pos = end.end()

    missing = sorted(needed - set(selected))
    if missing:
        raise GlobalMammalAppendix2AuditError(
            "header references missing shared-string indexes: "
            + ", ".join(map(str, missing))
        )
    return selected


def _header_sha(values: list[str]) -> str:
    payload = "".join(f"{value}\n" for value in values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_workbook(
    xlsx_path: Path,
    *,
    contract: Mapping,
) -> dict:
    source = contract["source"]
    if sha256_file(xlsx_path) != source["expected_sha256"]:
        raise GlobalMammalAppendix2AuditError(
            "Appendix 2 file SHA mismatch before audit"
        )

    try:
        with zipfile.ZipFile(xlsx_path, "r") as zf:
            members = tuple(zf.namelist())
            if "[Content_Types].xml" not in members:
                raise GlobalMammalAppendix2AuditError(
                    "not a valid OOXML workbook"
                )
            sheets = _workbook_sheets(zf)

            row_meta = []
            needed_shared: set[int] = set()
            for sheet in sheets:
                row_bytes, scanned, namespace_attrs = _first_row_bytes(
                    zf,
                    sheet["worksheet_member"],
                )
                parsed, shared = _parse_row_fragment(
                    row_bytes,
                    namespace_attrs,
                )
                needed_shared |= shared
                row_meta.append({
                    **sheet,
                    **parsed,
                    "worksheet_decompressed_bytes_scanned_to_header_end": scanned,
                    "first_row_fragment_sha256": hashlib.sha256(
                        row_bytes
                    ).hexdigest(),
                })

            if needed_shared:
                if "xl/sharedStrings.xml" not in members:
                    raise GlobalMammalAppendix2AuditError(
                        "shared-string header indexes exist but sharedStrings.xml is missing"
                    )
                # Keep all nonselected shared strings as opaque bytes. Only
                # explicitly referenced header <si> fragments are XML-decoded.
                shared_raw = zf.read("xl/sharedStrings.xml")
                selected_shared = _selected_shared_strings(
                    shared_raw,
                    needed_shared,
                )
            else:
                selected_shared = {}

    except zipfile.BadZipFile as exc:
        raise GlobalMammalAppendix2AuditError(
            "Appendix 2 is not a valid ZIP/XLSX"
        ) from exc

    observed_headers = []
    sheets_out = []
    for sheet in row_meta:
        cells_out = []
        values = []
        for cell in sheet["cells"]:
            item = dict(cell)
            if item["cell_type"] == "shared_string":
                item["header_value"] = selected_shared[
                    item["shared_string_index"]
                ]
            value = str(item["header_value"])
            values.append(value)
            observed_headers.append(value)
            cells_out.append(item)
        sheets_out.append({
            "sheet_name": sheet["sheet_name"],
            "relationship_id": sheet["relationship_id"],
            "worksheet_member": sheet["worksheet_member"],
            "first_physical_row_number": sheet["row_number"],
            "header_cell_count": sheet["cell_count"],
            "header_values": values,
            "header_sha256": _header_sha(values),
            "header_cells": cells_out,
            "first_row_fragment_sha256": sheet[
                "first_row_fragment_sha256"
            ],
            "worksheet_decompressed_bytes_scanned_to_header_end": sheet[
                "worksheet_decompressed_bytes_scanned_to_header_end"
            ],
        })

    intended = tuple(contract["prospective_safe_column_intent"])
    forbidden_patterns = tuple(
        contract["prospective_forbidden_header_patterns"]
    )
    intended_presence = {
        column: column in observed_headers
        for column in intended
    }

    forbidden_observed = []
    for value in observed_headers:
        if (
            value.startswith("Richness_")
            or value.startswith("SIE_")
            or value.startswith("pSIE")
        ):
            forbidden_observed.append(value)

    return {
        "schema": (
            "structural.global_mammals_appendix2_header_audit_result.v1_21"
        ),
        "status": "APPENDIX2_WORKBOOK_HEADERS_AUDITED_DATA_ROWS_SEALED",
        "candidate_id": contract["candidate_id"],
        "analysis_route": contract["analysis_route"],
        "source": {
            "file_name": source["file_name"],
            "dryad_file_id": source["dryad_file_id"],
            "size_bytes": source["expected_size_bytes"],
            "sha256": source["expected_sha256"],
        },
        "xlsx_member_count": len(members),
        "sheet_count": len(sheets_out),
        "sheets": sheets_out,
        "header_shared_string_indexes_decoded": sorted(needed_shared),
        "header_shared_string_entry_count_decoded": len(needed_shared),
        "prospective_safe_column_intent_presence": intended_presence,
        "prospective_safe_columns_all_observed_somewhere": all(
            intended_presence.values()
        ),
        "prospective_forbidden_header_patterns": list(
            forbidden_patterns
        ),
        "observed_forbidden_pattern_headers": forbidden_observed,
        "appendix2_data_rows_semantically_opened": 0,
        "appendix2_data_cell_values_decoded": 0,
        "response_file_reopened": False,
        "biological_response_values_opened_in_v1_21": False,
        "safe_columns_authorized_for_row_access": False,
        "forbidden_columns_row_access_authorized": False,
        "counts_as_empirical_evidence": False,
        "counts_as_fresh_confirmation": False,
        "fresh_system_denominator_contribution": 0,
        "original_global_mammal_fresh_chain_restored": False,
        "next_action": contract["header_audit_ceiling"]["next_action"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit-receipt", type=Path)
    args = parser.parse_args()

    xlsx_path = None
    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.global_mammals_appendix2_header_audit_contract.v1_21"
        ):
            raise GlobalMammalAppendix2AuditError(
                "unexpected v1.21 audit contract schema"
            )
        if contract.get("status") != (
            "APPENDIX2_WORKBOOK_HEADER_ONLY_AUDIT_PREDECLARED"
        ):
            raise GlobalMammalAppendix2AuditError(
                "v1.21 audit contract status drift"
            )
        if contract["freshness_boundary"][
            "original_global_mammal_fresh_chain_closed_by_v1_20"
        ] is not True:
            raise GlobalMammalAppendix2AuditError(
                "v1.20 contamination boundary not acknowledged"
            )

        output = args.output or (
            ROOT / "build/global_mammals_v121/Appendix_2-dryad.xlsx"
        )
        xlsx_path = output
        transport = _exact_download(
            output,
            contract=contract,
            token=os.environ.get("DRYAD_TOKEN", ""),
        )
        result = audit_workbook(
            output,
            contract=contract,
        )
        result["transport"] = transport
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ET.ParseError,
        zipfile.BadZipFile,
        GlobalMammalAppendix2AuditError,
    ) as exc:
        result = {
            "schema": (
                "structural.global_mammals_appendix2_header_audit_result.v1_21"
            ),
            "status": "HOLD_APPENDIX2_HEADER_AUDIT_FAILED",
            "reason": str(exc),
            "appendix2_data_rows_semantically_opened": 0,
            "appendix2_data_cell_values_decoded": 0,
            "response_file_reopened": False,
            "biological_response_values_opened_in_v1_21": False,
            "safe_columns_authorized_for_row_access": False,
            "counts_as_empirical_evidence": False,
            "counts_as_fresh_confirmation": False,
            "fresh_system_denominator_contribution": 0,
            "original_global_mammal_fresh_chain_restored": False,
        }
        code = 2
    else:
        code = 0

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.audit_receipt is not None:
        args.audit_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.audit_receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
