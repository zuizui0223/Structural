from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_handoff_requires_official_sampling_event_data_only():
    x=json.loads((ROOT/"development/ebird_sed_acquisition_handoff_v1_157.json").read_text())
    assert x["official_source"]["product"]=="eBird Basic Dataset - Sampling Event Data"
    assert x["official_source"]["species_observation_table_requested_for_this_gate"] is False
    assert x["raw_Dryad_species_archive_may_open"] is False
    assert x["counts_as_empirical_source_loss_evidence"] is False

def test_handoff_reuses_frozen_v154_v155_v156_chain():
    x=json.loads((ROOT/"development/ebird_sed_acquisition_handoff_v1_157.json").read_text())
    f=x["frozen_chain"]
    assert f["contract"]=="development/ebird_sed_support_chain_contract_v1_156.json"
    assert f["metadata_contract"]=="development/ebird_sampling_event_metadata_audit_contract_v1_154.json"
    assert f["island_year_contract"]=="development/ebird_island_year_survey_contract_v1_155.json"

def test_local_runner_opens_no_species_response():
    s=(ROOT/"scripts/run_ebird_sed_handoff_v1_157.py").read_text()
    assert "run_ebird_sed_support_chain_v1_156.py" in s
    assert "species_response_opened" in s
    assert "source_loss_events_constructed" in s
    assert "Dryad" not in s
    assert "SCIENTIFIC NAME" not in s

def test_documented_next_action_is_external_sed_acquisition():
    s=(ROOT/"docs/EBIRD_SED_ACQUISITION_HANDOFF_V1_157.md").read_text()
    assert "Sampling Event Data" in s
    assert "2002–2019" in s
    assert "10 deduplicated complete checklists" in s
    assert "4 sampled months" in s
    assert "does **not** authorize opening the Dryad observed-species archive" in s
