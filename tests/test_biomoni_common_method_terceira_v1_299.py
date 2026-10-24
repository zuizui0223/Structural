"""v1.299: deterministic six original beetle Event methods/site; no plant/beetle taxa."""
import json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from biomoni_common_method_terceira_v1_299 import evaluate
from test_biomoni_terceira_event_colocation_v1_298 import fixtures

def original():
    p=json.loads((ROOT/"development/biomoni_common_method_study_design_v1_299.json").read_text(encoding="utf-8"))
    cross=json.loads((ROOT/"development/biomoni_terceira_colocated_event_gate_v1_298.json").read_text(encoding="utf-8"))
    return p,cross

def test_synthetic_first_six_standardized_mode_events_per_site_protects_unopened_responses():
    trees,beetles=fixtures()
    protocol,cross=original()
    r=evaluate(trees,beetles,protocol,cross)
    # Synthetic fixture has FIVE shared modes (4 each), not the published
    # source's THREE shared modes (1/4/1); should legitimately stop.
    assert r["status"]=="TERMINAL_NO_FROZEN_SHARED_METHODS"
    assert r["source_reported_shared_mode_count"]==5
    assert r["original_beetle_Occurrence_rows_opened"]==0
    assert r["original_woody_Occurrence_rows_opened"]==0
    assert r["old_v1_298_full_method_gate_remains_terminal"]

def test_three_shared_modes_one_four_one_generate_sixty_exact_source_event_ids():
    t,b=fixtures()
    protocol,cross=original()
    # We require 308 original source Event rows but design a synthetic
    # 3 common methods, min counts 1,4,1, total method effort variable.
    for n in range(10):
        rec=[r for r in b if r["source_coreid"].startswith(f"b-ter-{n}-")]
        # 20 rows/site originally 5 modes×4. For common methods M1, M2,
        # M3, retain 1,4,1. Convert remaining samples to site-local
        # method strings, preserving 20 physical source Event rows/site.
        rec.sort(key=lambda r:r["source_coreid"])
        for i,row in enumerate(rec):
            if i==0:row["samplingProtocol"]="AAS"
            elif i<5:row["samplingProtocol"]="PIT"
            elif i==5:row["samplingProtocol"]="GWS"
            else:row["samplingProtocol"]=f"plot{n}-private"
    r=evaluate(t,b,protocol,cross)
    assert r["status"]=="EXPLORATORY_TEN_PLOTS_SIX_COMMON_METHOD_BEETLE_EVENTS_EACH_RESPONSE_SEALED"
    assert r["shared_protocol_modes_count"]==3
    assert r["shared_modes_minimum_sampling_events_sorted"]==[1,1,4]
    assert r["selected_beetle_Event_rows_each_woody_plot"]==6
    assert r["selected_beetle_Event_rows_total"]==60
    assert len(r["selected_original_Event_coreids_sha256"])==64
    assert r["old_v1_298_full_method_gate_remains_terminal"]
    assert r["selection_done_before_any_beetle_or_woody_species_value_access"]
    assert r["not_an_independent_geographic_replication"]
    assert not r["eBird_used"] and r["GEB_scientific_HOLD"]
    assert r["original_beetle_Occurrence_rows_opened"]==0
    assert r["original_woody_Occurrence_rows_opened"]==0
    # No source plot name, beetle species or source Event ID ever exported.
    assert "b-ter-" not in json.dumps(r)
    assert "TER-NFBF" not in json.dumps(r)

def test_even_sample_different_beetle_method_design_must_stop():
    t,b=fixtures()
    protocol,cross=original()
    # Source data mode set may not be relaxed merely for significance.
    protocol["method_subsample"]["prospective_shared_mode_count_exact"]=4
    r=evaluate(t,b,protocol,cross)
    assert r["status"]=="TERMINAL_NO_FROZEN_SHARED_METHODS"
