import importlib.util,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/audit_frozen_prediction_headers_v1_195.py"

def load():
    s=importlib.util.spec_from_file_location("header195",SCRIPT)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_actual_header_has_two_dimensions_despite_three_dimensional_payload(tmp_path):
    m=load()
    p=tmp_path/"actual.f64le"
    p.write_bytes(m.ACTUAL+struct.pack("<II",3,4)+b"\0"*(3*4*2*8))
    r=m.inspect(p,m.ACTUAL,(3,4),(3,4,2))
    assert r["header_dims"]==[3,4]
    assert r["payload_shape"]==[3,4,2]

def test_null_header_has_three_dimensions(tmp_path):
    m=load()
    p=tmp_path/"null.f64le"
    p.write_bytes(m.NULL+struct.pack("<III",2,3,4)+b"\0"*(2*3*4*8))
    r=m.inspect(p,m.NULL,(2,3,4),(2,3,4))
    assert r["header_dims"]==[2,3,4]

def test_wrong_actual_three_dimension_header_is_rejected(tmp_path):
    m=load()
    p=tmp_path/"actual.f64le"
    p.write_bytes(m.ACTUAL+struct.pack("<II",3,4)+b"\0"*(3*4*2*8))
    import pytest
    with pytest.raises((m.Stop,ValueError,struct.error)):
        m.inspect(p,m.ACTUAL,(3,4,2),(3,4,2))
