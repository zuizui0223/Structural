from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_120"

def load(path):
    return json.loads((ROOT/path).read_text())

def test_ultrarare_primary_and_topology_are_prospectively_supported():
    x=load("development/global_mammals_ultrarare_result_freeze_v1_119.json")
    assert x["species_layer"]["pilot_presence_range"]==[1,4]
    assert x["species_layer"]["species"]==529
    assert x["primary_presence_opportunity"]["point_C_minus_R3"]==-0.5962586684916777
    assert x["primary_presence_opportunity"]["bootstrap_ci95_high"]<0
    assert x["primary_presence_opportunity"]["supported"] is True
    assert x["secondary_topology_specificity"]["point_actualC_minus_mean_rewiredC"]<0
    assert x["secondary_topology_specificity"]["bootstrap_ci95_high"]<0
    assert x["secondary_topology_specificity"]["actual_C_better_than_n_of_20_nulls_on_presence_metric"]==20
    assert x["secondary_topology_specificity"]["supported"] is True

def test_rare96_nonreplication_is_retained():
    x=load("development/global_mammals_sealed_species_result_freeze_v1_97.json")
    assert x["species_layer"]["pilot_presence_range"]==[5,12]
    assert x["species_layer"]["species"]==96
    assert x["P1_primary"]["supported"] is False
    assert x["P4_topology_specificity"]["supported"] is False
    assert x["P2_constraint_signature"]["presence_point"]<0
    assert x["P2_constraint_signature"]["absence_point"]>0

def test_original79_actual_adjacency_is_not_topology_specific():
    x=load("development/global_mammals_original79_topology_audit_freeze_v1_119.json")
    assert x["population"]["species"]==79
    assert x["actual_vs_rewired"]["all_cells"]["actual_minus_mean_rewired"]>0
    assert x["actual_vs_rewired"]["all_cells"]["bootstrap_ci95_low"]>0
    assert x["actual_vs_rewired"]["all_cells"]["actual_better_than_n_of_20_nulls"]==0
    assert x["interpretation"]["actual_topology_specificity_supported"] is False

def test_broad_end_is_nonestimable_not_negative_evidence():
    x=load("development/global_mammals_sealed_broad_species_pilot_terminal_v1_112.json")
    assert x["result"]["selected_species"]==0
    assert x["same_dataset_retry_with_wider_broad_threshold_authorized"] is False
    assert x["counts_as_empirical_support_or_non_support"] is False

def test_current_status_describes_regime_dependence_not_monotonicity():
    x=load("development/current_status_v1_119.json")
    assert x["global_mammal_occupancy_layers"]["ultrarare_1_4"]["primary_supported"] is True
    assert x["global_mammal_occupancy_layers"]["rare_5_12"]["overall_supported"] is False
    assert x["global_mammal_occupancy_layers"]["exploratory_13_plus"]["actual_better_than_nulls"]=="0/20"
    assert x["revised_ecological_synthesis"]["formal_monotonic_or_unimodal_law_established"] is False
    assert x["revised_ecological_synthesis"]["causal_dispersal_or_rescue_established"] is False

def test_active_priority_closes_same_dataset_mining():
    x=load("development/structural_active_priority_v1_119.json")
    prohibited="\n".join(x["do_not"])
    assert "open another species layer" in prohibited
    assert "widen the failed near-ubiquitous broad-species threshold" in prohibited
    assert "search alternative occupancy cutpoints" in prohibited
    assert "claim monotonic rarity dependence" in prohibited

def test_manuscript_is_island_ecology_first_and_blinded():
    s=(GEB/"blinded_main_text.md").read_text()
    assert s.startswith("# When do source islands matter? Species occupancy changes the role of connectivity across islands")
    abstract=s.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    assert len(abstract.split())<=300
    assert "**Aim:**" in abstract and "**Innovation:**" in abstract and "**Main conclusions:**" in abstract
    assert "−0.596" in abstract
    assert "all 20 matched null topologies" in abstract
    assert "These occurrence results do not demonstrate dispersal or demographic rescue." in abstract
    assert len(s.split())<5000
    assert not re.search(r"zuizui0223|github\.com/zuizui0223|ZHANG Ruiqi|張瑞琪|Rachel Zhang",s,re.I)

def test_every_reference_is_cited():
    s=(GEB/"blinded_main_text.md").read_text()
    body,rest=s.split("## References",1)
    refs=rest.split("## Data and Code Availability Statement",1)[0]
    entries=[x for x in refs.splitlines() if x.startswith("- ")]
    assert len(entries)==14
    for e in entries:
        m=re.match(r"-\s+([^,]+),.*?\((\d{4})\)",e)
        assert m,e
        first,year=m.group(1),m.group(2)
        assert year in body
        assert f"{first} " in body or f"{first} &" in body or f"{first} et al." in body

def test_submission_manifest_has_conservation_claim_boundary():
    x=json.loads((GEB/"submission_manifest.json").read_text())
    assert x["central_evidence"]["ultrarare_1_4"]["primary_supported"] is True
    assert x["central_evidence"]["rare_5_12"]["overall_supported"] is False
    assert x["central_evidence"]["exploratory_13_plus"]["actual_topology_specificity_supported"] is False
    assert x["claim_boundary"]["causal_colonization_or_rescue"] is False
    assert x["claim_boundary"]["management_intervention_effect"] is False
    assert x["new_same_dataset_threshold_search_authorized"] is False
