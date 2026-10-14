import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ranke2021_exact_pairs_header_v1_243 import urls,file_list,file_id,LOCK

def test_public_publisher_exact_routes():
    assert len(urls(193))==3
    assert all(x.startswith("https://datadryad.org/") for x in urls(193))
def test_author_file_id_no_external_source():
    assert file_id({"_links":{"self":{"href":"/api/v2/files/12345"}}})==12345
    with pytest.raises(ValueError):file_id({"_links":{"self":{"href":"https://fake.example/api/v2/files/123"}}})
def test_source_byte_metadata_exact_match():
    e={"_embedded":{"stash:files":[
        {"path":n,"size":size,"digest":sha,
         "_links":{"self":{"href":"/api/v2/files/"+str(j+100)}}}
        for j,(n,(size,sha)) in enumerate(LOCK.items())]},"total":2}
    assert len(file_list(e))==2
    e["_embedded"]["stash:files"][0]["digest"]="bad"
    with pytest.raises(ValueError):file_list(e)
