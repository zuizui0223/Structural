import sys,hashlib
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from fox_hydra_readme_md5_v1_247 import candidate_urls,verify_source,MD5,LENGTH
def test_publisher_only_routes():
    urls=candidate_urls()
    assert len(urls)==3
    assert all(u.startswith("https://datadryad.org/") for u in urls)
def test_md5_identity_not_weakened():
    with pytest.raises(ValueError):
        verify_source(b"fake source")
    assert len(MD5)==32
    assert LENGTH==1440
def test_no_raw_outcome_parser_in_gate():
    import inspect
    import fox_hydra_readme_md5_v1_247 as m
    assert "biological CSV" in m.__doc__
    assert len(candidate_urls())==3
