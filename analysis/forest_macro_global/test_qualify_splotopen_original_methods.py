"""Validate GIVD method metadata crosswalk and no pseudo-independent forest expansion."""
import csv
import importlib.util
import json
from pathlib import Path
import pytest

SCRIPT=Path(__file__).with_name("qualify_splotopen_original_methods.py")
META=Path(__file__).with_name("original_method_crosswalk_v1.json")
spec=importlib.util.spec_from_file_location("original_methods",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fake_source(path,missing=None,unverified=False):
    fields=["source_givd_dataset","forest_plots","contemporaneous_height_and_cover_plots",
            "declared_woody_height_and_cover_plots",
            "UNSPECIFIED_survey_scope_height_and_cover_plots"]
    with path.open("w",newline="",encoding="utf-8") as fd:
        w=csv.DictWriter(fd,fieldnames=fields);w.writeheader()
        for i in range(84):
            sid=m.EXPECTED_IDS[i] if i<4 else f"source-other-{i}"
            if sid==missing:sid="missing-as-source-"+str(i)
            both=([85,24,1499,1306][i] if i<4 else 1)
            w.writerow({
                "source_givd_dataset":sid,
                "forest_plots":both+10,
                "contemporaneous_height_and_cover_plots":both,
                "declared_woody_height_and_cover_plots":both if i<2 else 0,
                "UNSPECIFIED_survey_scope_height_and_cover_plots":both if i in (2,3) else 0
            })

def test_qualified_source_is_still_not_independent_forest_network(tmp_path):
    source=tmp_path/"sources.csv"
    fake_source(source)
    q=m.run(source,META,tmp_path/"out")
    assert q["source_original_givd_identity_verified"]==4
    assert q["open_subset_matched_height_cover_plot_nodes_not_independent_forests"]==2914
    assert q["declared_woody_scope_source_count"]==2
    assert q["unclear_open_subset_scope_source_count"]==2
    assert q["forest_source_networks_certified_for_island_biogeographic_occurrence_test"]==0
    assert q["new_species_data_opened"]==0
    assert not q["unobserved_forest_patches_assumed_unoccupied"]
    raw=(tmp_path/"out"/"four_source_original_field_method_crosswalk.csv").read_text()
    assert "GIVD_ID" in raw and "GIVD_ID,longitude" not in raw
    assert "PENDING" in raw
    assert "experimental control" not in raw

def test_source_disappearance_fails(tmp_path):
    source=tmp_path/"source.csv"
    fake_source(source,missing="AS-BD-001")
    with pytest.raises(ValueError,match="source_original_dataset_not_in_splotopen"):
        m.run(source,META,tmp_path/"out")

def test_will_not_accept_unfrozen_or_admitted_source(tmp_path):
    source=tmp_path/"source.csv"
    fake_source(source)
    changed=json.loads(META.read_text())
    changed["source_records"][0]["source_outcome_admission"]="ADMITTED"
    p=tmp_path/"crosswalk.json";p.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match="marked_admitted"):
        m.run(source,p,tmp_path/"out")
