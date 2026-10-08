import importlib.util,io,zipfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("zh224",ROOT/"scripts/zhoushan_supplement_source_metadata_v1_224.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_source_bytes_are_only_zip_central_directory():
    f=io.BytesIO()
    with zipfile.ZipFile(f,"w") as z:
        z.writestr("[Content_Types].xml","<t/>")
        z.writestr("word/document.xml","<body>potential field species outcomes</body>")
    x=m.member_metadata(f.getvalue())
    assert x["document_xml_bytes_read"]==0
    assert x["table_or_field_response_values_read"]==0
def test_official_source_and_freshwater_hard_limit():
    assert m.safe_url(m.URL)
    assert not m.safe_url("https://example.org/source.docx")
    r=json.loads((ROOT/"development/field_mammal_survey_preintake_v1_224.json").read_text())
    assert r["priority"]["marine_land_bridge_islands"]==39
    assert r["priority"]["island_species_source_values_opened"] is False
    assert r["priority"]["eligible_for_GEB_confirmation_now"] is False
    assert r["freshwater_comparator"]["freshwater_is_not_saline_original_mammal_graph_population"] is True
    assert all(v is True for v in r["hard_guards"].values())
