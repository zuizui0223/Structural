from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_gift_pilot_contract_never_authorizes_confirmatory_lists():
 x=json.loads((ROOT/"development/gift_pilot_response_contract_v1_54.json").read_text())
 assert x["routing"]["pilot_list_IDs"]==147
 assert x["routing"]["confirmatory_list_IDs"]==596
 assert x["routing"]["confirmatory_list_ID_may_be_requested"] is False
 assert x["species_universe"]["m"]==5
 assert x["evidence_boundary"]["confirmatory_response_authorized"] is False

def test_gift_pilot_script_filters_high_confidence_native_and_unions_lists():
 s=(ROOT/"scripts/run_gift_pilot_response_v1_54.R").read_text()
 assert 'native==1 & questionable==0 & quest_native==0' in s
 assert 'confirmatory list_ID returned during pilot' in s
 assert 'GIFT::GIFT_checklists_raw' in s
 assert 'floristic_group="native"' in s
 assert 'confirmatory_list_IDs_requested=0L' in s

def test_request_is_one_shot_and_confirmatory_sealed():
 x=json.loads((ROOT/"development/gift_pilot_response_request_v1_55.json").read_text())
 assert x["pilot_response_authorized"] is True
 assert x["confirmatory_response_authorized"] is False
 assert x["one_shot"] is True
