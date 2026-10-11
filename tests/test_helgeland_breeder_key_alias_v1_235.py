import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_breeder_key_alias_v1_235 import SHA,producer_identity_rows
def test_original_blobs_locked():
    assert SHA["presence"]=="c998367c55d0d88ec17e6d1dc2931a97c46aff55"
    assert len(SHA)==2
def test_r_index_is_not_ID():
    names=["Year_ID_Location","Year_ID","ID","Year_Location","Year","Location","Island","Least_age","Least_age_sq","Least_hatchyear","filled","obs","capt","gene_new","Own_survival","estimated_pop_size","N","n","zNR","in_out","sex","N_nestlings","N_Recruits","r2s"]
    d={k:"0" for k in names}
    d.update({"ID":"27","Year_ID":"2010_27","Year_ID_Location":"2010_27_isle","Year":"2010","Island":"20","Least_hatchyear":"2009"})
    b=(";".join(names)+"\n"+"15;"+";".join(d[k] for k in names)+"\n").encode()
    out=list(producer_identity_rows(b))
    assert out[0]["ID"]=="27"
    assert out[0]["Year_ID"]=="2010_27"
    assert "N_nestlings" not in out[0]
def test_malformed_column_width_stops():
    names=["Year_ID_Location","Year_ID","ID","Year","Least_hatchyear","Island"]+["x"+str(i) for i in range(18)]
    b=(";".join(names)+"\n"+";".join(["1"]*24)+"\n").encode()
    with pytest.raises(ValueError,match="R index"):list(producer_identity_rows(b))
