from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("audit",ROOT/"scripts/preflight_four_patch_metadata_v1_206.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_endpoint_guard_prevents_binary_download(monkeypatch):
    for p in ("/api/v2/files/3/download","/api/v2/versions/100/download",
              "https://datadryad.org/api/v2/versions/100/files"):
        try: m.get_json(p)
        except ValueError: pass
        else: raise AssertionError("Data URL was not blocked: "+p)
def test_fixture_exact_doi_file_and_version():
    dataset={"identifier":m.DOI,"versionNumber":1,
       "_links":{"stash:version":{"href":"/api/v2/versions/456"}}}
    files={"_embedded":{"stash:files":[{"path":m.NAME,"size":147732,
       "digest":"aa","digestType":"md5"}]}}
    r=m.validate(dataset,files)
    assert r["status"]=="PASS_EXACT_DRYAD_FILE_METADATA_ONLY"
    assert r["biological_response_rows_read"]==0
    files["_embedded"]["stash:files"][0]["path"]="another.csv"
    try:m.validate(dataset,files)
    except ValueError: pass
    else:raise AssertionError("Mismatched identity not stopped")
def test_scientific_evidence_boundary():
    x=json.loads((ROOT/"development/four_patch_dryad_metadata_request_v1_206.json").read_text())
    assert x["published_description"]["independent_treatment_cell_replicates"]==1
    assert x["future_response_access_authorized"] is False
    assert x["original_global_mammal_biology_replication"] is False
    assert x["never_treat_patches_or_days_as_independent_treatment_replicates"]
    assert x["eBird"] is False and x["ALA_replay"] is False
