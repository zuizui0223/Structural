import json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("field250",R/"scripts/camtrapasia_four_island_field_positives_v1_250.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_hard_frozen_original_study_and_taxon_counts():
 c=json.loads((R/"development/camtrapasia_field_positive_protocol_v1_250.json").read_text())
 assert sum(z["expected_study_count"] for z in c["precommitted_field_panel"]["four_prechosen_natural_island_candidates"])==78
 assert c["precommitted_field_panel"]["distinct_heldout_original_blocks_expected"]==3
 assert c["precommitted_field_panel"]["no_negative_occurrence_inference"] is True
 assert c["precommitted_field_panel"]["records_definition"].startswith("Positive independent photo-record")
 assert all(z is False for z in c["safeguards"].values())
def test_domestic_status_is_not_assumed_wild():
 assert "yes" in m.DOMESTIC and "true" in m.DOMESTIC
 assert "no" in m.SAFE_WILD and "false" in m.SAFE_WILD
 assert "" not in m.SAFE_WILD
 assert m.DOMESTIC.isdisjoint(m.SAFE_WILD)
def test_dot_normalization_follows_original_188_not_fuzzy():
 assert m.canon("Sus.scrofa")==m.canon("Sus scrofa")
 assert m.canon("Sus scrofa ferus")!=m.canon("Sus scrofa")
