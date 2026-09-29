from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_global_mammals_appendix2_header_v1_21.py"
CONTRACT = (
    ROOT / "development/global_mammals_appendix2_header_audit_contract_v1_21.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "global_mammals_appendix2_v121",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def synthetic_xlsx_bytes() -> bytes:
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets><sheet name="islands" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
  Target="worksheets/sheet1.xml"/>
</Relationships>"""
    sheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:x14ac="http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac">
 <sheetData>
  <row r="1" x14ac:dyDescent="0.25">
   <c r="A1" t="s"><v>0</v></c>
   <c r="B1" t="s"><v>1</v></c>
   <c r="C1" t="s"><v>2</v></c>
  </row>
  <row r="2">
   <c r="A2"><v>1</v></c>
   <c r="B2" t="s"><v>3</v></c>
   <c r="C2"><v>999999</v></c>
  </row>
 </sheetData>
</worksheet>"""
    shared = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 count="4" uniqueCount="4">
 <si><t>ID</t></si>
 <si><t>Lat_centroid</t></si>
 <si><t>Richness_native</t></si>
 <si><t>SECRET_ROW_VALUE</t></si>
</sst>"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="xml" ContentType="application/xml"/>
</Types>"""

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
        zf.writestr("xl/sharedStrings.xml", shared)
    return out.getvalue()


def synthetic_contract(payload: bytes):
    x = load_contract()
    x["source"] = dict(x["source"])
    x["source"]["expected_size_bytes"] = len(payload)
    x["source"]["expected_sha256"] = hashlib.sha256(payload).hexdigest()
    return x


def test_contract_keeps_global_mammal_route_nonfresh_after_v119_failure():
    x = load_contract()
    assert x["analysis_route"] == "contaminated_macro_analysis_only"
    assert x["freshness_boundary"][
        "original_global_mammal_fresh_chain_closed_by_v1_20"
    ] is True
    assert x["freshness_boundary"]["v1_21_does_not_restore_freshness"] is True
    assert x["freshness_boundary"]["quarantine_reentry_authorized"] is False
    ceiling = x["header_audit_ceiling"]
    assert ceiling["appendix2_data_rows_semantically_opened"] == 0
    assert ceiling["response_file_reopened"] is False
    assert ceiling["counts_as_fresh_confirmation"] is False
    assert ceiling["fresh_system_denominator_contribution"] == 0


def test_synthetic_header_audit_decodes_only_row1_and_selected_shared_strings(
    tmp_path: Path,
):
    module = load_module()
    payload = synthetic_xlsx_bytes()
    path = tmp_path / "Appendix_2-dryad.xlsx"
    path.write_bytes(payload)

    out = module.audit_workbook(
        path,
        contract=synthetic_contract(payload),
    )

    assert out["status"] == (
        "APPENDIX2_WORKBOOK_HEADERS_AUDITED_DATA_ROWS_SEALED"
    )
    assert out["sheet_count"] == 1
    assert out["sheets"][0]["sheet_name"] == "islands"
    assert out["sheets"][0]["first_physical_row_number"] == "1"
    assert out["sheets"][0]["header_values"] == [
        "ID",
        "Lat_centroid",
        "Richness_native",
    ]
    assert out["header_shared_string_indexes_decoded"] == [0, 1, 2]
    assert out["header_shared_string_entry_count_decoded"] == 3
    assert out["observed_forbidden_pattern_headers"] == [
        "Richness_native"
    ]
    assert out["appendix2_data_rows_semantically_opened"] == 0
    assert out["appendix2_data_cell_values_decoded"] == 0
    assert out["response_file_reopened"] is False
    assert out["biological_response_values_opened_in_v1_21"] is False
    assert out["safe_columns_authorized_for_row_access"] is False

    rendered = json.dumps(out, sort_keys=True)
    assert "SECRET_ROW_VALUE" not in rendered
    assert "999999" not in rendered


def test_namespace_prefixed_header_row_attribute_is_parseable(tmp_path: Path):
    module = load_module()
    payload = synthetic_xlsx_bytes()
    path = tmp_path / "test.xlsx"
    path.write_bytes(payload)
    out = module.audit_workbook(
        path,
        contract=synthetic_contract(payload),
    )
    first = out["sheets"][0]
    assert first["header_cell_count"] == 3
    assert [x["cell_reference"] for x in first["header_cells"]] == [
        "A1", "B1", "C1"
    ]


def test_wrong_xlsx_identity_stops_before_header_semantics(tmp_path: Path):
    module = load_module()
    payload = synthetic_xlsx_bytes()
    path = tmp_path / "test.xlsx"
    path.write_bytes(payload)
    contract = synthetic_contract(payload)
    contract["source"]["expected_sha256"] = "0" * 64
    with pytest.raises(
        module.GlobalMammalAppendix2AuditError,
        match="file SHA mismatch before audit",
    ):
        module.audit_workbook(path, contract=contract)


def test_only_header_referenced_shared_string_indexes_are_decoded(tmp_path: Path):
    module = load_module()
    payload = synthetic_xlsx_bytes()
    path = tmp_path / "test.xlsx"
    path.write_bytes(payload)
    out = module.audit_workbook(
        path,
        contract=synthetic_contract(payload),
    )
    assert 3 not in out["header_shared_string_indexes_decoded"]
    assert "SECRET_ROW_VALUE" not in json.dumps(out)


def test_ooxml_relationship_target_is_normalized_before_escape_check():
    module = load_module()
    assert module._normalize_sheet_target(
        "worksheets/sheet1.xml"
    ) == "xl/worksheets/sheet1.xml"
    assert module._normalize_sheet_target(
        "/xl/worksheets/sheet1.xml"
    ) == "xl/worksheets/sheet1.xml"
    assert module._normalize_sheet_target(
        "../xl/worksheets/sheet1.xml"
    ) == "xl/worksheets/sheet1.xml"


def test_ooxml_relationship_that_really_escapes_xl_is_rejected():
    module = load_module()
    with pytest.raises(
        module.GlobalMammalAppendix2AuditError,
        match="escapes xl/",
    ):
        module._normalize_sheet_target("../worksheets/sheet1.xml")
