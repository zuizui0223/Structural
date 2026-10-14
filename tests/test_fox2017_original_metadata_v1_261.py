"""Synthetic publisher metadata fixtures only."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from fox2017_original_metadata_v1_261 import validate,NAMES,DOI
def fixture():
    d={"identifier":DOI}
    v={"_embedded":{"stash:versions":[
        {"versionNumber":2,"curationStatus":"Published",
         "_links":{"self":{"href":"/api/v2/versions/18101"}}}]}}
    files={"total":2,"_embedded":{"stash:files":[
        {"path":name,"size":50000+i,"digest":str(i+1)*64,
         "_links":{"self":{"href":f"/api/v2/files/{902+i}"}}}
        for i,name in enumerate(sorted(NAMES))]}}
    return d,v,files
def test_published_two_files_only():
    a=validate(*fixture())
    assert a["latest_version_id"]==18101
    assert len(a["source_file_metadata"])==2
    assert a["biological_rows_decoded"]==0
def test_no_wrong_source_file():
    d,v,f=fixture()
    f["_embedded"]["stash:files"].pop()
    f["total"]=1
    with pytest.raises(ValueError,match="file set"):
        validate(d,v,f)
def test_publisher_hash_required():
    d,v,f=fixture()
    f["_embedded"]["stash:files"][0]["digest"]="wrong"
    with pytest.raises(ValueError,match="hash"):
        validate(d,v,f)
def test_wrong_dataset_prohibited():
    d,v,f=fixture()
    d["identifier"]="10.5061/dryad.different"
    with pytest.raises(ValueError,match="DOI"):
        validate(d,v,f)
