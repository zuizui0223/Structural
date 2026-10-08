from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v195_terminal_stop_does_not_rescue_biology():
    x=json.loads((ROOT/"development/global_mammals_ala_technical_terminal_stop_v1_195.json").read_text())
    assert x["status"]=="TERMINAL_POST_PAIR_EXPOSURE_TECHNICAL_STOP_NO_ECOLOGICAL_SCORE"
    assert x["response_boundary"]["external_ALA_species_island_year_pairs_opened"] is True
    assert x["response_boundary"]["original_4126_island_heldout_mammal_labels_opened"]==0
    assert x["response_boundary"]["same_ALA_archive_rerun_authorized"] is False
    assert x["scientific_conclusion"]["supported_external_validation"] is False
    assert x["scientific_conclusion"]["non_supportive_external_validation"] is False

def test_old_actual_header_schema_and_new_reader_error_are_explicit():
    x=json.loads((ROOT/"development/global_mammals_ala_technical_terminal_stop_v1_195.json").read_text())
    assert x["exact_technical_cause"]["no_prediction_score_calculated"] is True
    assert "2 uint32 header dimensions" in x["exact_technical_cause"]["old_actual_format"]
    original=(ROOT/"scripts/score_global_mammals_ultrarare_v1_115.py").read_text()
    new=(ROOT/"scripts/score_global_mammals_ala_positive_locations_v1_194.py").read_text()
    assert 'struct.unpack("<II",h.read(8))' in original
    assert 'len(shape)*4' in new
