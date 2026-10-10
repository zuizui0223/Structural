import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_two_year_resight_v1_232 import classify
def test_retained_migrant_recorded_twice():
    assert classify({(1994,1,"nest"),(1995,2,"capt"),(1996,2,"obs")},1994,2)=="same_destination_seen_t2"
def test_secondary_dispersal_record():
    assert classify({(1994,1,"nest"),(1995,2,"capt"),(1996,3,"obs")},1994,2)=="different_destination_seen_t2"
def test_unknown_not_mortality():
    assert classify({(1994,1,"nest"),(1995,2,"capt")},1994,2)=="unknown_second_followup"
def test_multiple_t2_islands_ambiguous():
    assert classify({(1994,1,"nest"),(1995,2,"capt"),(1996,2,"obs"),(1996,3,"capt")},1994,2)=="ambiguous_second_followup"
