import json,io,zipfile,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v228",ROOT/"scripts/zhoushan_docx_table_shapes_v1_228.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_table_shapes_never_read_xml_text():
    doc=io.BytesIO()
    content=('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:tbl><w:tr><w:tc><w:p><w:r><w:t>protected incidence 1</w:t></w:r></w:p></w:tc>'
        '<w:tc><w:p><w:r><w:t>species name</w:t></w:r></w:p></w:tc></w:tr>'
        '<w:tr><w:tc><w:p/></w:tc><w:tc><w:p/></w:tc></w:tr></w:tbl></w:body></w:document>')
    with zipfile.ZipFile(doc,"w") as z:
        z.writestr("word/document.xml",content)
        z.writestr("[Content_Types].xml","no cell data")
    a=m.table_shapes(doc.getvalue())
    assert a["table_count"]==1
    assert a["tables"][0]["rows"]==2
    assert a["tables"][0]["first_row_cells"]==2
    assert a["all_table_text_fields_read"]==0
    assert "protected incidence" not in json.dumps(a)
def test_frozen_identity_and_future_scientific_hold():
    p=json.loads((ROOT/"development/zhoushan_docx_table_geometry_contract_v1_228.json").read_text())
    assert p["required_outer_zip_sha256"]==m.OUTER_SHA
    assert p["required_docx_crc32"]=="8874d873"
    assert p["no_observation_rows_read"] is True
    assert p["no_automatic_admission_if_table_shape_matches"] is True
    assert p["no_GEB_submission_promotion"] is True
