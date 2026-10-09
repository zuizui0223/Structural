import hashlib,importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("capture249",R/"scripts/camtrapasia_capture_header_only_v1_249.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_field_identity_audited_no_response_rows():
    assert m.BYTES==956340
    assert m.MD5=="a73975d7626def4012a4e1197497ba87"
    c=json.loads((R/"development/camtrapasia_capture_header_contract_v1_249.json").read_text())
    assert c["frozen_allowed_operations"]["do_not_iterate_through_second_or_later_lines"] is True
    assert c["proposed_future_criterion"]["admission_of_external_score_now"] is False
    assert all(v is False for v in c["safeguards"].values())
def test_true_header_reader_rejects_wrong_md5_without_data_access():
    source=b"study_id,taxon,count\nA,Some species,7\n"
    try:m.inspect(source)
    except ValueError:pass
    else:raise AssertionError("Different camera capture file accepted")
def test_geography_freeze_keeps_big_landmass_and_island_grains_distinct():
    r=json.loads((R/"development/camtrapasia_full239_polygon_result_freeze_v1_248.json").read_text())
    assert sum(x["study_n"] for x in r["source_geographic_units"])==79
    assert r["unconfounded_natural_island_geometry_only_candidate"]["distinct_original_islands"]==4
    assert r["unconfounded_natural_island_geometry_only_candidate"]["distinct_original_heldout_blocks"]==3
    assert r["unconfounded_natural_island_geometry_only_candidate"]["zero_species_specific_detection_rows_opened"] is True
