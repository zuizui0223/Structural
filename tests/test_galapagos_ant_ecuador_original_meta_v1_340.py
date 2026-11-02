"""Ecuador v1.8 original source distinct from unavailable Pensoft original."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from galapagos_ant_ecuador_original_meta_v1_340 import inventory
from test_galapagos_ant_original_meta_v1_338 import make_source
def contract():
    return json.loads((ROOT/"development/galapagos_ant_ecuador_original_meta_contract_v1_340.json").read_text())
def test_fixed_alternative_original_Ecuador_data_source_metadata_only():
    r=inventory(make_source(),contract())
    assert r["status"]=="GALAPAGOS_ANT_SITE_HABITAT_ELEVATION_AND_ORIGIN_SCHEMA_PRESENT_RESPONSES_SEALED"
    assert r["source_dataset_uuid"]=="8cff356d-d84f-42f7-93f8-dac680639943"
    assert r["source_published_2026_version"]=="2026-06-17 Ecuador IPT source original version 1.8"
    assert r["original_Event_rows_opened"]==r["original_Occurrence_rows_opened"]==0
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
def test_origin_missing_in_Ecuador_does_not_use_pensoft_annotations():
    r=inventory(make_source(origin=False),contract())
    assert r["status"]=="TERMINAL_SOURCE_MISSING_ANT_HABITAT_ORIGIN_FIELD"
    assert r["source_qualification"]["source_taxonomic_origin"] is False
    assert r["original_Occurrence_rows_opened"]==0
