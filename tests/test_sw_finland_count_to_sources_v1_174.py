from pathlib import Path
import csv,importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/promote_sw_finland_counts_to_sources_v1_174.py"
CONTRACT=ROOT/"development/sw_finland_count_to_sources_contract_v1_174.json"

def load():
    spec=importlib.util.spec_from_file_location("swf174",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def mini_contract():
    c=json.loads(CONTRACT.read_text())
    c["required_v1_173"]=dict(c["required_v1_173"])
    c["required_v1_173"].update({
      "species_count":3,"minimum_anchor_matches":1,"minimum_exact_source_species":1
    })
    c["exact_source_reconstruction"]=dict(c["exact_source_reconstruction"])
    c["exact_source_reconstruction"].update({
      "island_universe":471,"minimum_exact_species":1
    })
    return c

def write_count_table(path):
    fields=["species","Historical_total_log","recovered_historical_source_count","recovered_Potential_islands","archived_absent_count","absence_plus_source_count","count_rounding_error","support_status"]
    rows=[
      {"species":"A","Historical_total_log":"0","recovered_historical_source_count":"1","recovered_Potential_islands":"470","archived_absent_count":"470","absence_plus_source_count":"471","count_rounding_error":"0","support_status":"exact_source_identity_count_supported"},
      {"species":"B","Historical_total_log":"0","recovered_historical_source_count":"1","recovered_Potential_islands":"470","archived_absent_count":"1","absence_plus_source_count":"2","count_rounding_error":"0","support_status":"incomplete_archive_absence_set"},
      {"species":"C","Historical_total_log":"0","recovered_historical_source_count":"1","recovered_Potential_islands":"470","archived_absent_count":"1","absence_plus_source_count":"2","count_rounding_error":"0","support_status":"incomplete_archive_absence_set"}
    ]
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def mini_receipt():
    return {
      "schema":"structural.sw_finland_standardized_historical_count_result.v1_173",
      "status":"STANDARDIZED_HISTORICAL_SOURCE_COUNTS_RECOVERED_T0_ONLY",
      "species_count":3,"anchors_matched":1,
      "anchor_max_count_rounding_error":0.0,
      "all_species_max_count_rounding_error":0.0,
      "exact_source_species":1,"impossible_species":0,
      "future_outcome_values_opened":0,
      "supplement_future_summary_values_used":0
    }

def test_promotes_exact_count_to_complement_sources(tmp_path):
    m=load();safe=tmp_path/"safe.csv";counts=tmp_path/"counts.csv"
    # Preserve the production source + potential = 471 invariant in synthetic tests.
    safe.write_text(
      "spp.name,holmkod,Euref_X_original,Euref_Y_original\n"
      + "".join(f"A,i{i},{i},{i}\n" for i in range(1,471))
      + "B,i1,1,1\nC,i471,471,471\n"
    )
    write_count_table(counts)
    router={"status":"T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE","protected_field_values_decoded":0,"outcome_values_read":0}
    species,members,geometry,r=m.reconstruct(safe,router,counts,mini_receipt(),mini_contract())
    assert r["exact_source_species"]==1
    assert r["incomplete_species"]==2
    assert members==[("A","i471")]
    assert r["future_outcome_values_opened"]==0
    assert r["supplement_file_required"] is False

def test_v173_receipt_threshold_drift_is_rejected(tmp_path):
    m=load();p=tmp_path/"counts.csv";write_count_table(p)
    rec=mini_receipt();rec["impossible_species"]=1
    try:m.load_count_authority(p,rec,mini_contract())
    except m.Stop:pass
    else:raise AssertionError("impossible v1.173 receipt must be rejected")

def test_contract_keeps_future_outcome_sealed():
    c=json.loads(CONTRACT.read_text())
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["supplement_future_summary_values_used"]==0
    assert c["response_boundary"]["pilot_future_outcome_authorized"] is False
    assert c["response_boundary"]["confirmatory_future_outcome_authorized"] is False
    assert c["response_boundary"]["eBird_enabled"] is False
