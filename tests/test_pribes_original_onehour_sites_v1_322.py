"""Synthetic response-blind PRIBES separate published 1-hour subset science gates."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from pribes_original_onehour_sites_v1_322 import original_onehour_cohort
from test_pribes_original_event_sites_v1_321 import fixture as base_fixture

def contracts():
    p=json.loads((ROOT/"development/pribes_equal_onehour_original_event_protocol_v1_322.json").read_text())
    older=json.loads((ROOT/"development/pribes_original_event_site_contract_v1_321.json").read_text())
    return p,older
def example():
    raw=base_fixture()
    # Source 80 Events / 79 full physical source locations. Six overlap
    # islands contain 73 measured physical sites, of which 72 are one-hour.
    for row in raw:
        row["samplingProtocol"]="vegetation beating"
    corvo=next(r for r in raw if r["island"]=="Corvo")
    corvo["island"]="Faial"
    corvo["locationID"]="SITE_FAI_12"
    invalid=next(r for r in raw if r["island"]=="Corvo")
    invalid["sampleSizeValue"]=""
    half_hour=next(r for r in raw if r["island"]=="Pico")
    half_hour["sampleSizeValue"]="30"
    half_hour["sampleSizeUnit"]="minutes"
    assert len(raw)==80
    return raw

def test_original_published_one_hour_only_separate_lower_evidence_cohort():
    p,old=contracts()
    r=original_onehour_cohort(example(),p,old)
    assert r["status"]=="NEW_SEPARATE_72_RUDERAL_SITES_ONEHOUR_EACH_TAXON_RESPONSES_SEALED"
    assert r["onehour_source_sites_overlapping_BALA_n"]==72
    assert r["onehour_source_physical_sites_by_BALA_overlap_island"]=={
       "FAI":13,"FLO":12,"PIC":11,"TER":12,"SMG":12,"SMR":12}
    assert r["source_event_exclusions_by_exact_effort_metadata"]=={
       "not_original_published_one_hour":1,"unknown_source_effort":1}
    assert r["source_additional_duplicate_onehour_Events_per_site"]==1
    assert r["previous_v1_321_full_source_equal_effort_gate"]=="TERMINAL"
    assert r["source_origin_and_species_values_OPENED"]==0
    assert r["original_BALA_Event_or_Occurrence_rows_reopened"]==0
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
    assert "SITE_FAI" not in json.dumps(r)
    assert "PRIBES-COR" not in json.dumps(r)

def test_nonuniform_original_method_is_not_relabeled_after_species():
    x=example()
    p,old=contracts()
    r=next(v for v in x if v["island"]=="Flores")
    r["samplingProtocol"]="sweep-netting"
    out=original_onehour_cohort(x,p,old)
    assert out["status"]=="TERMINAL_NO_EXACT_PUBLISHED_ONEHOUR_SIX_ISLAND_FRAME"
    assert out["source_origin_and_species_values_OPENED"]==0

def test_source_unit_changed_no_posthoc_back_conversion():
    x=example()
    p,old=contracts()
    r=next(v for v in x if v["island"]=="Flores")
    r["sampleSizeValue"]="60"
    r["sampleSizeUnit"]="minutes"
    # Tampering the fixed all-event v1.321 source-effort fingerprint is a
    # HARD error, not eligible to be relabelled as the separate one-hour study.
    import pytest
    with pytest.raises(ValueError,match="TERMINAL diagnosis not fixed"):
        original_onehour_cohort(x,p,old)

def test_prior_all_event_source_gate_never_qualified_in_restricted_cohort():
    p,old=contracts()
    r=original_onehour_cohort(example(),p,old)
    assert r["previous_v1_321_full_source_equal_effort_gate"]=="TERMINAL"
    assert r["onehour_source_sites_overlapping_BALA_n"]==72
    assert len(r["source_onehour_selected_original_Event_coreids_sha256"])==64
