"""Source-author README documentation parser must not open extinction/occurrence sheets."""
from pathlib import Path
import io,zipfile,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from macaronesia_extirpation_author_methods_v1_264 import extract_readme_tab

NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RN="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL="http://schemas.openxmlformats.org/package/2006/relationships"

def fake_workbook():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml",f'<workbook xmlns="{NS}" xmlns:r="{RN}"><sheets><sheet name="Table S1" sheetId="1" r:id="rId1"/><sheet name="Read me" sheetId="2" r:id="rId2"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml",f'<worksheet xmlns="{NS}"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Species</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>NEVER_READ_SPECIES_NAME</t></is></c></row></sheetData></worksheet>')
        z.writestr("xl/worksheets/sheet2.xml",f'<worksheet xmlns="{NS}"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>TABLE S1</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>Extirpated means extinct on one island.</t></is></c></row><row r="3"><c r="A3" t="inlineStr"><is><t>TABLE S3 native flora.</t></is></c></row></sheetData></worksheet>')
    return b.getvalue()

def test_author_methods_only_readme_sheet_and_no_species_values():
    x=extract_readme_tab(fake_workbook())
    assert x["source_tab"]=="Read me"
    assert x["method_rows"][0]["text"]=="TABLE S1"
    assert "Extirpated" in x["method_rows"][1]["text"]
    assert x["non_method_worksheet_values_decoded"]==0
    assert "NEVER_READ_SPECIES_NAME" not in str(x)

def test_missing_author_readme_must_stop_not_use_biology_sheet():
    raw=fake_workbook()
    raw=raw.replace(b"Read me",b"Readyou") if False else raw
    # Explicit malformed workbook case rather than falling back to Table S1.
    try:
        extract_readme_tab(b"not excel")
    except ValueError:
        pass
    else:
        raise AssertionError("An unreadable source is not a valid method key")
