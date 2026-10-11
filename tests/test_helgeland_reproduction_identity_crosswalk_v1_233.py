"""Known-truth tests for 24-header/25-value author R rowname CSV."""
import csv,io,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_reproduction_identity_crosswalk_v1_233 import producers,blob
def test_extra_r_row_index_dropped_correctly():
    cols=["Year_ID_Location","Year_ID","ID","Year_Location","Year","Location","Island","Least_age","Least_age_sq","Least_hatchyear","filled","obs","capt","gene_new","Own_survival","estimated_pop_size","N","n","zNR","in_out","sex","N_nestlings","N_Recruits","r2s"]
    vals=["dummy","2008_1","1","2008_isle","2008","isle","28"]+["0"]*17
    raw=(";".join(cols)+"\n"+"1;"+";".join(vals)+"\n").encode()
    x=list(producers(raw))
    assert len(x)==1
    assert x[0]["ID"]=="1"
    assert x[0]["Year"]=="2008"
    assert x[0]["Island"]=="28"
    assert x[0]["N_nestlings"]=="0"
def test_fail_closed_on_column_count():
    cols=";".join(["ID","Year","Island","N_nestlings","N_Recruits"]+["x"+str(i) for i in range(19)])
    raw=(cols+"\n"+";".join(["1"]*24)+"\n").encode()
    with pytest.raises(ValueError,match="25 fields"):list(producers(raw))
def test_blobs_semantics():
    assert len(blob(b"example"))==40
