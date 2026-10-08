from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/independent_biological_evidence_admissibility_v1_196.json"

def test_external_ALA_is_technical_no_score_and_not_replayable():
    d=json.loads(P.read_text());a=d["datasets"]["ALA_Australian_islands"]
    assert a["geography_one_to_one_islands"]==167
    assert a["precommitted_provisional_taxa"]==65
    assert a["external_positive_taxon_island_pairs_opened"] is True
    assert a["response_scored"] is False
    assert a["fresh_same_archive_retry_authorized"] is False
    assert a["biological_positive_or_negative_adjudication"] is None

def test_checklist_frozen_source_transport_failed_before_binary_access():
    d=json.loads(P.read_text());c=d["datasets"]["Hebert_2021_archipelago_checklists"]
    assert c["first_header_audit_result"]=="STOP_EXTERNAL_CHECKLIST_TRANSPORT"
    assert c["external_file_headers_decoded"]==0
    assert c["external_island_names_decoded"]==0
    assert c["external_binary_labels_decoded"]==0
    assert c["original_heldout_labels_reopened"]==0
    assert c["downstream_scoring_authorized"] is False
    assert c["thresholds_must_not_be_relaxed"] is True
    assert "CaliforniaGulf" in c["excluded_direct_IUCN"]

def test_tern_mover_only_data_not_demographic_validation():
    d=json.loads(P.read_text());t=d["datasets"]["Denmark_arctic_tern_ring_movements"]
    assert t["natal_displacement_events"]==890 and t["breeding_displacement_events"]==200
    assert t["retained_nonmover_records_available"] is False
    assert t["independently_enumerated_available_destination_colonies"] is False
    assert t["allows_colonization_probability_or_population_rescue"] is False
    assert t["outcome_values_opened_by_structural"]==0

def test_scientific_holds_and_no_rescue():
    d=json.loads(P.read_text())
    assert d["scientific_status"]["externally_validated_contemporary_mammal_occupancy"] is False
    assert d["scientific_status"]["GEB_biological_mechanism_submission_authorized"] is False
    assert d["policy"]["no_eBird"] is True
    assert d["policy"]["no_ALA_v194_replay"] is True
    assert d["scientific_status"]["original_ultrarare_within_map_prediction_remains_numerically_supported"] is True
