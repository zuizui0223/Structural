#!/usr/bin/env python3
"""Extract only historical island identity fields from the consumed 318-island workbook."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

from structural.zenodo_318_mammal_pilot_router import (
    MammalStressPilotRouterError,
    _cell_ref_and_type,
    _cells,
    _col_letters,
    _decode_cell,
    _row_bytes,
    _sheet_xml_and_shared,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "development/global_mammals_historical_overlap_gate_contract_v0_90.json"


class HistoricalIdentityError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_contract(path: Path) -> dict:
    x = json.loads(path.read_text(encoding="utf-8"))
    if x.get("schema") != "structural.global_mammals_historical_overlap_gate_contract.v0_90":
        raise HistoricalIdentityError("unexpected overlap contract schema")
    return x


def extract_identity(workbook: Path, output: Path, contract: dict) -> dict:
    spec = contract["historical_identity_input"]
    if workbook.stat().st_size != int(spec["size_bytes"]):
        raise HistoricalIdentityError("historical workbook size mismatch")
    if sha256_file(workbook) != spec["sha256"]:
        raise HistoricalIdentityError("historical workbook SHA-256 mismatch")

    raw = workbook.read_bytes()
    try:
        worksheet, shared = _sheet_xml_and_shared(raw, sheet_name=spec["sheet"])
    except MammalStressPilotRouterError as exc:
        raise HistoricalIdentityError(str(exc)) from exc

    dm = re.search(br'<dimension[^>]*ref="([^"]+)"', worksheet[:20000])
    if not dm or dm.group(1).decode("ascii") != spec["dimension"]:
        raise HistoricalIdentityError("historical occurrence sheet dimension drift")

    header_cells = _cells(_row_bytes(worksheet, int(spec["header_row"])))
    if len(header_cells) < 3:
        raise HistoricalIdentityError("historical header has fewer than three cells")
    opened_headers = []
    for expected_col, cell in zip(("A", "B", "C"), header_cells[:3]):
        ref, _ = _cell_ref_and_type(cell)
        if _col_letters(ref) != expected_col:
            raise HistoricalIdentityError("historical metadata column order drift")
        opened_headers.append(
            _decode_cell(cell, shared=shared, label="historical identity header").strip()
        )
    if opened_headers != spec["allowed_fields"]:
        raise HistoricalIdentityError(
            f"unexpected historical identity headers: {opened_headers!r}"
        )

    first_row, last_row = map(int, spec["data_rows_1based"])
    rows: list[tuple[str, str, str]] = []
    seen_ids: set[str] = set()
    for row_number in range(first_row, last_row + 1):
        cells = _cells(_row_bytes(worksheet, row_number))
        if len(cells) < 3:
            raise HistoricalIdentityError(f"historical row {row_number} has fewer than three cells")
        opened: list[str] = []
        for expected_col, cell in zip(("A", "B", "C"), cells[:3]):
            ref, _ = _cell_ref_and_type(cell)
            if _col_letters(ref) != expected_col:
                raise HistoricalIdentityError(
                    f"historical row {row_number} metadata order drift"
                )
            opened.append(
                _decode_cell(cell, shared=shared, label="historical island identity").strip()
            )
        island_id, island, group = opened
        if not island_id or not island:
            raise HistoricalIdentityError(f"blank historical ID/name at row {row_number}")
        if island_id in seen_ids:
            raise HistoricalIdentityError(f"duplicate historical island ID {island_id}")
        seen_ids.add(island_id)
        rows.append((island_id, island, group))

    if len(rows) != 318:
        raise HistoricalIdentityError(f"expected 318 historical islands, observed {len(rows)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["historical_id", "historical_island", "historical_group"])
        w.writerows(rows)

    return {
        "schema": "structural.zenodo_318_identity_extraction_result.v0_90",
        "status": "historical_identity_only_extracted",
        "historical_islands": len(rows),
        "distinct_historical_ids": len(seen_ids),
        "opened_fields": ["ID", "Island", "Island_group"],
        "species_header_fields_semantically_opened": 0,
        "species_occurrence_cells_semantically_opened": 0,
        "output_sha256": sha256_file(output),
        "counts_as_empirical_evidence": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workbook", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = p.parse_args()

    try:
        result = extract_identity(args.workbook, args.output, load_contract(args.contract))
        code = 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError,
            HistoricalIdentityError, MammalStressPilotRouterError) as exc:
        result = {
            "schema": "structural.zenodo_318_identity_extraction_result.v0_90",
            "status": "STOP",
            "reason": str(exc),
            "species_header_fields_semantically_opened": 0,
            "species_occurrence_cells_semantically_opened": 0,
            "counts_as_empirical_evidence": False,
        }
        code = 2

    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
