from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("ht199",ROOT/"scripts/probe_hebert_one_byte_transport_v1_199.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture():
    return (
        json.loads((ROOT/"development/hebert_transport_preflight_receipt_v1_198.json").read_text()),
        json.loads((ROOT/"development/global_mammals_independent_checklist_preintake_v1_188.json").read_text()),
        json.loads((ROOT/"development/hebert_one_byte_transport_contract_v1_199.json").read_text())
    )

def test_only_206_zero_to_zero_range_can_be_read():
    assert m.range_response_ok(206,"bytes 0-0/803","text/csv")
    assert not m.range_response_ok(200,"bytes 0-0/803","text/csv")
    assert not m.range_response_ok(206,"bytes 0-5/803","text/csv")
    assert not m.range_response_ok(206,"bytes 0-0/803","text/html")
    assert not m.range_response_ok(206,"bytes 0-0/1","text/csv")

def test_transport_only_boundary_with_no_available_file():
    receipt,source,contract=fixture()
    r=m.run(receipt,source,contract,probe=lambda _:{"state":"RANGE_REQUEST_FAILED","range_bytes_read":0})
    assert r["status"]=="RANGE_UNAVAILABLE"
    assert r["original_frozen_file_count"]==9
    assert r["range_probe_bytes_read"]==0
    assert r["external_island_species_0_1_values_decoded"]==0
    assert r["original_heldout_mammal_values_opened"]==0
    assert r["external_scoring_authorized"] is False

def test_one_byte_range_result_does_not_authorize_external_scoring():
    receipt,source,contract=fixture()
    r=m.run(receipt,source,contract,probe=lambda _:{"state":"ONE_BYTE_RANGE_OK","range_bytes_read":1})
    assert r["status"]=="RANGE_AVAILABLE_ALL_9"
    assert r["files_with_range_available"]==9
    assert r["range_probe_bytes_read"]<=18
    assert r["source_header_fields_decoded"]==0
    assert r["source_island_names_decoded"]==0
    assert r["external_scoring_authorized"] is False
    assert r["biological_evidence_produced"] is False
