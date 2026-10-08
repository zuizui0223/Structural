import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v230",ROOT/"scripts/compare_zhoushan_taxa_v1_230.py")
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
def test_published_species_roster_and_identity_contract():
    x=json.loads((ROOT/"development/zhoushan_published_taxa_gate_v1_230.json").read_text())
    assert len(x["published_species_names"])==18
    assert len({v.norm(t) for t in x["published_species_names"]})==18
    assert x["frozen_mammal_manifest"]["species"]==529
    assert x["frozen_mammal_manifest"]["sha256"]==v.HASH
    assert x["field_incidence_read"] is False
    assert x["original_mammal_heldout_values_read"] is False
    assert x["GEB_submission_authorized"] is False
def test_no_fuzzy_taxon_rescue():
    assert v.norm(" Muntiacus   reevesi ")=="muntiacus reevesi"
    assert v.norm("Rattus norvegicus")!=v.norm("Rattus losea")
