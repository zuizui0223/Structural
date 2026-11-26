#!/usr/bin/env python3
"""DATASAPROX historical source SURVEY support × published Table 7 scope only.

No beetle taxon ID, species presence, abundance, raw project/coordinate/site,
original source sample content is exported. Public author Table7 project taxonomy
scope (complete vs partial) is NOT inferred from original species values.
"""
import argparse
import json
import collections
from pathlib import Path

from datasaprox_historical_sourcepool_geometry_sourceonly import (
    SHA, read_original_meta, match_history, TARGET_FIRST_YEAR, LAST_YEAR, test as geographic_test
)
from datasaprox_project_method_table7_gate import (
    paper_table7,norm,PAPER_DOI
)

def scope_gate(source_siteyears, published):
    project_sites=collections.defaultdict(list)
    for site in source_siteyears:
        producer,project,lat,lon,year=site
        project_sites[(producer,project)].append(site)
    categories={}
    for original_project in project_sites:
        pub=published.get((norm(original_project[0]),norm(original_project[1])))
        scope=pub["published_project_community_scope"] if pub else "UNMATCHED"
        if scope not in ("complete","partial","UNMATCHED"):
            raise ValueError("SOURCE_PUBLISHER_TABLE7_SCOPE_CLASS_STOP")
        categories[original_project]=scope
    project_counts=collections.Counter(categories.values())
    point_years_by_scope=collections.Counter()
    for key,sites in project_sites.items():
        point_years_by_scope[categories[key]]+=len(sites)
    strict_complete=[site for site in source_siteyears
                     if categories[(site[0],site[1])]=="complete"]
    strict_partial=[site for site in source_siteyears
                    if categories[(site[0],site[1])]=="partial"]
    complete_target=[site for site in strict_complete
                     if TARGET_FIRST_YEAR<=site[4]<=LAST_YEAR]
    result={
        "original_publisher_table7_doi":PAPER_DOI,
        "strict_source_projects_total":len(project_sites),
        "strict_source_project_scope_counts":dict(sorted(project_counts.items())),
        "strict_source_project_point_year_scope_counts":dict(sorted(point_years_by_scope.items())),
        "strict_source_complete_only_project_count":
            int(project_counts["complete"]),
        "strict_source_complete_only_distinct_producers":
            len({s[0] for s in strict_complete if s[0]}),
        "strict_source_complete_only_project_point_years":len(strict_complete),
        "later_2016_2025_complete_source_project_point_years":
            len(complete_target),
        "original_species_labels_or_taxon_abundances_read":0,
        "unmatched_table7_project_assumed_complete":False,
        "anonymous_no_original_project_titles_or_sample_ids_exported":True,
    }
    if strict_complete:
        audit=match_history(strict_complete)
        result["publisher_complete_source_historical_other_PRODUCER_100km"]={
            "eligible_later_complete_source_project_point_years":
                audit["target_2016_2025_project_point_years"],
            "with_earlier_different_producer_within_100km":
                audit["target_with_historical_independent_PRODUCER_within_100km"],
            "with_earlier_different_producer_within_200km":
                audit["target_with_historical_independent_PRODUCER_within_200km"],
            "with_earlier_different_project_within_100km_descriptive":
                audit["target_with_historical_independent_project_within_100km"],
            "species_specific_SOURCE_POPULATIONS_IDENTIFIED":False,
            "original_taxonomic_coverage_harmonized_across_projects":False,
        }
    else:
        result["publisher_complete_source_historical_other_PRODUCER_100km"]={
            "eligible_later_complete_source_project_point_years":0,
            "with_earlier_different_producer_within_100km":0,
            "with_earlier_different_producer_within_200km":0,
            "species_specific_SOURCE_POPULATIONS_IDENTIFIED":False,
        }
    result["status"]=(
        "SOURCE_AUTHOR_COMPLETE_PROJECT_HISTORICAL_SURVEY_SUPPORT_READY_NOT_SPECIES_POOL"
        if complete_target and
           result["publisher_complete_source_historical_other_PRODUCER_100km"]
           ["with_earlier_different_producer_within_100km"]>0
        else "SOURCE_AUTHOR_COMPLETE_PROJECT_DIFFERENT_PRODUCER_HISTORICAL_GEOGRAPHY_HOLD"
    )
    return result


def synthetic():
    fake={
      ("public_provider_a","Source A"):{"published_project_community_scope":"complete"},
      ("public_provider_a","Source B"):{"published_project_community_scope":"partial"}
    }
    fake_sites=[
      ("public_provider_a","Source A",46.0,2.0,2019),
      ("public_provider_a","Source B",46.1,2.1,2020),
      ("public_provider_x","No Map",46.3,2.2,2021)]
    z=scope_gate(fake_sites,{
      (norm(k[0]),norm(k[1])):v for k,v in fake.items()
    })
    assert z["strict_source_projects_total"]==3
    assert z["strict_source_project_scope_counts"]["complete"]==1
    assert z["strict_source_project_scope_counts"]["partial"]==1
    assert z["strict_source_project_scope_counts"]["UNMATCHED"]==1
    assert not z["unmatched_table7_project_assumed_complete"]
    assert z["original_species_labels_or_taxon_abundances_read"]==0
    print("DATASAPROX_ORIGINAL_AUTHORED_TABLE7_SCOPE_SOURCEONLY_FIXTURE_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--archive")
    p.add_argument("--paper-xml")
    p.add_argument("--out",default="datasaprox_historical_table7_scope/receipt.json")
    args=p.parse_args()
    synthetic()
    geographic_test()
    if args.test:return
    if not args.archive or not args.paper_xml:
        p.error("--archive and --paper-xml required")
    r={
        "schema":"structural.datasaprox_v16_author_table7_historical_independent_survey_scope.v1",
        "original_publisher_dataset_SHA256":SHA,
        "public_published_article_DOI":PAPER_DOI,
        "original_beetle_organism_taxon_abundance_values_read":0,
        "original_raw_project_or_point_identifiers_exported":False,
        "old_DATASAPROX_vertical_source_science_STOP_retained":True,
        "prior_Ecuador_Traylor_Ramberg_BALA_GEB_mammal_scores_unreopened":True,
        "new_biological_effects_calculated":0,
        "status":"SOURCE_ORIGINAL_TABLE7_UNOPENED",
    }
    try:
        pub,audit=paper_table7(Path(args.paper_xml).read_bytes(),return_audit=True)
        original=read_original_meta(args.archive)
        sites=original.pop("eligible_unique_project_point_years")
        r["original_source_event_and_strict_geography_aggregate"]={
            "source_unique_events":original["source_unique_events"],
            "original_rows":original["original_rows"],
            "method_conflicts":original["method_conflicts"],
            "retained_method_consistent_events":original["retained_method_consistent_events"],
            "strict_original_event_count":original["source_metadata_rejection_counts"].get(
                "strict_source_events_meeting_coordinate_and_time_gate",0),
            "strict_project_point_years":len(sites),
        }
        r["original_published_Table7_method_catalogue_counts_only"]=audit
        r["author_table7_strict_source_coverage"]=scope_gate(sites,pub)
        r["status"]=r["author_table7_strict_source_coverage"]["status"]
    except Exception as e:
        r["status"]="SOURCE_PUBLISHED_TABLE7_OR_ORIGINAL_LOCATION_SCHEMA_STOP"
        r["error_class"]=type(e).__name__
        r["error_code"]=str(e)[:150] if isinstance(e,ValueError) else ""
    path=Path(args.out)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("SOURCE_AUTHOR_TAXON_SCOPE_HISTORICAL_COVERAGE_STATUS",r["status"])
    x=r.get("author_table7_strict_source_coverage",{})
    print("STRICT_COMPLETE_ORIGINAL_SOURCE_PROJECTS",x.get("strict_source_complete_only_project_count"))
    print("HISTORICAL_DIFFERENT_PRODUCER_100KM",x.get(
       "publisher_complete_source_historical_other_PRODUCER_100km",{}).get(
           "with_earlier_different_producer_within_100km"))
    print("ORIGINAL_BEETLE_SPECIES_COUNT_ROWS_READ",r["original_beetle_organism_taxon_abundance_values_read"])

if __name__=="__main__":
    main()
