"""Synthetic OOXML workbook relationship and schema audit, privacy / MD5 stop."""
import hashlib,importlib.util,zipfile
from pathlib import Path
import pytest

p=Path(__file__).with_name("audit_brisbane_canopy_ground_original_xlsx.py")
spec=importlib.util.spec_from_file_location("brisbane_original_beetle_workbook",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fake_xlsx(path):
    oox=m.OOXML
    cells=[
        '<row r="1">'
        '<c r="A1" t="s"><v>0</v></c>'
        '<c r="B1" t="s"><v>1</v></c>'
        '<c r="C1" t="s"><v>2</v></c>'
        '<c r="D1" t="s"><v>3</v></c>'
        '</row>'
    ]
    for i in range(80):
        k=i+2
        cells.append(f'<row r="{k}"><c r="A{k}" t="s"><v>4</v></c>'
                     f'<c r="B{k}"><v>{i%2}</v></c>'
                     f'<c r="C{k}"><v>{15+i%20}</v></c>'
                     f'<c r="D{k}"><v>{1+i%5}</v></c></row>')
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml",f'<workbook xmlns="{oox}" xmlns:r="{m.REL}"><sheets><sheet name="Traps and Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",'<Relationships xmlns="'+m.PKGREL+'"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml",f'<worksheet xmlns="{oox}"><sheetData>{"".join(cells)}</sheetData></worksheet>')
        ss="".join('<si><t>'+x+'</t></si>' for x in ["site","stratum","canopy_cover","species_count","SECRET_SITE_ID"])
        z.writestr("xl/sharedStrings.xml",f'<sst xmlns="{oox}">{ss}</sst>')

def test_excel_source_headers_and_80_publisher_rows_no_species_export(tmp_path):
    src=tmp_path/"source.xlsx"
    fake_xlsx(src)
    original=m.SOURCE_MD5
    m.SOURCE_MD5=hashlib.md5(src.read_bytes()).hexdigest()
    try:q=m.run(src,tmp_path/"out")
    finally:m.SOURCE_MD5=original
    assert q["source_original_md5_verified"]
    assert q["source_paper_reports_flight_intercept_trap_locations"]==80
    assert q["original_independent_forest_study_region_count"]==1
    assert q["source_sheets"][0]["OOXML_data_row_count"]==81
    assert q["source_sheets"][0]["source_first_row_field_headers_only_when_15_or_fewer"]==[
        "site","stratum","canopy_cover","species_count"]
    assert q["source_incidence_abundance_or_env_join_NOT_SCORED"]
    txt=(tmp_path/"out"/"brisbane_stone_beetle_original_workbook_schema.json").read_text()
    assert "SECRET_SITE_ID" not in txt
    assert not q["new_canopy_beetle_effect_scored"]


def test_md5_version_change_fails_before_any_original_data_read(tmp_path):
    p=tmp_path/"source.xlsx"
    fake_xlsx(p)
    with pytest.raises(ValueError,match="MD5_VERSION_MISMATCH"):
        m.parse_schema(p)
