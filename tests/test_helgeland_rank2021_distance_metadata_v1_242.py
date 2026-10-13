"""Source-only 2021 Ranke Dryad HAL metadata exact identity tests."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_rank2021_distance_metadata_v1_242 import version_ids,headers_only,DOI
def test_HAL_version_and_two_spatial_files():
    v={"_embedded":{"stash:versions":[{"versionNumber":1,"curationStatus":"Published",
        "_links":{"self":{"href":"/api/v2/versions/43212"}}}]}}
    f={"total":2,"_embedded":{"stash:files":[
        {"path":"island_distances.csv","size":1200,"digest":"abc"},
        {"path":"recruitment.csv","size":1300,"digest":"xyz"}]}}
    a=headers_only({"identifier":DOI},v,f)
    assert a["selected_published_version_id"]==43212
    assert a["candidate_filenames"]==["island_distances.csv"]
    assert not a["distance_matrix_or_breeding_location_coordinates_ACTUALLY_VERIFIED"]
    assert a["biological_outcome_rows_read"]==0
def test_wrong_DOI_rejected():
    vv={"_embedded":{"stash:versions":[{"versionNumber":1,"id":4}]}}
    with pytest.raises(ValueError,match="DOI"):
        headers_only({"identifier":"10.5061/dryad.fake"},vv,{"total":0,"_embedded":{"stash:files":[]}})
def test_pagination_cannot_silently_skip():
    vv={"_embedded":{"stash:versions":[{"versionNumber":1,"id":4}]}}
    with pytest.raises(ValueError,match="paginated"):
        headers_only({"identifier":DOI},vv,{"total":2,"_embedded":{"stash:files":[]}})
