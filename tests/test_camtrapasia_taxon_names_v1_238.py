import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v238",R/"scripts/camtrapasia_taxon_only_v1_238.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_original_R_style_species_tokens_canonical():
 assert m.clean("Sus.scrofa")==m.clean("Sus scrofa")
 assert m.clean("Sus_scrofa")==m.clean("Sus scrofa")
 assert m.clean("Sus scrofa ferus")!=m.clean("Sus scrofa")
def test_source_name_only_and_hard_no_response():
 z=json.loads((R/"development/camtrapasia_taxon_name_contract_v1_238.json").read_text())
 assert z["external_species_traits"]["allowed_columns"]==["class","binomial_verified","taxonomic_level"]
 assert z["original_frozen_529"]["sha256"]==m.ORIGINAL_SHA
 assert z["research_firewall"]["no_capture_or_species_site_abundance_rows"] is True
 assert z["research_firewall"]["no_mammal_original_heldout_values"] is True
 assert all(v is False for v in z["safeguards"].values())
