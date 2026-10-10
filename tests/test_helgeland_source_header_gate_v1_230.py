"""Known-truth header parser tests; no external response reads."""
import hashlib
import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_source_header_gate_v1_230 import inspect_one,git_blob_sha,run

def spec(raw):
    return {"bytes":len(raw),"git_blob_sha1":git_blob_sha(raw),
            "required_header_fields":["Year","Island","ID"]}
def test_git_blob_length_fingerprint():
    raw=b"Year;Island;ID\n1994;20;123\n"
    assert git_blob_sha(raw)==hashlib.sha1(
        b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
def test_only_header_is_read_semantically(tmp_path):
    raw=b"Year;Island;ID\nTHIS_IS_OPAQUE;DO_NOT_PARSE;BAD\n"
    p=tmp_path/"presence.txt";p.write_bytes(raw)
    x=inspect_one(p,spec(raw))
    assert x["header_fields"]==["Year","Island","ID"]
    assert x["response_rows_decoded"]==0
def test_abort_on_source_or_schema_drift(tmp_path):
    raw=b"Year;Island;ID\n1;2;3\n"
    p=tmp_path/"presence.txt";p.write_bytes(raw)
    d=spec(raw);d["git_blob_sha1"]="0"*40
    with pytest.raises(ValueError,match="blob"):inspect_one(p,d)
    d=spec(raw);d["required_header_fields"].append("natal_origin")
    with pytest.raises(ValueError,match="schema"):inspect_one(p,d)
def test_do_not_prove_natal_source_from_id(tmp_path):
    raw=b"Year;Island;ID\n1994;20;123\n"
    p=tmp_path/"presence.txt";p.write_bytes(raw)
    assert inspect_one(p,spec(raw))["observed_directed_migrant_events_confirmed"] is False
