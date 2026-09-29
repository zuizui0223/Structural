from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_overlap_audit_uses_identity_not_response():
 x=json.loads((ROOT/"development/global_mammals_historical_overlap_contract_v1_37.json").read_text())
 assert x["historical_population"]["historically_analyzed_eligible_islands"]==309
 assert x["global_identity_projection"]["columns_opened"]==["ID","Island_name","CountryISO","Area"]
 assert x["global_identity_projection"]["protected_response_derived_columns_opened"]==0
 assert x["response_boundary"]["Appendix1_access_authorized"] is False
def test_species_overlap_is_not_used_to_choose_islands():
 x=json.loads((ROOT/"development/global_mammals_historical_overlap_contract_v1_37.json").read_text())
 assert x["species_overlap"]["not_an_independence_exclusion_criterion"] is True
 assert x["species_overlap"]["species_header_access_for_overlap_audit"] is False
def test_overlap_exclusion_has_no_replacement_or_repartition():
 x=json.loads((ROOT/"development/global_mammals_historical_overlap_contract_v1_37.json").read_text())
 e=x["exclusion_rule"]
 assert e["replacement_islands_allowed"] is False
 assert e["repartition_allowed"] is False
 assert e["remove_from_species_source_pool"] is True
