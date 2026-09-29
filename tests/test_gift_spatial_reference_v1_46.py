from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def test_gift_design_has_archipelago_blocks_and_stronger_r3():
    x=json.loads((ROOT/"development/gift_spatial_reference_contract_v1_46.json").read_text())
    assert x["validation_blocks"]["unit"]=="Weigelt archip"
    assert x["regional_pool"]["expected_primary_islands"]==503
    assert x["validation_blocks"]["expected_pilot_blocks"]==19
    assert x["validation_blocks"]["expected_confirmatory_blocks"]==59
    r3=x["future_species_conditioned_reference"]["R3_must_add"]
    assert "training-only species_x_regional_pool prevalence_or_membership" in r3
    assert x["future_species_conditioned_reference"]["heldout_archipelago_source_leakage_allowed"] is False

def test_regional_pool_selection_is_response_independent():
    x=json.loads((ROOT/"development/gift_spatial_reference_contract_v1_46.json").read_text())
    assert x["regional_pool"]["candidate_cell_width_degrees"]==[20,30,45,60,90]
    assert x["regional_pool"]["expected_selected_width_degrees"]==60
    assert x["response_boundary"]["species_composition_authorized"] is False

def test_mammal_final_reference_freeze_is_still_nonfresh():
    x=json.loads((ROOT/"development/global_mammals_reference_operator_freeze_v1_45.json").read_text())
    assert x["result"]["retained_islands"]==5401
    assert x["response_boundary"]["occurrence_values_opened"] is False
    assert x["response_boundary"]["fresh_status_restored"] is False
