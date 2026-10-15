"""Original Fox 2017 method source fingerprint and API naming test only."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from fox2017_hydra_source_readiness_v1_247 import (
    published_versions,file_metadata,check_readme,FILES,digest_algorithm_from_publisher_hex)

def test_original_two_file_version_source_metadata():
    ver={"_embedded":{"stash:versions":[{
      "versionNumber":2,"curationStatus":"Published",
      "_links":{"self":{"href":"/api/v2/versions/194230"}}}]}}
    assert published_versions(ver)==[(2,194230)]
    expected=[
       {"path":n,"size":100,"digest":"a"*64,
        "_links":{"self":{"href":f"/api/v2/files/{100+i}"}}}
       for i,n in enumerate(sorted(FILES))]
    f=file_metadata({"total":2,"_embedded":{"stash:files":expected}})
    assert set(f)==FILES
    assert sorted(x["publisher_file_id"] for x in f.values())==[100,101]

def test_no_silent_alternative_file():
    data={"total":1,"_embedded":{"stash:files":[{"path":"other.csv"}]}}
    with pytest.raises(ValueError):file_metadata(data)

def test_do_not_open_biology_as_readme():
    with pytest.raises(ValueError):
        check_readme("data_for_Fox_et_el_2017_nature_ee.csv",
          {"publisher_file_id":23,"bytes":12,"sha256":"f"*64})

def test_unapproved_version_host_refused():
    vv={"_embedded":{"stash:versions":[{"versionNumber":1,
        "_links":{"self":{"href":"https://evil.example/api/v2/versions/1"}}}]}}
    with pytest.raises(ValueError):published_versions(vv)

def test_legacy_source_MD5_never_labelled_sha256():
    assert digest_algorithm_from_publisher_hex("b25b2ddd88e046ac58849a20a549e9e7")=="md5"
    assert digest_algorithm_from_publisher_hex("a39aec4a41c5fcb301203ee56f922b89")=="md5"
    assert digest_algorithm_from_publisher_hex("a"*64)=="sha256"
    with pytest.raises(ValueError):digest_algorithm_from_publisher_hex("not a publisher checksum")
    with pytest.raises(ValueError):digest_algorithm_from_publisher_hex("a"*40)
