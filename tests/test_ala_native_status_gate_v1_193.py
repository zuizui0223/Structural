from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/audit_ala_mammal_native_status_v1_193.py"
CONTRACT=ROOT/"development/global_mammals_ala_native_status_gate_v1_193.json"

def load():
    spec=importlib.util.spec_from_file_location("tax193",SCRIPT)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def test_author_exclusions_parse_only_named_sections():
    m=load()
    t='prefix\n## remove invasives\nx <- c("Rattus rattus","Dama dama")\n## remove marine mammals\ny <- c("Dugong dugon")\nausisles.mamala.df3 <-'
    rules=[{"reason":"invasive","start":"## remove invasives","end":"## remove marine mammals"},{"reason":"marine","start":"## remove marine mammals","end":"ausisles.mamala.df3 <-"}]
    got=m.author_exclusions(t,rules)
    assert got["rattus rattus"]=="invasive" and got["dugong dugon"]=="marine"
    assert "prefix" not in got

def test_conservative_exclusions_and_65_species_count_frozen_before_pair():
    c=json.loads(CONTRACT.read_text())
    assert c["expected_outcome_without_opening_pairs"]["provisionally_retained_taxa"]==65
    assert c["expected_outcome_without_opening_pairs"]["excluded_by_author_source"]==3
    assert set(c["author_taxon_exclusions"]["expected_excluded_overlap"])=={"Dama.dama","Rattus.rattus","Sus.scrofa"}
    assert set(c["conservative_additional_exclusions"])=={"Potorous.platyops","Rattus.exulans"}
    assert c["response_boundary"]["external_species_x_island_positive_pairs_opened"]==0
    assert c["response_boundary"]["original_heldout_labels_opened"]==0
    assert c["response_boundary"]["biological_scoring_authorized"] is False

def test_no_future_repair_from_positive_counts():
    c=json.loads(CONTRACT.read_text())
    assert c["matching"]["never_promote_invasive_or_extinct_species_by_event_counts"] is True
    assert c["interpretive_boundary"]["site_specific_nativeness_verified"] is False
    assert c["interpretive_boundary"]["future_nonzero_pair_evidence_requires_separate_exact_frozen_protocol"] is True
