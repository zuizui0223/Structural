from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_exploratory_lineage_keeps_original_scientific_method():
    x=json.loads((ROOT/"development/global_mammals_exploratory_pilot_contract_v1_70.json").read_text())
    assert x["eligibility"]["same_v165_protocol_retry"] is False
    assert x["eligibility"]["counts_as_confirmatory_evidence"] is False
    assert x["routing"]["pilot_islands"]==1275
    assert x["routing"]["confirmatory_islands"]==4126
    assert x["species_universe"]["minimum_presence"]==13
    assert x["species_universe"]["minimum_absence"]==13
    assert x["model_method"]["must_remain"]=="development/global_mammals_macro_model_contract_v1_67.json"

def test_exploratory_parser_uses_correct_rowname_schema():
    x=json.loads((ROOT/"development/global_mammals_exploratory_pilot_contract_v1_70.json").read_text())
    assert x["physical_schema"]["header_species_fields"]==5394
    assert x["physical_schema"]["data_fields"]==5395
    s=(ROOT/"scripts/run_global_mammals_exploratory_pilot_v1_70.py").read_text()
    assert 'if header!=species' in s
    assert 'if len(fields)!=nsp+1' in s
    assert 'vals=fields[1:]' in s
    assert '"confirmatory_occurrence_values_decoded":0' in s

def test_no_execution_request_exists_before_v169_artifact_freeze():
    assert not (ROOT/"development/global_mammals_exploratory_pilot_request_v1_70.json").exists()
