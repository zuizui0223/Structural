import importlib.util,io,json,csv,hashlib
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("audit207",ROOT/"scripts/audit_four_patch_header_v1_207.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_source_link_restricts_one_exact_metadata_identity():
    f={"_embedded":{"stash:files":[{"path":m.FIXED_NAME,"size":m.FIXED_SIZE,
       "digest":m.FIXED_MD5,"digestType":"md5","_links":{"self":{"href":"/api/v2/files/719"}}}]}}
    assert m._source_url(f)[1]==719
    f["_embedded"]["stash:files"][0]["digest"]="incorrect"
    with pytest.raises(ValueError):m._source_url(f)
def test_bad_download_url_forbidden_before_network(monkeypatch):
    with pytest.raises(ValueError):m._request("https://example.com/data.csv",1000)
    with pytest.raises(ValueError):m._request("https://datadryad.org/api/v2/files/719/download/extra",1000)
def test_header_gate_exacts_expected_patch_fields(monkeypatch):
    header=["Day","metapop","disp.rate","pp.g.l"]+[f"Eupl.{i}" for i in range(1,5)]+[f"Tet.pres{i}" for i in range(1,5)]
    b=(",".join(header)+"\n").encode()+b"?"*(m.FIXED_SIZE-len(",".join(header))-1)
    monkeypatch.setattr(m,"FIXED_MD5",hashlib.md5(b).hexdigest())
    assert m.header_only(b)==header
    bad=["index"]+header
    v=(",".join(bad)+"\n").encode()+b"?"*(m.FIXED_SIZE-len(",".join(bad))-1)
    monkeypatch.setattr(m,"FIXED_MD5",hashlib.md5(v).hexdigest())
    with pytest.raises(ValueError):m.header_only(v)
def test_scope_is_not_scoring():
    x=json.loads((ROOT/"development/four_patch_header_contract_v1_207.json").read_text())
    assert x["science_boundary"]["no_outcome_rows_interpreted"] is True
    assert x["science_boundary"]["fresh_confirmatory"] is False
    assert x["science_boundary"]["eBird"] is False
