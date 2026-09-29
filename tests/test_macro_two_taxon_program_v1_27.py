from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
def test_program_keeps_evidence_classes_separate():
 x=load("development/macro_two_taxon_program_v1_27.json")
 assert x["evidence_classes"]["global_mammals_5592"]["fresh_confirmatory"] is False
 assert x["evidence_classes"]["boreal_19island_beetles"]["primary_supported"] is False
 assert x["evidence_classes"]["GIFT_native_angiosperms"]["species_composition_opened"] is False
 assert x["GIFT_response_authorized"] is False
def test_reference_and_leakage_are_strong():
 x=load("development/macro_two_taxon_program_v1_27.json")
 assert "training-only species_x_regional_pool membership_or_prevalence" in x["reference_ladder_requirement"]["R3_must_include"]
 assert "leave-one-heldout-block-out" in x["leakage_rule"]
def test_gift_first_stage_is_metadata_only():
 c=load("development/gift_metadata_freeze_contract_v0_89.json")
 assert c["call"]["list_set_only"] is True
 assert c["call"]["floristic_group"]=="native"
 assert c["pilot_response_authorized"] is False
 s=(ROOT/"scripts/freeze_gift_metadata_v0_89.R").read_text()
 assert "list_set_only = TRUE" in s
 assert "species composition was returned" in s
