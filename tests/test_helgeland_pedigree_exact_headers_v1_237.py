"""Synthetic-only identity and HAL URL safety tests."""
import hashlib,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_pedigree_exact_headers_v1_237 import file_id,download_href,source_files,header_line,audit_metadata

def test_file_id_and_authority_validation():
    v={"_links":{"self":{"href":"/api/v2/files/901"},
                  "stash:download":{"href":"/api/v2/files/901/download"}}}
    assert file_id(v)==901
    assert download_href(v,901)=="https://datadryad.org/api/v2/files/901/download"
    v["_links"]["self"]["href"]="https://attack.example/api/v2/files/901"
    with pytest.raises(ValueError):file_id(v)

def test_no_unadvertised_download_endpoint():
    x={"_links":{"self":{"href":"/api/v2/files/901"}}}
    with pytest.raises(ValueError,match="advertised"):download_href(x,901)

def test_metadata_must_match_version_and_sha():
    a={"file_sha256":{"LRS.txt":"f"*64},"bytes":{"LRS.txt":7}}
    v={"path":"LRS.txt","size":7,"digest":"f"*64,
        "_links":{"self":{"href":"/api/v2/files/901"},
                  "stash:download":{"href":"/api/v2/files/901/download"}}}
    z=audit_metadata({"total":1,"_embedded":{"stash:files":[v]}},a)
    assert z["LRS.txt"]["file_id"]==901
    v["digest"]="0"*64
    with pytest.raises(ValueError):audit_metadata({"total":1,"_embedded":{"stash:files":[v]}},a)

def test_no_raw_response_rows_in_header():
    txt=b"ID\tnatal.island\tLRS\nSENSITIVE_VALUE\t999\t888\n"
    x=header_line(txt)
    assert x["fields"]==["ID","natal.island","LRS"]
    assert "SENSITIVE_VALUE" not in repr(x)
