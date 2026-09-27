"""Byte-disciplined pilot router for the 318-island mammal stress test.

This evidence lane is not pristine confirmation: island-level response-derived
summaries were exposed only after the safe island split/reference design had
been frozen. The 1,474-species occurrence matrix itself remains sealed.

During burned-pilot routing this module may decode:
- schema rows 1/2/4;
- row A (ID) for every island, solely for routing;
- occurrence cells D:... only when ID is in the frozen pilot set.

Confirmatory and out-of-scope occurrence cells are never semantically decoded.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import html
import io
import re
from typing import Sequence
import xml.etree.ElementTree as ET
import zipfile


class MammalStressPilotRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class MammalStressPilotSurface:
    csv_text: str
    raw_surface_sha256: str
    pilot_species_universe: tuple[str, ...]
    pilot_species_universe_sha256: str
    pilot_species_universe_count: int
    pilot_islands_opened: int
    pilot_occurrence_values_parsed: int
    confirmatory_occurrence_values_parsed: int
    excluded_occurrence_values_parsed: int
    occurrence_rows_seen: int


MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _col_letters(ref: str) -> str:
    m = re.match(r"([A-Z]+)", ref)
    if not m:
        raise MammalStressPilotRouterError(f"invalid cell reference: {ref!r}")
    return m.group(1)


def _shared_string_blocks(raw: bytes) -> list[bytes]:
    return re.findall(br"<si(?:\s[^>]*)?>.*?</si>", raw, flags=re.S)


def _local_text(block: bytes) -> str:
    node = ET.fromstring(block)
    return "".join(
        (el.text or "")
        for el in node.iter()
        if el.tag.rsplit("}", 1)[-1] == "t"
    )


def _cell_ref_and_type(cell: bytes) -> tuple[str, str | None]:
    head = cell.split(b">", 1)[0] + b">"
    rm = re.search(br'\br="([^"]+)"', head)
    if not rm:
        raise MammalStressPilotRouterError("cell has no reference")
    tm = re.search(br'\bt="([^"]+)"', head)
    return (
        rm.group(1).decode("ascii"),
        tm.group(1).decode("ascii") if tm else None,
    )


def _decode_cell(
    cell: bytes,
    *,
    shared: list[bytes],
    label: str,
) -> str:
    ref, typ = _cell_ref_and_type(cell)
    vm = re.search(br"<v>(.*?)</v>", cell, flags=re.S)
    inline = re.search(br"<is>.*?<t[^>]*>(.*?)</t>.*?</is>", cell, flags=re.S)

    if typ == "s":
        if not vm:
            raise MammalStressPilotRouterError(f"shared-string cell lacks value: {label} {ref}")
        idx = int(vm.group(1))
        if not 0 <= idx < len(shared):
            raise MammalStressPilotRouterError(f"shared-string index out of range: {label} {ref}")
        return _local_text(shared[idx])
    if typ == "inlineStr":
        if not inline:
            raise MammalStressPilotRouterError(f"inline string lacks text: {label} {ref}")
        return html.unescape(inline.group(1).decode("utf-8"))
    if typ in (None, "str"):
        return html.unescape(vm.group(1).decode("utf-8")) if vm else ""
    raise MammalStressPilotRouterError(
        f"unexpected cell type in opened field: {label} {ref} type={typ!r}"
    )


def _sheet_xml_and_shared(
    workbook_bytes: bytes,
    *,
    sheet_name: str,
) -> tuple[bytes, list[bytes]]:
    with zipfile.ZipFile(io.BytesIO(workbook_bytes)) as zf:
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        relmap = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in rels.findall(PKG + "Relationship")
        }

        worksheet = None
        for s in wb.find(MAIN + "sheets"):
            if s.attrib["name"] == sheet_name:
                target = relmap[s.attrib[REL + "id"]].lstrip("/")
                if not target.startswith("xl/"):
                    target = "xl/" + target
                worksheet = zf.read(target)
                break
        if worksheet is None:
            raise MammalStressPilotRouterError(f"missing worksheet: {sheet_name}")

        shared_raw = (
            zf.read("xl/sharedStrings.xml")
            if "xl/sharedStrings.xml" in zf.namelist()
            else b""
        )
    return worksheet, _shared_string_blocks(shared_raw)


def _row_bytes(worksheet: bytes, row_number: int) -> bytes:
    m = re.search(
        rb'<row\b[^>]*\br="' + str(row_number).encode() + rb'"[^>]*>.*?</row>',
        worksheet,
        flags=re.S,
    )
    if not m:
        raise MammalStressPilotRouterError(f"missing worksheet row {row_number}")
    return m.group(0)


def _cells(row: bytes) -> list[bytes]:
    return re.findall(br"<c\b[^>]*>.*?</c>|<c\b[^>]*/>", row, flags=re.S)


def _decode_schema_headers(
    worksheet: bytes,
    shared: list[bytes],
    *,
    expected_species_headers_sha256: str,
    expected_species_count: int,
) -> tuple[str, ...]:
    row4 = _row_bytes(worksheet, 4)
    values: list[str] = []
    for cell in _cells(row4):
        value = _decode_cell(cell, shared=shared, label="schema row 4").strip()
        values.append(value)

    if len(values) != 3 + expected_species_count:
        raise MammalStressPilotRouterError(
            f"unexpected row4 cell count: {len(values)}"
        )
    if tuple(values[:3]) != ("ID", "Island", "Island_group"):
        raise MammalStressPilotRouterError(
            f"unexpected response metadata headers: {values[:3]!r}"
        )

    species = tuple(values[3:])
    if not all(species) or len(set(species)) != len(species):
        raise MammalStressPilotRouterError(
            "species headers must be nonblank and unique"
        )
    digest = hashlib.sha256(
        ("\n".join(species) + "\n").encode("utf-8")
    ).hexdigest()
    if digest != expected_species_headers_sha256:
        raise MammalStressPilotRouterError(
            "species-header fingerprint mismatch"
        )
    return species


def build_zenodo_318_mammal_stress_pilot_surface(
    *,
    workbook_bytes: bytes,
    pilot_island_ids: Sequence[str],
    confirmatory_island_ids: Sequence[str],
    expected_sheet_dimension: str = "A1:BDU322",
    expected_species_headers_sha256: str,
    expected_species_count: int = 1474,
    first_data_row: int = 5,
    last_data_row: int = 322,
    minimum_species_support_islands: int = 2,
) -> MammalStressPilotSurface:
    pilot_order = tuple(str(x) for x in pilot_island_ids)
    confirmatory = {str(x) for x in confirmatory_island_ids}
    pilot_set = set(pilot_order)

    if len(pilot_set) != len(pilot_order):
        raise MammalStressPilotRouterError("duplicate pilot island ID")
    if pilot_set & confirmatory:
        raise MammalStressPilotRouterError("pilot and confirmatory island IDs overlap")
    if minimum_species_support_islands < 2:
        raise MammalStressPilotRouterError(
            "minimum_species_support_islands must be >=2"
        )

    worksheet, shared = _sheet_xml_and_shared(
        workbook_bytes, sheet_name="occurrence"
    )

    dm = re.search(br'<dimension[^>]*ref="([^"]+)"', worksheet[:20000])
    if not dm or dm.group(1).decode("ascii") != expected_sheet_dimension:
        raise MammalStressPilotRouterError("occurrence sheet dimension drift")

    species = _decode_schema_headers(
        worksheet,
        shared,
        expected_species_headers_sha256=expected_species_headers_sha256,
        expected_species_count=expected_species_count,
    )

    pilot_matrix: dict[str, tuple[int, ...]] = {}
    rows_seen = 0
    pilot_values = 0
    confirmatory_values = 0
    excluded_values = 0

    for row_number in range(first_data_row, last_data_row + 1):
        row = _row_bytes(worksheet, row_number)
        cells = _cells(row)
        if len(cells) != 3 + expected_species_count:
            raise MammalStressPilotRouterError(
                f"unexpected cell count at row {row_number}: {len(cells)}"
            )
        rows_seen += 1

        first = cells[0]
        ref, _ = _cell_ref_and_type(first)
        if _col_letters(ref) != "A":
            raise MammalStressPilotRouterError(
                f"first cell at row {row_number} is not column A"
            )
        island_id = _decode_cell(
            first, shared=shared, label="routing island ID"
        ).strip()
        if not island_id:
            raise MammalStressPilotRouterError(
                f"blank routing island ID at row {row_number}"
            )

        if island_id in confirmatory:
            continue
        if island_id not in pilot_set:
            continue
        if island_id in pilot_matrix:
            raise MammalStressPilotRouterError(
                f"duplicate pilot island row: {island_id}"
            )

        targets: list[int] = []
        for cell in cells[3:]:
            value = _decode_cell(
                cell, shared=shared, label=f"pilot occurrence island {island_id}"
            ).strip()
            if value not in {"0", "1"}:
                raise MammalStressPilotRouterError(
                    f"unexpected pilot occurrence value {value!r} on island {island_id}"
                )
            targets.append(int(value))
            pilot_values += 1
        pilot_matrix[island_id] = tuple(targets)

    missing_pilot = [x for x in pilot_order if x not in pilot_matrix]
    if missing_pilot:
        raise MammalStressPilotRouterError(
            "missing frozen pilot islands: " + ", ".join(missing_pilot)
        )

    support = [0] * expected_species_count
    for targets in pilot_matrix.values():
        for j, value in enumerate(targets):
            support[j] += value

    kept_indices = tuple(
        j for j, count in enumerate(support)
        if count >= minimum_species_support_islands
    )
    kept_species = tuple(species[j] for j in kept_indices)
    if not kept_species:
        raise MammalStressPilotRouterError(
            "fixed pilot-supported species universe is empty"
        )

    species_digest = hashlib.sha256(
        ("\n".join(kept_species) + "\n").encode("utf-8")
    ).hexdigest()

    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["partition_unit", "block", "target"])
    for island_id in pilot_order:
        targets = pilot_matrix[island_id]
        for j in kept_indices:
            writer.writerow([island_id, island_id, str(targets[j])])

    text = out.getvalue()
    raw_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

    return MammalStressPilotSurface(
        csv_text=text,
        raw_surface_sha256=raw_digest,
        pilot_species_universe=kept_species,
        pilot_species_universe_sha256=species_digest,
        pilot_species_universe_count=len(kept_species),
        pilot_islands_opened=len(pilot_matrix),
        pilot_occurrence_values_parsed=pilot_values,
        confirmatory_occurrence_values_parsed=confirmatory_values,
        excluded_occurrence_values_parsed=excluded_values,
        occurrence_rows_seen=rows_seen,
    )
