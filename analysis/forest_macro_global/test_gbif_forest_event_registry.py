"""Synthetic forest event registry audit: no eBird, no fabricated site geography."""
import importlib.util,json
from pathlib import Path
SCRIPT=Path(__file__).with_name("gbif_forest_event_registry.py")
s=importlib.util.spec_from_file_location("forest_registry",SCRIPT)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def test_metadata_only_not_independent_forest_sites():
    docs={
      "forest":[
        {"key":"111","type":"SAMPLING_EVENT","title":"Native forest beetle survey",
         "doi":"10.15468/example","publishingCountry":"US","recordCount":900},
        {"key":"222","type":"SAMPLING_EVENT","title":"Grassland plot survey",
         "description":"Contains forest edge data","publishingCountry":"FR"},
        {"key":"333","type":"OCCURRENCE","title":"Forest bird opportunistic photos"},
        {"key":"444","type":"SAMPLING_EVENT","title":"eBird forest checklists"}
      ],
      "woodland":[{"key":"111","type":"SAMPLING_EVENT","title":"Native forest beetle survey"}],
    }
    def fake(term,offset,limit):
        return {"results":docs.get(term,[]) if offset==0 else [],
                "endOfRecords":True,"count":len(docs.get(term,[]))}
    rows,meta=m.collect(("forest","woodland"),fetch=fake,delay=0)
    assert len(rows)==2 and meta["n_distinct_GBIF_dataset_UUIDs"]==2
    assert meta["n_candidate_title_or_abstract_forest_keyword"]==2
    assert meta["n_unique_sampled_sites_verified"]==0
    assert meta["n_original_source_Event_rows_read"]==0
    assert not meta["eBird_used"]
    a=[x for x in rows if x["gbif_dataset_uuid"]=="111"][0]
    assert a["matched_search_terms"]=="forest|woodland"
    assert a["source_publishing_country_NOT_sampling_country"]=="US"
    assert a["source_record_count_NOT_site_count"]==900
    assert not a["original_site_count_verified"]

def test_registry_serialization_preserves_uncertainty(tmp_path):
    rows,meta=m.collect(("forest",),fetch=lambda q,o,l:{
        "results":[{"key":"t","title":"forest transect","type":"SAMPLING_EVENT",
                    "publishingCountry":"JP"}],"endOfRecords":True},delay=0)
    m.save(tmp_path,rows,meta)
    saved=json.loads((tmp_path/"GBIF_forest_source_registry_audit.json").read_text())
    assert saved["n_unique_sampled_sites_verified"]==0
    assert saved["publishing_country_is_not_sampling_location"]
    assert saved["source_license_requires_individual_verification"]
    text=(tmp_path/"GBIF_forest_sampling_event_candidates_METADATA_ONLY.csv").read_text()
    assert "source_publishing_country_NOT_sampling_country" in text
    assert "FOREST_METADATA_CANDIDATE_ONLY" in text

def test_non_forest_keyword_not_admitted():
    r=m.candidate({"key":"x","title":"Grassland summer arthropods",
        "type":"SAMPLING_EVENT"},"forest")
    assert r["status"]=="SEARCH_RESULT_FOREST_SITE_NOT_VERIFIED"
    assert m.candidate({"key":"x","title":"eBird tropical rainforest sightings",
        "type":"SAMPLING_EVENT"},"forest") is None
