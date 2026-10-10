"""v1.228 metadata-only schema test; no biological measurements opened."""
import io,sys,csv
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from hopson_prey_volume_schema_v1_228 import classify,audit
def test_all_four_semantic_flag_states():
    assert classify(.3,0,0)=="both_zero_undiluted"
    assert classify(.3,2.7,.1)=="both_positive_diluted"
    assert classify(.3,2.7,0)=="dilution_positive_subsample_zero"
    assert classify(.3,0,.1)=="dilution_zero_subsample_positive"
def test_invalid_metadata_rejected_as_category():
    assert classify(0,0,0)=="invalid_volume"
    assert classify(-.3,0,0)=="invalid_volume"
    assert classify(.3,float("nan"),.1)=="invalid_nonfinite"
def test_audit_does_not_inspect_species_columns():
    import hopson_prey_volume_schema_v1_228 as mod
    old=mod.EXPECTED
    try:
        mod.EXPECTED=3
        b=("date,day,jar.no,samp.vol,dil.vol,sub.samp.vol,eupl,tet\n"
           "x,1,1,0.3,0,0,NOT_A_COUNT,NOT_A_COUNT\n"
           "x,4,1,0.3,3,0,NOT_A_COUNT,NOT_A_COUNT\n"
           "x,7,1,0.3,3,0.1,NOT_A_COUNT,NOT_A_COUNT\n").encode()
        r=audit(b)
    finally:
        mod.EXPECTED=old
    assert r["rows_outside_v227_frozen_rules"]==1
    assert r["status"]=="STOP_V227_ASSAY_DOMAIN_MISMATCH"
    assert not r["raw_eupl_tet_values_used"]
