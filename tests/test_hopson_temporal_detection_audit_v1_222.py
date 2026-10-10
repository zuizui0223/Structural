"""Exact source-safe synthetic checks for zero detection != colonization."""
import csv,io,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from hopson_temporal_detection_audit_v1_222 import layout_index,rows_locked,optional_count,intish

def test_expected_layout_header():
    raw=b"jar.no,metapop.no,patch.no,trt,time.block\n1,1,1,sw,1\n"
    assert list(rows_locked(raw,["jar.no","metapop.no","patch.no","trt","time.block"]))[0]["trt"]=="sw"
    with pytest.raises(ValueError):
        list(rows_locked(raw,["bad"]))

def test_missing_detection_and_zero_not_occupancy():
    assert optional_count("0","eupl")==0
    assert optional_count("NA","eupl") is None
    assert optional_count("","eupl") is None
    assert optional_count("1","eupl")==1
    with pytest.raises(ValueError):optional_count("-2","eupl")

def test_full_synthetic_14x15_layout():
    rows=["jar.no,metapop.no,patch.no,trt,time.block"]
    assignment={1:("sw",1),2:("sw",1),3:("sw",1),4:("sw",1),
                5:("nn",1),6:("nn",1),7:("nn",1),
                8:("sw",2),9:("sw",2),10:("sw",2),
                11:("nn",2),12:("nn",2),13:("nn",2),14:("nn",2)}
    for m,(trt,block) in assignment.items():
        for patch in range(1,16):
            jar=(m-1)*15+patch
            rows.append(f"{jar},{m},{patch},{trt},{block}")
    raw=("\n".join(rows)+"\n").encode()
    assert len(layout_index(raw))==210
    with pytest.raises(ValueError):layout_index(raw.replace(b"210,14,15,nn,2",b"210,14,14,nn,2"))

def test_integer_guards():
    assert intish("0","day")==0
    with pytest.raises(ValueError):intish("1.1","day")
