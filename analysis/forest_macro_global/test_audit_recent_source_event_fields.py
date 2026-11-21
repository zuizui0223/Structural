"""Synthetic original GBIF forest source Event field QC; never sites from records."""
import importlib.util,json,csv
from pathlib import Path
FILE=Path(__file__).with_name("audit_recent_source_event_fields.py")
sp=importlib.util.spec_from_file_location("forest_field_qc",FILE)
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)

def test_event_metadata_counts_not_visitor_species_or_independent_sites():
    cand={"dataset_uuid":"a","predefined_source_role_NOT_geography_proven":"forest",
          "title":"forest","indexed_occurrence_count_2019_2026_NOT_sites":12000}
    response={"results":[
        {"eventID":"site-A-1","locationID":"A","year":2022,"country":"JP",
         "decimalLatitude":33.0,"decimalLongitude":130.0,
         "samplingProtocol":"Pitfall traps","habitat":"native forest",
         "scientificName":"Species X","individualCount":20},
        {"eventID":"site-A-1","locationID":"A","year":2022,"country":"JP",
         "decimalLatitude":33.0,"decimalLongitude":130.0,
         "samplingProtocol":"Pitfall traps","habitat":"native forest",
         "scientificName":"Species Y","individualCount":30}]}
    r=m.summarize(cand,response)
    assert r["metadata_sample_indexed_occurrence_rows_downloaded"]==2
    assert r["sample_eventID_distinct_lower_bound_NOT_full_site_count"]==1
    assert r["sample_coordinate_valid_n"]==2
    assert r["sample_samplingProtocol_present_count"]==2
    assert r["actual_independent_forest_plots_verified"]==0
    assert "scientificName" not in json.dumps(r)
    assert "Species X" not in json.dumps(r)
    assert "individualCount" not in json.dumps(r)

def test_year_geolocation_and_missing_fields_not_imputed():
    row={"dataset_uuid":"b","predefined_source_role_NOT_geography_proven":"x",
         "title":"temperate forest","indexed_occurrence_count_2019_2026_NOT_sites":10}
    d=m.summarize(row,{"results":[{"eventID":"","country":"SE","year":2021}]})
    assert d["sample_coordinate_valid_n"]==0
    assert d["sample_eventID_distinct_lower_bound_NOT_full_site_count"]==0
    assert d["sample_coordinate_uncertainty_reported_n"]==0
    assert d["actual_independent_forest_plots_verified"]==0
    assert m.valid_coord({"decimalLatitude":91,"decimalLongitude":0}) is False
