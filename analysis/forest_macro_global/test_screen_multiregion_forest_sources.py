"""Fixed cross-biome forest network: no biological values or false plot counts."""
import importlib.util,json
from pathlib import Path
FILE=Path(__file__).with_name("screen_multiregion_forest_sources.py")
spec=importlib.util.spec_from_file_location("forest_screen",FILE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_metadata_years_countries_and_no_site_claims():
    uid=list(m.FIXED_CANDIDATES)[0]
    source={uid:{"name":"Boreal forest monitoring","gbif_dataset_uuid":uid}}
    def mock(path,params=None):
        if path.startswith("/dataset/"):
            return {"key":uid,"type":"SAMPLING_EVENT","title":"Boreal forest monitoring","publishingCountry":"SE"}
        if params and params.get("year")=="2019,2026":
            return {"count":17,"results":[]}
        return {"count":800,"facets":[{"field":"COUNTRY","counts":[{"name":"NO","count":400},{"name":"SE","count":400}]}],"results":[]}
    item=m.build_row(uid,"boreal",source[uid],
        mock("/dataset/"+uid),mock("/occurrence/search"),mock("/occurrence/search",{"year":"2019,2026"}))
    assert item["indexed_occurrence_count_2019_2026_NOT_sites"]==17
    assert item["actual_occurrence_country_facets_n"]==2
    assert item["publisher_country_NOT_sampling_country"]=="SE"
    assert not item["georeferenced_independent_forest_plots_verified"]
    assert item["original_occurrence_species_rows_visited"]==0
    assert item["source_2020_canopy_alignment_status"]=="RECENT_OCCURRENCE_CANDIDATE_NOT_SITE_VERIFIED"

def test_two_source_networks_no_eligible_plot_fabrication(tmp_path):
    ids=list(m.FIXED_CANDIDATES)
    # Fixed dataset IDs must not be substituted by outcome-selected candidates.
    assert len(ids)==18
    def mock(path,params=None):
        if path.startswith("/dataset/"):
            return {"key":path.split("/")[-1],"type":"SAMPLING_EVENT","title":"Forest plot source"}
        if params and params.get("year")=="2019,2026":
            return {"count":0,"results":[]}
        return {"count":50,"facets":[],"results":[]}
    registry=[{"gbif_dataset_uuid":uid,"name":"Forest site census"} for uid in ids]
    rows=m.screen(registry,request=mock,delay=0)
    report=m.save(tmp_path,rows)
    assert report["original_global_registry_fixed_source_candidates"]==18
    assert report["actual_original_forest_plot_site_counts_verified"]==0
    assert report["sampled_study_locations_qualified_for_2020_canopy_height"]==0
    assert report["source_original_Occurrence_species_rows_read"]==0
    assert report["not_a_global_forest_biodiversity_or_canopy_effect"]
    assert not report["eBird_used"]
    assert (tmp_path/"GBIF_multiregion_original_forest_monitoring_screen.csv").exists()
    assert json.loads((tmp_path/"multiregion_source_screen_manifest.json").read_text())==report
