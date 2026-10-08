import io,json,zipfile,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("epmc227",ROOT/"scripts/europepmc_zhoushan_source_metadata_v1_227.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def _fake_docx_zip(member=None):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as f:
        f.writestr(member or m.MEMBER,b"arbitrary content never decoded as ecology")
    return b.getvalue()
def test_zip_central_metadata_and_named_member():
    t=m.catalogue(_fake_docx_zip())
    assert t["exact_expected_docx_member_present"]
    assert t["source_docx_contents_read"]==0
    assert t["exact_docx_member_uncompressed_bytes"]>0
def test_name_mismatch_stops_before_any_biological_read():
    try:m.catalogue(_fake_docx_zip("another.docx"))
    except ValueError:pass
    else:raise AssertionError("unfrozen supplementary file admitted")
def test_only_official_locus_and_no_response_authorized():
    c=json.loads((ROOT/"development/zhoushan_europepmc_official_source_contract_v1_227.json").read_text())
    assert m.is_official(c["source"])
    assert not m.is_official("https://myblog.example/data.zip")
    assert c["no_member_body_extracted"] is True
    assert c["source_island_species_identity_and_529_validation_still_unverified"] is True
    assert c["original_mammal_outcomes_reopened"] is False
    assert c["GEB_scientific_hold"] is True
