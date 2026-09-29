from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_reference_ladder_controls_region_and_generic_network_before_C():
 x=json.loads((ROOT/"development/global_mammals_reference_operator_contract_v1_33.json").read_text())
 assert "bioregion_categorical" in x["state_reference"]["R0"]
 assert "z_Current_isolation" in x["state_reference"]["R1_add"]
 assert "z_generic_neighbor_pressure" in x["generic_network_R2"]["R2_add"]
 assert x["future_species_conditioned_reference"]["R3_must_add"][1]=="training-only species_x_bioregion prevalence_or_membership"
 assert x["future_species_conditioned_reference"]["heldout_block_source_leakage_allowed"] is False
def test_graph_is_response_independent_and_separate_from_validation_blocks():
 x=json.loads((ROOT/"development/global_mammals_reference_operator_contract_v1_33.json").read_text())
 assert x["generic_network_R2"]["graph"]=="symmetrized k-nearest-neighbour"
 assert x["generic_network_R2"]["k_selection"].startswith("smallest integer k")
 assert x["response_boundary"]["Appendix1_access_authorized"] is False
