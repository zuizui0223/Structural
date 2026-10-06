from pathlib import Path
import importlib.util,json,zipfile

ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/inventory_ebird_species_archive_v1_160.py"
    spec=importlib.util.spec_from_file_location("eb160",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_contract_keeps_species_semantics_closed():
    x=json.loads((ROOT/"development/ebird_species_archive_firewall_contract_v1_160.json").read_text())
    a=x["v1_160_access_ceiling"]
    assert a["zip_central_directory_only"] is True
    assert a["member_decompression_allowed"] is False
    assert a["member_bytes_read_allowed"] is False
    assert a["RData_deserialization_allowed"] is False
    assert a["species_identity_opened"] is False
    assert a["species_detection_opened"] is False
    assert a["species_nondetection_constructed"] is False
    assert a["annual_species_occupancy_constructed"] is False
    assert a["source_loss_events_constructed"] is False
    assert a["t2_outcome_opened"] is False

def test_parent_gate_requires_successful_v159():
    m=load_module()
    c=json.loads((ROOT/"development/ebird_species_archive_firewall_contract_v1_160.json").read_text())
    good={
      "status":"RESPONSE_INDEPENDENT_PREBIOLOGY_HANDOFF_COMPLETE",
      "species_response_opened":False,
      "source_loss_events_constructed":False,
      "confirmatory_window_ids":["A","B","C"]
    }
    m.require_parent(good,c)
    bad=dict(good);bad["confirmatory_window_ids"]=["A","B"]
    try:
        m.require_parent(bad,c)
    except m.Stop:
        pass
    else:
        raise AssertionError("confirmatory-window minimum did not stop")

def test_inventory_uses_central_directory_without_member_open(tmp_path):
    m=load_module()
    z=tmp_path/"tiny.zip"
    with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as h:
        h.writestr("a.RData",b"response-a")
        h.writestr("b.RData",b"response-b")
    c={"inventory_rules":{"RData_extension_casefold":[".rdata",".rda"],"require_exact_RData_member_count":2}}
    rows,n=m.inventory(z,c)
    assert n==2
    assert [r["basename"] for r in sorted(rows,key=lambda x:x["basename"])]==["a.RData","b.RData"]

def test_inventory_function_never_calls_member_read_or_open():
    s=(ROOT/"scripts/inventory_ebird_species_archive_v1_160.py").read_text()
    body=s.split("def inventory",1)[1].split("def write_manifest",1)[0]
    assert ".infolist()" in body
    assert ".read(" not in body
    assert ".open(" not in body

def test_date_parser_and_pilot_member_selection_are_deliberately_deferred():
    x=json.loads((ROOT/"development/ebird_species_archive_firewall_contract_v1_160.json").read_text())
    r=x["inventory_rules"]
    assert r["filename_date_parser_status"]=="NOT_AUTHORIZED_IN_V1_160"
    assert r["pilot_year_member_selection_status"]=="NOT_AUTHORIZED_IN_V1_160"
    assert r["confirmatory_year_member_selection_status"]=="NOT_AUTHORIZED_IN_V1_160"

def test_priority_still_has_one_external_blocker():
    x=json.loads((ROOT/"development/structural_active_priority_v1_160.json").read_text())
    assert x["live_candidate"]["status"]=="HOLD_OFFICIAL_SAMPLING_EVENT_DATA_REQUIRED"
    assert x["live_candidate"]["species_response_access_authorized"] is False
    assert "v1_160" in x["live_candidate"]["species_archive_first_access"]
