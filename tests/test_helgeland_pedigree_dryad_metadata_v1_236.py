"""Synthetic API metadata source lock, no published reproductive records."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_pedigree_dryad_metadata_v1_236 import audit,FILES,versions,files
def fixture():
    ds={"identifier":"10.5061/dryad.qfttdz0sx"}
    vv={"_embedded":{"stash:versions":[{"id":88,"versionNumber":1,"versionStatus":"published"}]}}
    fs={"_embedded":{"stash:files":[{"id":j,"path":name,"size":100+j} for j,name in enumerate(sorted(FILES))]}}
    return ds,vv,fs
def test_five_files_and_version():
    r=audit(*fixture())
    assert set(r["exact_five_file_metadata"])==FILES
    assert r["version_id"]==88
    assert r["biological_rows_semantically_read"]==0
def test_missing_pedigree_file_stops():
    a,b,c=fixture()
    c["_embedded"]["stash:files"].pop()
    with pytest.raises(ValueError,match="five"):audit(a,b,c)
def test_changed_doi_stops():
    a,b,c=fixture();a["identifier"]="10.5061/dryad.other"
    with pytest.raises(ValueError,match="DOI"):audit(a,b,c)

def test_dryad_hal_version_self_href_numeric_id():
    vv={"_embedded":{"stash:versions":[
        {"_links":{"self":{"href":"/api/v2/versions/207850"}},
          "versionNumber":1,"curationStatus":"Published","publicationDate":"2025-03-25"}
    ]}}
    assert versions(vv)[0]["id"]==207850
    assert versions(vv)[0]["versionNumber"]==1
