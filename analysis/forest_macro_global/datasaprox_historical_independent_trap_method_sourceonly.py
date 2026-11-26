#!/usr/bin/env python3
"""One strict DATASAPROX original paired historical sampling METHOD gate.

Only source producer/project/sample event, WGS84/accuracy, year/month, trap
model/type/bait/colour and recorded days. NO taxon, scientificName,
abundance, ecological outcomes or species source-pool donor labels accessed.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

import datasaprox_source_metadata_gate as source
import datasaprox_historical_sourcepool_geometry_sourceonly as geo
from datasaprox_project_method_table7_gate import paper_table7,norm
from datasaprox_historical_table7_scope_sourceonly import scope_gate

SOURCE_SHA=geo.SHA
RADIUS_KM=100
REQUIRED_FIELDS={
    "ownerInstitutionCode","datasetName","eventID","year","month",
    "eventDate","dynamicProperties","sampleSizeValue","sampleSizeUnit",
    "decimalLatitude","decimalLongitude","georeferenceRemarks",
    "coordinateUncertaintyInMeters"
}
SOURCE_CANDIDATE_REQUIRED={"Model","Type"}

def nonblank(v):
    return bool(str(v or "").strip())


def method_classes(t,d):
    """Return fixed method match levels, never infer missing==unbaited."""
    # Tuple names: model,type,bait,colour,month,days
    a,b=t
    if any(not nonblank(x) for x in (*a[:2],*b[:2])):
        return (False,False,False)
    first=(a[0]==b[0] and a[1]==b[1])
    second=(first and all(nonblank(x) for x in (*a[2:4],*b[2:4]))
            and a[2:4]==b[2:4])
    third=(second and nonblank(a[4]) and a[4]==b[4]
           and a[5] is not None and b[5] is not None
           and 7<=a[5]<=35 and 7<=b[5]<=35
           and abs(a[5]-b[5])<=7)
    return first,second,third


def extract_metadata(archive):
    f=Path(archive)
    if not f.is_file() or f.stat().st_size>source.MAX_COMPRESSED:
        raise ValueError("SOURCE_ARCHIVE_OR_BYTES_INVALID")
    if hashlib.sha256(f.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError("SOURCE_PUBLISHED_V1_6_SHA256_MISMATCH")
    events={}
    bad_methods=set()
    bad_coords=set()
    n=0
    with zipfile.ZipFile(f) as z:
        if sum(x.file_size for x in z.infolist())>source.MAX_UNCOMPRESSED:
            raise ValueError("SOURCE_ARCHIVE_UNCOMPRESSED_CAP")
        m=source.schema(z)
        fields=m["fields"]
        if not REQUIRED_FIELDS.issubset(fields):
            raise ValueError("SOURCE_REQUIRED_ORIGINAL_WGS84_TRAP_METHOD_FIELDS_MISSING")
        with z.open(m["file"]) as fh:
            raw=io.TextIOWrapper(fh,encoding="utf-8-sig",errors="strict",newline="")
            reader=csv.reader(raw,delimiter=m["delimiter"],
                quotechar=m["quote"] or '"',
                quoting=csv.QUOTE_MINIMAL if m["quote"] else csv.QUOTE_NONE)
            for _ in range(m["header"]):next(reader)
            for row in reader:
                if not row:continue
                n+=1
                if n>source.MAX_ROWS:
                    raise ValueError("SOURCE_ORIGINAL_ROWS_CAP")
                def val(k):
                    i=fields.get(k)
                    return row[i].strip() if i is not None and i<len(row) else ""
                producer,project,eid=(val(k) for k in
                    ("ownerInstitutionCode","datasetName","eventID"))
                if not project or not eid:continue
                k=(producer,project,eid)
                v=source.properties(val("dynamicProperties"))
                yr,mon=val("year"),val("month")
                dt=val("eventDate")
                if (not yr or not mon) and re.match(r"^\d{4}-\d{2}",dt):
                    yr,mon=yr or dt[:4],mon or dt[5:7]
                ym=f"{yr}-{mon.zfill(2)}" if yr and mon else ""
                days=source.duration(val("sampleSizeValue"),val("sampleSizeUnit"))
                desc=(
                    source.layer(v.get("trap_stratum","")),
                    v.get("id_plot",""),
                    v.get("trap_model",""),
                    v.get("trap_type",""),
                    v.get("id_condition",""),
                    v.get("trap_bait",""),
                    v.get("trap_colour",""),
                    ym,days
                )
                loc,strict=geo.geosource(*(val(k) for k in geo.GEO_FIELDS))
                if k in events:
                    if desc!=events[k][0]:bad_methods.add(k)
                    if loc!=events[k][1]:bad_coords.add(k)
                else:
                    events[k]=(desc,loc,strict)
    if n!=675525 or len(events)!=65642 or len(bad_methods)!=1133:
        raise ValueError("SOURCE_ORIGINAL_METHOD_CONFLICT_DENOMINATOR_DRIFT")
    good={k:v for k,v in events.items() if k not in bad_methods}
    if len(good)!=64509:raise ValueError("SOURCE_RETAINED_EVENT_DENOMINATOR_DRIFT")
    site_methods=defaultdict(list)
    reject=Counter()
    for (producer,project,eid),(m,g,strict) in good.items():
        k=(producer,project,eid)
        if k in bad_coords:
            reject["source_coordinate_conflict_excluded"]+=1
            continue
        monthyear=m[7]
        yr=int(monthyear[:4]) if re.fullmatch(r"\d{4}-\d{2}",monthyear) else None
        if yr is None or not 1997<=yr<=2025:
            reject["missing_original_year"]+=1
            continue
        if not strict:
            reject["source_coord_not_point_or_accuracy_over_1km"]+=1
            continue
        lat,lon,_,_=g
        site=(producer,project,lat,lon,yr)
        yearmonth=monthyear[-2:]
        site_methods[site].append((m[2],m[3],m[5],m[6],yearmonth,m[8]))
    if len(site_methods)!=1328:
        raise ValueError("SOURCE_PREEXISTING_1328_STRICT_POINTYEAR_DENOMINATOR_DRIFT")
    return site_methods,{
        "original_rows":n,
        "original_unique_event_keys":len(events),
        "method_conflicting_keys":len(bad_methods),
        "method_consistent_event_keys":len(good),
        "geo_conflicted_but_method_consistent_event_keys":len(bad_coords-bad_methods),
        "strict_eligible_unique_source_location_years":len(site_methods),
        "source_further_exclusion_counts":dict(reject),
    }


def comparison(events,public):
    siteyears=list(events)
    audit=scope_gate(siteyears,public)
    if (audit["strict_source_projects_total"]!=60
        or audit["strict_source_project_scope_counts"].get("complete")!=40
        or audit["later_2016_2025_complete_source_project_point_years"]!=570
        or audit["publisher_complete_source_historical_other_PRODUCER_100km"]
              ["with_earlier_different_producer_within_100km"]!=122):
        raise ValueError("SOURCE_122_OF_570_GEO_TABLE7_SCOPE_DENOMINATOR_DRIFT")
    complete={
      k for k in {x[:2] for x in siteyears}
      if (public.get((norm(k[0]),norm(k[1]))) or {}).get(
        "published_project_community_scope")=="complete"
    }
    donors=[site for site in siteyears if site[:2] in complete]
    targets=[site for site in donors if 2016<=site[4]<=2025]
    target_events=sum(len(events[site]) for site in targets)
    metacount=Counter()
    for s in donors:
        for method in events[s]:
            if method[0]:metacount["model_present"]+=1
            if method[1]:metacount["type_present"]+=1
            if all(nonblank(k) for k in method[:2]):metacount["model_and_type_present"]+=1
            if all(nonblank(k) for k in method[:4]):metacount["model_type_bait_colour_present"]+=1
            if method[4]:metacount["month_present"]+=1
            if method[5] is not None and 7<=method[5]<=35:metacount["bounded_effort_days_7_35"]+=1
    # Original project-point-year *not* every trap/month is independent target.
    # Restrict all donors to original COMPLETE Table7-scope projects.
    points=np.asarray([geo.xyz(s[2],s[3]) for s in donors],dtype=np.float64)
    tree=cKDTree(points)
    chord=2*np.sin(RADIUS_KM/(2*geo.EARTH_KM))
    metric_names=("other_producer_geo_100km",
                  "matched_model_and_type_100km",
                  "plus_explicit_bait_and_colour_100km",
                  "plus_same_month_and_7to35day_effort_100km")
    passed=Counter()
    per_year=defaultdict(Counter)
    passed_provider=set()
    matched_study_project=set()
    for site in targets:
        candidate=tree.query_ball_point(geo.xyz(site[2],site[3]),chord+1e-15)
        flags=[False]*len(metric_names)
        for i in candidate:
            prev=donors[i]
            if prev[4]>=site[4] or not site[0] or not prev[0] or prev[0]==site[0]:
                continue
            flags[0]=True
            for a in events[site]:
                for b in events[prev]:
                    m=method_classes((a,b),None)
                    for j,hit in enumerate(m,1):
                        if hit:flags[j]=True
                    if all(flags):break
                if all(flags):break
            if all(flags):break
        for flag,name in zip(flags,metric_names):
            if flag:
                passed[name]+=1
                per_year[site[4]][name]+=1
        if flags[-1]:
            passed_provider.add(site[0])
            matched_study_project.add(site[:2])
    if passed[metric_names[0]]!=122:
        raise ValueError("SOURCE_PREVIOUSLY_FROZEN_STRICT_HISTORY_122_COVERAGE_DRIFT")
    if not all(passed[a]>=passed[b] for a,b in
       zip(metric_names,metric_names[1:])):
        raise ValueError("SOURCE_HIERARCHICAL_STRICT_METHOD_SUPPORT_MONOTONICITY_FAIL")
    coverage={name:{
        "covered_target_project_point_years":int(passed[name]),
        "fraction_of_570_complete_later_source_targets":round(passed[name]/570,6)}
        for name in metric_names}
    return {
       "original_author_Table7_complete_source_projects":40,
       "original_complete_source_distinct_project_pointyears":len(donors),
       "original_complete_source_later_2016to2025_project_pointyears":len(targets),
       "later_original_source_method_events_not_unique_locations":target_events,
       "original_complete_source_method_event_metadata_completeness":dict(sorted(metacount.items())),
       "source_matching_historial_other_producer_method_stage_100km":coverage,
       "number_independent_target_original_producers_at_full_method_stage":len(passed_provider),
       "number_target_original_projects_at_full_method_stage":len(matched_study_project),
       "original_species_taxon_occurrence_values_read":0,
       "original_beetle_dispersal_or_source_occupied_identified":False,
       "complete_author_Table7_no_outcome_bias_certification":False,
       "source_total_actual_sampled_zero_absence_frame_verified":False,
       "original_site_stand_tree_resource_join_admitted":False,
       "new_ecological_effects_fitted":0,
       "status":(
          "SOURCE_HISTORICALLY_MATCHED_TRAP_METHOD_GEOGRAPHY_CANDIDATE_NOT_BEETLE_POOL"
          if passed[metric_names[-1]] and len(passed_provider)>=2
          else "SOURCE_STRICT_INDEPENDENT_TRAP_METHOD_COMPARABILITY_HOLD")
    }


def synthetic():
    assert method_classes((("A","FIT","unbaited","clear","06",21),
                          ("A","FIT","unbaited","clear","06",28)),None)==(True,True,True)
    assert method_classes((("A","FIT","","","06",21),
                          ("A","FIT","","","06",21)),None)==(True,False,False)
    assert method_classes((("A","FIT","unbaited","clear","06",21),
                          ("A","FIT","unbaited","clear","05",21)),None)==(True,True,False)
    assert method_classes((("A","FIT","unbaited","clear","06",21),
                          ("A","FIT","unbaited","clear","06",35)),None)==(True,True,False)
    assert method_classes((("A","FIT","unbaited","clear","06",21),
                          ("B","FIT","unbaited","clear","06",21)),None)==(False,False,False)
    print("DATASAPROX_AUTHOR_METHOD_STRICT_HISTORY_FIXTURES_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--archive")
    p.add_argument("--paper-xml")
    p.add_argument("--out",default="datasaprox_historical_method_comparability/receipt.json")
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.archive or not a.paper_xml:
        p.error("--archive and --paper-xml required")
    report={
      "schema":"structural.datasaprox_v16_earlier_independent_producer_method_gate.v1",
      "original_publisher_zip_SHA256":geo.SHA,
      "original_source_organism_species_taxon_abundance_values_read":0,
      "new_ecological_composition_or_sourcepool_scores":0,
      "old_Datasaprox_vertical_and_traylor_forest_original_science_scores_unchanged":True,
      "source_original_project_identifiers_geography_values_exported":False,
      "eBird_used":False,"TinyFish_used":False,
      "status":"SOURCE_ORIGINAL_HISTORY_METHOD_UNOPENED"}
    try:
        s,src=extract_metadata(a.archive)
        pub,audit=paper_table7(Path(a.paper_xml).read_bytes(),return_audit=True)
        report["original_source_method_metadata_frame"]=src
        report["original_publisher_Table7_catalogue_counts"]=audit
        report["original_independent_provider_method_support"]=comparison(s,pub)
        report["status"]=report["original_independent_provider_method_support"]["status"]
    except Exception as e:
        report["status"]="SOURCE_ORIGINAL_PREBIOLOGY_METHOD_SCHEMA_STOP"
        report["error_class"]=type(e).__name__
        report["error_code"]=str(e)[:170] if isinstance(e,ValueError) else ""
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print("HISTORICAL_SOURCE_TRAP_METHOD_STATUS",report["status"])
    r=report.get("original_independent_provider_method_support",{})
    for name,val in r.get("source_matching_historial_other_producer_method_stage_100km",{}).items():
        print(name,val["covered_target_project_point_years"])
    print("ORIGINAL_TAXON_SOURCE_VALUES_READ",report["original_source_organism_species_taxon_abundance_values_read"])
if __name__=="__main__":
    main()
