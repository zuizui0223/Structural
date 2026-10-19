"""Synthetic XLSX only: source schema not colony/species census outcome values."""
import io
import sys
from pathlib import Path
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from jncc_seabird_comparative_source_preflight_v1_264 import scan_workbook

MAIN="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG="http://schemas.openxmlformats.org/package/2006/relationships"

def synthetic_xlsx():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("xl/workbook.xml",f"""<workbook xmlns="{MAIN}" xmlns:r="{REL}">
           <sheets><sheet name="Full census" sheetId="1" r:id="rId1"/>
           <sheet name="Notes" sheetId="2" state="hidden" r:id="rId2"/></sheets></workbook>""")
        z.writestr("xl/_rels/workbook.xml.rels",f"""<Relationships xmlns="{PKG}">
           <Relationship Id="rId1" Type="{REL}/worksheet" Target="worksheets/sheet1.xml"/>
           <Relationship Id="rId2" Type="{REL}/worksheet" Target="worksheets/sheet2.xml"/>
           </Relationships>""")
        z.writestr("xl/sharedStrings.xml",f"""<sst xmlns="{MAIN}" count="5" uniqueCount="5">
           <si><t>Site identity</t></si><si><t>Species</t></si>
           <si><t>Seabird 2000</t></si><si><t>Seabirds Count</t></si>
           <si><t>SECRET_RESPONSE_SPECIES</t></si></sst>""")
        z.writestr("xl/worksheets/sheet1.xml",f"""<worksheet xmlns="{MAIN}">
           <dimension ref="A1:E20000"/><sheetData>
           <row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>
           <c r="C1" t="s"><v>2</v></c><c r="D1" t="s"><v>3</v></c></row>
           <row r="8"><c r="B8" t="s"><v>4</v></c><c r="C8"><v>999</v></c></row>
           </sheetData></worksheet>""")
        z.writestr("xl/worksheets/sheet2.xml",f"""<worksheet xmlns="{MAIN}">
           <dimension ref="A1:C5"/><sheetData><row r="1"><c r="A1" t="inlineStr">
           <is><t>Legend</t></is></c></row></sheetData></worksheet>""")
    return b.getvalue()

def test_scan_reports_sheets_dimension_only_and_predefined_header_strings():
    r=scan_workbook(synthetic_xlsx())
    assert r["sheet_count"]==2
    first=r["sheets"][0]
    assert first["name"]=="Full census"
    assert first["approx_dimension_ref"]=="A1:E20000"
    assert any("Site identity" in s for s in first["header_only_text_preview"])
    assert any("Seabird" in s for s in first["header_only_text_preview"])
    assert "SECRET_RESPONSE_SPECIES" not in str(r)
    assert "999" not in str(r)
    assert r["biological_census_count_rows_read"]==0
    assert r["sheets"][1]["hidden"] is True

def test_truncated_or_nonzip_source_fails_closed():
    try:
        scan_workbook(b"not-a-spreadsheet")
    except ValueError as exc:
        assert "XLSX" in str(exc)
    else:
        raise AssertionError("A source-not-a-workbook cannot be accepted")

def test_source_scan_preserves_sheet_provenance_without_macros():
    r=scan_workbook(synthetic_xlsx())
    assert not r["contains_macro_code"]
    assert not r["contains_external_workbook_links"]
