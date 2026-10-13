"""Proof of only predeclared Dryad public UI transports and header-only parse."""
import sys,hashlib
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_pedigree_web_headers_v1_238 import exact_routes,interpret_header

def test_no_arbitrary_file_ids_or_external_host():
    assert exact_routes(3972793)==(
        "https://datadryad.org/downloads/file_stream/3972793",
        "https://datadryad.org/stash/downloads/file_stream/3972793")
    with pytest.raises(ValueError):exact_routes(0)
    with pytest.raises(ValueError):exact_routes("3972793")

def test_headers_not_actual_response_records():
    raw=b"ID\tnatal.island\tadult.island\tLRS\n123\t4\t5\t99\n"
    x=interpret_header(raw)
    assert x["n_columns"]==4
    assert x["columns"]==["ID","natal.island","adult.island","LRS"]
    assert "123" not in repr(x)

def test_non_tabular_data_cannot_be_scored():
    with pytest.raises(ValueError):interpret_header(b"unstructured")
