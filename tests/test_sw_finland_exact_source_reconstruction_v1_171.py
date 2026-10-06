from pathlib import Path
import csv,importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/reconstruct_sw_finland_exact_sources_v1_171.py"
CONTRACT=ROOT/"development/sw_finland_exact_source_reconstruction_contract_v1_171.json"

def load():
    spec=importlib.util.spec_from_file_location("swf171",SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def make_contract():
    c=json.loads(CONTRACT.read_text());c["island_universe"]["expected_unique_islands"]=3;c["exact_identity_rule"]["minimum_exact_species"]=1;return c

def test_exact_complement_reconstruction(tmp_path):
    m=load()
    safe=tmp_path/"safe.csv"
    safe.write_text(
      "spp.name,holmkod,Euref_X_original,Euref_Y_original\n"
      "A,i1,1,1\nA,i2,2,2\n"
      "B,i1,1,1\nC,i3,3,3\n",
      encoding="utf-8"
    )
    lookup=tmp_path/"lookup.csv"
    lookup.write_text(
      "species,Potential_islands,historical_source_count\nA,2,1\nB,2,1\nC,2,1\n",
      encoding="utf-8"
    )
    router={"status":"T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE","protected_field_values_decoded":0,"outcome_values_read":0}
    validation={"status":"T0_SOURCE_COUNT_LOOKUP_VALIDATED_NO_FUTURE_SUMMARIES_PERSISTED","future_summary_values_persisted":0}
    species,members,geometry,r=m.reconstruct(safe,lookup,router,validation,make_contract())
    assert r["exact_source_species"]==1
    assert r["incomplete_species"]==2
    assert ("A","i3") in members
    assert all(x[0] not in {"B","C"} for x in members)
    assert r["future_outcome_values_opened"]==0

def test_impossible_absence_count_stops(tmp_path):
    m=load();safe=tmp_path/"safe.csv";lookup=tmp_path/"lookup.csv"
    safe.write_text("spp.name,holmkod,Euref_X_original,Euref_Y_original\nA,i1,1,1\nA,i2,2,2\nB,i3,3,3\n")
    lookup.write_text("species,Potential_islands,historical_source_count\nA,1,2\nB,2,1\n")
    router={"status":"T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE","protected_field_values_decoded":0,"outcome_values_read":0}
    validation={"status":"T0_SOURCE_COUNT_LOOKUP_VALIDATED_NO_FUTURE_SUMMARIES_PERSISTED","future_summary_values_persisted":0}
    try:m.reconstruct(safe,lookup,router,validation,make_contract())
    except m.Stop:pass
    else:raise AssertionError("impossible absence count must stop")

def test_contract_keeps_future_outcome_sealed():
    c=json.loads(CONTRACT.read_text())
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["pilot_future_outcome_authorized"] is False
    assert c["response_boundary"]["confirmatory_future_outcome_authorized"] is False
    assert c["response_boundary"]["eBird_enabled"] is False
