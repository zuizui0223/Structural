"""CSIC Macaronesian Excel: inspect source metadata and first-row headers only."""
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from macaronesia_extirpation_source_profile_v1_263 import inventory_workbook

WB_NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICE_REL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL="http://schemas.openxmlformats.org/package/2006/relationships"

def make_workbook():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml",f'''<?xml version="1.0"?>
        <workbook xmlns="{WB_NS}" xmlns:r="{OFFICE_REL}">
        <sheets><sheet name="Table S1" sheetId="1" r:id="rId1"/>
        <sheet name="Table S3" sheetId="3" r:id="rId3"/></sheets>
        </workbook>''')
        z.writestr("xl/_rels/workbook.xml.rels",f'''<?xml version="1.0"?>
        <Relationships xmlns="{PACKAGE_REL}">
        <Relationship Id="rId1" Target="worksheets/sheet1.xml"
         Type="{OFFICE_REL}/worksheet"/>
        <Relationship Id="rId3" Target="/xl/worksheets/sheet3.xml"
         Type="{OFFICE_REL}/worksheet"/>
        </Relationships>''')
        z.writestr("xl/worksheets/sheet1.xml",f'''<?xml version="1.0"?>
        <worksheet xmlns="{WB_NS}">
         <dimension ref="A1:C15"/>
         <sheetData>
          <row r="1"><c r="A1" t="inlineStr"><is><t>Taxon</t></is></c>
           <c r="B1" t="inlineStr"><is><t>Island</t></is></c>
           <c r="C1" t="inlineStr"><is><t>Extirpation</t></is></c></row>
          <row r="2"><c r="A2" t="inlineStr"><is><t>NEVER_COPY_SECRET_SPECIES</t></is></c>
           <c r="B2" t="inlineStr"><is><t>NEVER_COPY_RESPONSE</t></is></c></row>
         </sheetData>
        </worksheet>''')
        z.writestr("xl/worksheets/sheet3.xml",f'''<?xml version="1.0"?>
        <worksheet xmlns="{WB_NS}">
         <dimension ref="A1:B100"/>
         <sheetData><row r="1">
           <c r="A1" t="s"><v>0</v></c>
           <c r="B1" t="s"><v>1</v></c></row>
           <row r="2"><c r="A2" t="s"><v>2</v></c></row>
         </sheetData>
        </worksheet>''')
        z.writestr("xl/sharedStrings.xml",f'''<?xml version="1.0"?>
        <sst xmlns="{WB_NS}">
         <si><t>Accepted name</t></si><si><t>Native status</t></si>
         <si><t>NEVER_DECODE_SECRET_SPECIES_2</t></si>
        </sst>''')
    return b.getvalue()

def test_profile_reads_sheet_names_dimensions_and_headers_without_species_responses():
    r=inventory_workbook(make_workbook())
    assert r["sheet_count"]==2
    assert [s["sheet_name"] for s in r["sheets"]]==["Table S1","Table S3"]
    assert r["sheets"][0]["nominal_dimension"]=="A1:C15"
    assert r["sheets"][0]["first_row_headers"]==["Taxon","Island","Extirpation"]
    assert r["sheets"][1]["first_row_headers"]==["Accepted name","Native status"]
    assert r["sheets"][1]["nominal_max_row"]==100
    assert r["species_or_island_extirpation_observation_rows_read"]==0
    assert "NEVER" not in str(r)

def test_invalid_non_excel_html_or_truncated_zip_rejected():
    for garbage in (b"<html>blocked</html>",b"PK\x03\x04abc"):
        try:
            inventory_workbook(garbage)
        except (ValueError,zipfile.BadZipFile):
            pass
        else:
            raise AssertionError("Never accept HTML or truncated download as source workbook")

def test_duplicate_unsafe_workbook_schema_rejected():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("xl/workbook.xml",f'<workbook xmlns="{WB_NS}"><sheets/></workbook>')
    try:
        inventory_workbook(b.getvalue())
    except ValueError:
        pass
    else:
        raise AssertionError("Empty authored source is not an admissible native flora table")
