import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from fox_hydra_dryad_source_v1_246 import receipt,DOI,NAMES
def fixture():
    ds={"identifier":DOI}
    vv={"_embedded":{"stash:versions":[
        {"versionNumber":1,"curationStatus":"Published",
         "_links":{"self":{"href":"/api/v2/versions/881"}}}]}}
    files={"total":2,"_embedded":{"stash:files":[
        {"path":s,"size":30000+k,"digest":str(k+1)*64,
         "_links":{"self":{"href":"/api/v2/files/"+str(992+k)}}}
        for k,s in enumerate(sorted(NAMES))]}}
    return ds,vv,files
def test_source_metadata_only():
    d=receipt(*fixture())
    assert d["source_version_id"]==881
    assert set(d["source_files"])==NAMES
    assert d["biological_data_rows_read"]==0
    assert d["new_independent_confirmatory_systems"]==0
    assert d["published_spatial_hydra_result_is_prior_art"]
def test_different_doi_stops():
    ds,v,f=fixture()
    ds["identifier"]="10.5061/dryad.wrong"
    with pytest.raises(ValueError,match="DOI"):receipt(ds,v,f)
def test_missing_source_or_bad_sha_stops():
    ds,v,f=fixture()
    f["_embedded"]["stash:files"][0]["digest"]="0"
    result=receipt(ds,v,f)
    assert result["status"]=="SOURCE_DIGEST_NOT_VERIFIED_HOLD_METADATA_ONLY"
    assert result["biological_data_rows_read"]==0
    ds,v,f=fixture()
    f["_embedded"]["stash:files"].pop()
    with pytest.raises(ValueError):receipt(ds,v,f)
