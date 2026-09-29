from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_gift_eligibility_is_frozen_before_response():
 x=json.loads((ROOT/"development/gift_metadata_eligibility_contract_v1_28.json").read_text())
 assert x["response_access"]["species_composition_allowed"] is False
 assert x["overlap_rule"]["remove_overlap_was_false_at_metadata_retrieval"] is True
 assert x["block_rule"]["minimum_confirmatory_blocks"]==6
 assert x["reference_requirement"]["R3_must_include_species_x_regional_pool"] is True
 assert x["species_response_authorized"] is False
