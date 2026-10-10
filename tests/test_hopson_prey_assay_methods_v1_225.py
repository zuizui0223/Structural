"""Content-source and stop-gate synthetic regression tests. No live author biology."""
import hashlib
import re
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from hopson_prey_assay_methods_v1_225 import FILES,audit_source,ALLOWED_TERMS

def test_locked_R_match_and_bounded_excerpts():
    original=FILES["author_R"]
    raw=b"x\ntet = tet / sub.samp.vol\n density=1\n unrelated\n"
    try:
        FILES["author_R"]=(original[0],hashlib.md5(raw).hexdigest())
        result=audit_source("author_R",raw)
    finally:
        FILES["author_R"]=original
    assert result["total_lines"]==4
    assert len(result["method_keyword_lines"])==2
    assert all(len(x["text"])<=300 for x in result["method_keyword_lines"])

def test_md5_never_accepts_source_drift():
    with pytest.raises(ValueError):
        audit_source("author_R",b"not the pinned author source")

def test_keywords_include_assay_volume():
    for term in ("tet","dil.vol","sub.samp.vol","samp.vol","eupl"):
        assert ALLOWED_TERMS.search(term)
    assert not ALLOWED_TERMS.search("NONSENSE")
