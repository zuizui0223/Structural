"""Tests explicitly distinguish redetection from colonization and censoring."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from hopson_zero_spell_audit_v1_223 import spells_for_jar

def test_single_zero_between_positives():
    e,right,interrupted=spells_for_jar([(1,1),(4,0),(8,1)])
    assert len(e)==1 and e[0]["zero_count"]==1
    assert not e[0]["left_censored"]
    assert e[0]["days_from_last_positive_to_redetection"]==7
    assert (right,interrupted)==(0,0)

def test_multiple_zero_spells_and_right_censoring():
    e,right,interrupted=spells_for_jar([(1,1),(4,0),(8,0),(11,1),(15,0)])
    assert len(e)==1 and e[0]["zero_count"]==2
    assert right==1 and interrupted==0

def test_left_censored_start_is_not_recent_loss():
    e,right,interrupted=spells_for_jar([(1,0),(4,0),(8,1)])
    assert e[0]["left_censored"] and e[0]["zero_count"]==2
    assert e[0]["days_from_last_positive_to_redetection"] is None

def test_missing_breaks_spell_instead_of_imputing_absence():
    e,right,interrupted=spells_for_jar([(1,1),(4,0),(8,None),(11,0),(15,1)])
    assert interrupted==1
    assert e[0]["left_censored"]
    assert e[0]["zero_count"]==1

def test_duplicate_day_and_invalid_state_rejected():
    with pytest.raises(ValueError):spells_for_jar([(1,1),(1,0)])
    with pytest.raises(ValueError):spells_for_jar([(1,1),(4,2)])
