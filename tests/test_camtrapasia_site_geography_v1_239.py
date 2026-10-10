import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v239",R/"scripts/camtrapasia_sites_vs_mammal_heldout_grid_v1_239.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_grid_metadata_does_not_make_island_identity():
    d=json.loads((R/"development/camtrapasia_site_geography_contract_v1_239.json").read_text())
    assert d["exact_method"]["no_exact_island_match"] is True
    assert d["exact_method"]["do_not_assume_sites_are_islands"] is True
    assert d["scientific_limits"]["taxa38_overlap_not_species_detection"] is True
    assert d["source_survey_metadata"]["bytes"]==m.SOURCE_SIZE
    assert all(v is False for v in d["guards"].values())
def test_heldout_index_rejects_wrong_denominator():
    fake={"schema":"structural.global_mammal_heldout_geographic_search_index_result.v1_235",
        "original_heldout_islands":4,"original_selected_model_islands":5401,
        "global_distinct_heldout_blocks":168}
    try:m.validated_grid(fake)
    except ValueError:pass
    else:raise AssertionError("Wrong heldout target accepted")
