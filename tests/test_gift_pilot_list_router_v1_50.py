from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_router_keeps_species_closed():
 x=json.loads((ROOT/"development/gift_pilot_list_router_contract_v1_50.json").read_text())
 assert x["router"]["expected_pilot_list_ID_count"]==147
 assert x["router"]["expected_confirmatory_list_ID_count"]==596
 assert x["geological_origin_gate"]["currently_resolved"] is False
 assert x["response_boundary"]["species_API_authorized_now"] is False
def test_first_response_can_only_use_pilot_lists():
 x=json.loads((ROOT/"development/gift_pilot_list_router_contract_v1_50.json").read_text())
 b=x["future_first_response_boundary"]
 assert b["allowed_list_IDs"]=="exact frozen pilot list_ID vector only"
 assert "596 confirmatory" in b["forbidden_list_IDs"]
 assert b["arguments"]["floristic_group"]=="native"
