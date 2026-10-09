import importlib.util,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v237",R/"scripts/zenodo_camtrapasia_header_only_v1_237.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_header_only_reads_first_line_and_checks_md5():
    b=b"study,latitude,longitude,trap_nights\nprivate,12,50,30\n"
    h=m.header_only(b,len(b),hashlib.md5(b).hexdigest())
    assert h==["study","latitude","longitude","trap_nights"]
    assert "private" not in h
def test_wrong_file_hash_stops():
    b=b"species,mass\nRattus,3\n"
    try:m.header_only(b,len(b),"0"*32)
    except ValueError:pass
    else:raise AssertionError("Source hashes not enforced")
def test_restrictions_and_no_capture_file():
    x=json.loads((R/"development/camtrapasia_csv_header_contract_v1_237.json").read_text())
    assert x["prohibited_file"] not in m.FILES
    assert x["never_iterate_data_rows"] is True
    assert x["limits"]["admit_external_score_now"] is False
    assert all(v is False for v in x["policy"].values())
