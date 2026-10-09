import json,importlib.util,io,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v232",ROOT/"scripts/zhoushan_site_first_field_v1_232.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_only_first_table_header_and_site_first_field_authorized():
    a=json.loads((ROOT/"development/zhoushan_site_identity_column_contract_v1_232.json").read_text())
    assert a["allow_read_only"]["table_index"]==0
    assert a["allow_read_only"]["maximum_rows"]==40
    assert a["allow_read_only"]["maximum_columns"]==12
    assert a["taxon_incidence_values_opened"] is False
    assert a["site_coords_or_polygon_identity_for_39_not_verified"] is True
    assert a["external_prediction_scoring_allowed"] is False
    assert a["GEB_submission_authorized"] is False
def test_docx_source_is_frozen_before_any_first_column_decode():
    assert m.SHA=="ec1d1d0a5dbe3f0cee955dfe4018e678a48a796d5135b2311888d47aad9ecd64"
    assert "word/document.xml" in open(ROOT/"scripts/zhoushan_site_first_field_v1_232.py").read()
