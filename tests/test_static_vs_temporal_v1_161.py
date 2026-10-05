from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_161"

def test_current_status_separates_static_information_from_temporal_consequence():
    x=json.loads((ROOT/"development/current_status_v1_161.json").read_text())
    assert x["ecological_synthesis"]["core"]=="species occupancy changes the predictive role of source islands, but static source-network importance is not equivalent to temporal conservation consequence"
    assert x["independent_temporal_consequence_test"]["primary_supported"] is False
    assert x["independent_temporal_consequence_test"]["primary_C_minus_R2"]==0.00067423414692237
    assert x["ecological_synthesis"]["causal_rescue_or_extinction_established"] is False

def test_ebird_is_disabled_by_project_policy():
    x=json.loads((ROOT/"development/structural_active_priority_v1_161.json").read_text())
    assert x["project_decision"]["ebird_enabled"] is False
    assert x["project_decision"]["official_SED_acquisition_authorized"] is False
    assert x["project_decision"]["Dryad_species_archive_access_authorized"] is False
    assert x["next_scientific_event"].startswith("no active confirmatory system")

def test_synthesis_keeps_occurrence_and_consequence_distinct():
    s=(ROOT/"docs/STATIC_SOURCE_INFORMATION_VS_TEMPORAL_CONSEQUENCE_V1_161.md").read_text()
    assert "Occurrence information" in s
    assert "Conservation consequence" in s
    assert "structurally distinctive in a static source network without its loss carrying generalizable information" in s
    assert "do not pursue eBird" in s.lower()

def test_geb_v161_title_and_abstract_are_endpoint_specific():
    s=(GEB/"blinded_main_text.md").read_text()
    assert s.startswith("# When do source islands matter? Occupancy-dependent connectivity and the limits of static source leverage")
    abstract=s.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    assert len(abstract.split()) <= 300
    assert "static structural importance and future conservation consequence are not the same quantity" in abstract
    assert "did not improve heldout prediction of later contraction" in abstract

def test_geb_v161_main_text_is_within_target_and_references_all_cited():
    s=(GEB/"blinded_main_text.md").read_text()
    body,rest=s.split("## References",1)
    assert len(body.split()) < 5000
    refs=rest.split("## Data and Code Availability Statement",1)[0]
    entries=[x for x in refs.splitlines() if x.startswith("- ")]
    assert len(entries)==18
    for e in entries:
        m=re.match(r"-\s+([^,]+),.*?\((\d{4})\)",e)
        assert m,e
        first,year=m.group(1),m.group(2)
        assert year in body
        assert (f"{first} " in body or f"{first} &" in body or f"{first} et al." in body),(first,year)

def test_connectivity_validation_literature_is_integrated():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "Moilanen 2011" in s
    assert "Castorani et al. 2015" in s
    assert "Dallas et al. 2020" in s
    assert "Poli et al. 2020" in s
    assert "regional persistence" in s
    assert "separate endpoints" in s

def test_manifest_records_temporal_boundary_without_management_claim():
    x=json.loads((GEB/"submission_manifest.json").read_text())
    assert x["status"]=="GEB_STATIC_OCCURRENCE_VS_TEMPORAL_CONSEQUENCE_PREPARED"
    assert x["format"]["reference_count"]==18
    assert x["format"]["main_text_words_approx"]==4670
    assert x["endpoint_separation"]["temporal_source_loss_consequence"]=="independent BALA primary not supported"
    assert x["endpoint_separation"]["management_ranking_validated"] is False
    assert x["project_policy"]["ebird_active"] is False
    assert x["new_same_dataset_mechanism_search_authorized"] is False

def test_bala_numbers_and_mammal_ultrarare_numbers_unchanged():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "−0.5963" in s
    assert "20 degree- and edge-length-matched null graphs" in s
    assert "+0.000674" in s
    assert "−0.02130 to +0.02558" in s
