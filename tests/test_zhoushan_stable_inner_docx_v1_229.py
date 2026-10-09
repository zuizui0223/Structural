import importlib.util,io,zipfile,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v229",ROOT/"scripts/zhoushan_docx_table_shapes_v1_229.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def _inner_docx():
    out=io.BytesIO()
    xml=('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:tbl><w:tr><w:tc><w:p><w:t>field outcome private</w:t></w:p></w:tc></w:tr>'
        '</w:tbl></w:body></w:document>')
    with zipfile.ZipFile(out,"w") as z:z.writestr("word/document.xml",xml)
    return out.getvalue()
def test_outer_zip_bytes_can_differ_but_inner_member_must_match(monkeypatch):
    inner=_inner_docx()
    monkeypatch.setattr(m,"DOCX_NAME","zoae006_suppl_supplementary_material.docx")
    monkeypatch.setattr(m,"DOCX_SIZE",len(inner))
    import zlib
    monkeypatch.setattr(m,"DOCX_CRC",zlib.crc32(inner))
    a=io.BytesIO()
    with zipfile.ZipFile(a,"w") as z:z.writestr(m.DOCX_NAME,inner)
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr(m.DOCX_NAME,inner)
        z.writestr("another.txt","extra package member")
    assert m.validate_outer(a.getvalue())==inner
    assert m.validate_outer(b.getvalue())==inner
    assert hashlib.sha256(a.getvalue()).hexdigest()!=hashlib.sha256(b.getvalue()).hexdigest()
    assert m.table_shapes(inner)["all_table_text_fields_read"]==0
def test_scientific_gate_still_closed():
    c=json.loads((ROOT/"development/zhoushan_stable_inner_docx_contract_v1_229.json").read_text())
    assert c["response_values_opened_before_gate"] is False
    assert c["no_biological_scoring_authorized"] is True
    assert c["no_original_IUCN_outcome_access"] is True
    assert c["immutable_member_identity"]["must_appear_exactly_once"] is True
