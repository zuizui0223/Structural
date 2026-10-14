"""Known truth for publisher file URL and header isolation."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from fox2017_original_md5_header_v1_262 import ORIGINAL,approved_urls,header_only
def test_known_publisher_source_ids():
    assert ORIGINAL["data_for_Fox_et_el_2017_nature_ee.csv"]["id"]==29820
    assert ORIGINAL["README_for_data_for_Fox_et_el_2017_nature_ee.txt"]["id"]==29821
    assert len(ORIGINAL)==2
def test_only_approved_three_publisher_urls():
    urls=approved_urls(29820)
    assert len(urls)==3
    assert all(x.startswith("https://datadryad.org/") for x in urls)
    with pytest.raises(ValueError):approved_urls("29820")
def test_only_header_is_semantically_accessed():
    x=header_only(b"metapop,patch,day,count\n12,2,4,789\n")
    assert x["fields"]==["metapop","patch","day","count"]
    assert "789" not in repr(x)
