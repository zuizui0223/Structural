#!/usr/bin/env python3
"""DATASAPROX v1.6 original historical source *SURVEY COVERAGE*, no biology.

Read only original producer/project/event, time, WGS84/precision, sample method.
No taxonIDs, species counts, abundance or actual sampled absence is inspected.
Original 65,642 event keys and 1,133 method conflicts are immutable source QA.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter
from pathlib import Path

import datasaprox_source_metadata_gate as original

SHA="4163a2f8f72d756e74f64319b8e199b284ecc6414196147e4465d342d7dcb6d0"
N_ROWS=675525
EVENT_KEYS=65642
METHOD_CONFLICTS=1133
N_RETAINED=64509
FIRST_YEAR=1997
LAST_YEAR=2025
TARGET_FIRST_YEAR=2016
RADIUS_KM=(100,200)
EARTH_KM=6371.0088
GEO_FIELDS=("decimalLatitude","decimalLongitude","georeferenceRemarks",
            "coordinateUncertaintyInMetres")
SOURCE_FIELDS=("ownerInstitutionCode","datasetName","eventID","year","month",
              "eventDate","sampleSizeValue","sampleSizeUnit","dynamicProperties")

class SourceStop(ValueError):
    pass


def numbers(raw, minimum=None, maximum=None):
    try:x=float(str(raw).strip())
    except (ValueError,TypeError):return None
    if not math.isfinite(x) or (minimum is not None and x<minimum) or (
         maximum is not None and x>maximum):
        return None
    return x


def geosource(lat,lon,remarks,uncertainty):
    a=numbers(lat,-90,90)
    b=numbers(lon,-180,180)
    strict=(str(remarks).strip().casefold()=="point")
    u=numbers(uncertainty)
    return (a,b,str(remarks).strip().casefold(),u), bool(
        a is not None and b is not None and strict and
        u is not None and 0<u<=1000)


def read_original_meta(archive):
    p=Path(archive)
    if not p.exists() or p.stat().st_size>original.MAX_COMPRESSED:
        raise SourceStop("SOURCE_ORIGINAL_ARCHIVE_NOT_AVAILABLE_OR_TOO_LARGE")
    if hashlib.sha256(p.read_bytes()).hexdigest()!=SHA:
        raise SourceStop("SOURCE_ORIGINAL_V1_6_ARCHIVE_FINGERPRINT_STOP")
    events={}
    conflict=set()
    coordinate_conflict=set()
    total=0
    with zipfile.ZipFile(p) as z:
        if sum(i.file_size for i in z.infolist())>original.MAX_UNCOMPRESSED:
            raise SourceStop("SOURCE_UNCOMPRESSED_ARCHIVE_OVER_CAP")
        meta=original.schema(z)
        fields=meta["fields"]
        required=set(SOURCE_FIELDS)|set(GEO_FIELDS)
        if not required.issubset(fields):
            raise SourceStop("SOURCE_MISSING_TIME_COORD_PROJECT_ORIGINAL_DWC_FIELDS")
        with z.open(meta["file"]) as f:
            raw=io.TextIOWrapper(f,encoding="utf-8-sig",errors="strict",newline="")
            reader=csv.reader(raw,delimiter=meta["delimiter"],
                              quotechar=meta["quote"] or '"',
                              quoting=csv.QUOTE_MINIMAL if meta["quote"] else csv.QUOTE_NONE)
            for _ in range(meta["header"]):next(reader)
            for row in reader:
                if not row:continue
                total+=1
                if total>original.MAX_ROWS:raise SourceStop("SOURCE_ROW_CAP_STOP")
                def val(k):
                    col=fields.get(k)
                    return row[col].strip() if col is not None and col<len(row) else ""
                producer=val("ownerInstitutionCode")
                project=val("datasetName")
                eid=val("eventID")
                if not project or not eid:continue
                key=(producer,project,eid)
                props=original.properties(val("dynamicProperties"))
                year,month=val("year"),val("month")
                dt=val("eventDate")
                if (not year or not month) and re.match(r"^\d{4}-\d{2}",dt):
                    year,month=year or dt[:4],month or dt[5:7]
                ym=f"{year}-{month.zfill(2)}" if year and month else ""
                dur=original.duration(val("sampleSizeValue"),val("sampleSizeUnit"))
                desc=(
                    original.layer(props.get("trap_stratum","")),
                    props.get("id_plot",""),
                    props.get("trap_model",""),
                    props.get("trap_type",""),
                    props.get("id_condition",""),
                    props.get("trap_bait",""),
                    props.get("trap_colour",""),
                    ym,
                    dur
                )
                georef,ok=geosource(*(val(k) for k in GEO_FIELDS))
                if key in events:
                    if events[key][0]!=desc:conflict.add(key)
                    if events[key][1]!=georef:coordinate_conflict.add(key)
                else:
                    events[key]=(desc,georef,ok)
    if total!=N_ROWS or len(events)!=EVENT_KEYS or len(conflict)!=METHOD_CONFLICTS:
        raise SourceStop("SOURCE_HISTORIC_EVENT_COUNT_OR_CONFLICT_BASELINE_DRIFT")
    remaining={key:v for key,v in events.items() if key not in conflict}
    if len(remaining)!=N_RETAINED:
        raise SourceStop("SOURCE_RETAINED_EVENT_BASELINE_DRIFT")
    eligible={}
    reason=Counter()
    for (producer,project,eid),(desc,geo,geo_pass) in remaining.items():
        if (producer,project,eid) in coordinate_conflict:
            reason["intraevent_coordinate_conflict"]+=1
            continue
        ym=desc[7]
        y=int(ym[:4]) if re.fullmatch(r"\d{4}-\d{2}",ym) else None
        if y is None or not FIRST_YEAR<=y<=LAST_YEAR:
            reason["year_unknown_or_outside_original_window"]+=1
            continue
        lat,lon,remark,uncertainty=geo
        if lat is None or lon is None:
            reason["missing_or_invalid_WGS84"]+=1
            continue
        if remark!="point":
            reason["not_verified_point_georeference"]+=1
            continue
        if not geo_pass:
            reason["point_precision_missing_or_over_1000m"]+=1
            continue
        # Distinct observed project×point×year support, never independent plot.
        site=(producer,project,lat,lon,y)
        eligible[site]=True
    return {
        "original_rows":total,
        "source_unique_events":len(events),
        "method_conflicts":len(conflict),
        "retained_method_consistent_events":len(remaining),
        "coordinate_conflicting_event_keys":len(coordinate_conflict-conflict),
        "source_metadata_rejection_counts":dict(sorted(reason.items())),
        "eligible_unique_project_point_years":list(eligible)
    }


def xyz(lat,lon):
    lat=math.radians(lat)
    lon=math.radians(lon)
    c=math.cos(lat)
    return (c*math.cos(lon),c*math.sin(lon),math.sin(lat))


def match_history(siteyears):
    """Compute source PROJECT coverage only, with zero data on taxon identity."""
    try:
        import numpy as np
        from scipy.spatial import cKDTree
    except ImportError as e:
        raise SourceStop("SOURCE_SCIPY_KDTREE_NOT_AVAILABLE") from e
    if not siteyears:
        raise SourceStop("SOURCE_NO_PRECISE_PROJECT_POINT_YEAR_SUPPORT")
    earliest={}
    # Original DISTINCT project-point *earliest* recorded year, not all repeats.
    for producer,project,lat,lon,year in siteyears:
        k=(producer,project,lat,lon)
        if k not in earliest or year<earliest[k]:
            earliest[k]=year
    donor=[(*k,y) for k,y in earliest.items()]
    geos=np.asarray([xyz(r[2],r[3]) for r in donor],dtype=float)
    tree=cKDTree(geos)
    radii=[2*math.sin(km/(2*EARTH_KM)) for km in RADIUS_KM]
    target=[r for r in siteyears if TARGET_FIRST_YEAR<=r[4]<=LAST_YEAR]
    total=Counter()
    by_year={}
    for producer,project,lat,lon,year in target:
        label=str(year)
        if label not in by_year:
            by_year[label]=Counter()
        point=np.asarray(xyz(lat,lon),dtype=float)
        neighbors=tree.query_ball_point(point,radii[1])
        covered=dict((k,False) for k in (
            "any_different_project_100km","any_different_project_200km",
            "any_different_producer_100km","any_different_producer_200km"))
        for j in neighbors:
            srcprod,srcproj,_,_,firsty=donor[j]
            if firsty>=year or (srcprod,srcproj)==(producer,project):
                continue
            d=float(np.linalg.norm(geos[j]-point))
            # chord check is equivalent to geodesic radius under WGS84 sphere
            if d<=radii[1]+1e-15:
                covered["any_different_project_200km"]=True
                if srcprod!=producer:
                    covered["any_different_producer_200km"]=True
            if d<=radii[0]+1e-15:
                covered["any_different_project_100km"]=True
                if srcprod!=producer:
                    covered["any_different_producer_100km"]=True
            if all(covered.values()):break
        total["target_project_point_years"]+=1
        by_year[label]["target_project_point_years"]+=1
        for k,v in covered.items():
            if v:
                total[k]+=1
                by_year[label][k]+=1
    return {
        "source_eligible_observed_project_point_years":len(siteyears),
        "source_distinct_producer_project_point_locations":len(donor),
        "source_producer_project_pairs":len(set((r[0],r[1]) for r in siteyears)),
        "source_distinct_producer_ids":len(set(r[0] for r in siteyears)),
        "target_2016_2025_project_point_years":len(target),
        "target_with_historical_independent_project_within_100km":
            int(total["any_different_project_100km"]),
        "target_with_historical_independent_project_within_200km":
            int(total["any_different_project_200km"]),
        "target_with_historical_independent_PRODUCER_within_100km":
            int(total["any_different_producer_100km"]),
        "target_with_historical_independent_PRODUCER_within_200km":
            int(total["any_different_producer_200km"]),
        "historical_100km_independent_project_coverage_fraction":
            total["any_different_project_100km"]/max(len(target),1),
        "target_year_source_history_aggregate_only":{
            y:dict(sorted(c.items())) for y,c in sorted(by_year.items())},
        "original_source_species_or_taxon_occurrences_accessed":0,
        "original_uncaptured_zero_sampling_events_observed":False,
        "original_independent_physical_FORESTS_established":False,
        "species_specific_accessible_source_population_established":False
    }


def test():
    # Same project/repeated future donors excluded. Different project only
    # allowed with strictly earlier year, across original donor project source.
    demo=[
        ("A","a",46.0,2.0,2019),
        ("A","a",46.0,2.0,2022),
        ("A","b",46.3,2.2,2020),
        ("B","c",46.4,2.2,2021),
        ("A","d",46.35,2.25,2023),
        ("A","e",42.0,6.0,2023),
    ]
    r=match_history(demo)
    assert r["target_2016_2025_project_point_years"]==len(demo)
    # A/a 2019: no other project earlier; A/b 2020: A/a earlier; B/c
    # 2021 has previous DIFFERENT producer; A/d 2023 has both; A/e far.
    assert r["target_with_historical_independent_project_within_100km"]>=3
    assert r["target_with_historical_independent_PRODUCER_within_100km"]>=1
    assert geosource("46.7","2.3","point","500")[1]
    assert not geosource("46.7","2.3","centroid","500")[1]
    assert not geosource("46.7","2.3","point","")[1]
    assert not geosource("46.7","2.3","point","2500")[1]
    print("DATASAPROX_SOURCE_HISTORY_ONLY_NO_RESPONSE_SYNTHETIC_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--archive")
    p.add_argument("--out",default="datasaprox_historical_sourcepool_meta/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    if not a.archive:p.error("--archive with exact original v1.6 required")
    report={
      "schema":"structural.datasaprox_v1_6_historical_project_sampling_geometry_only.v1",
      "original_source_UUID":original.UUID,
      "original_original_archive_sha256":SHA,
      "original_dataset_license":"CC-BY-4.0",
      "response_beetle_species_taxon_abundance_rows_accessed":0,
      "original_source_raw_coordinates_projects_plotIDs_exported":False,
      "original_species_specific_occupied_donors_identified":False,
      "new_biological_effects_estimated":0,
      "previous_Datasaprox_vertical_stop_and_island_forests_results_unchanged":True,
      "status":"SOURCE_HISTORICAL_GEOGRAPHIC_META_UNOPENED",
    }
    try:
        z=read_original_meta(a.archive)
        siteyears=z.pop("eligible_unique_project_point_years")
        report["original_source_event_and_precision_gate"]=z
        report["historical_independent_project_survey_coverage"]=match_history(siteyears)
        report["status"]="SOURCE_ONLY_HISTORICAL_SURVEY_GEOGRAPHY_FEASIBILITY_PASS_NOT_SOURCE_POOL"
    except Exception as e:
        report["status"]="SOURCE_ORIGINAL_ARCHIVE_OR_GEO_TEMPORAL_SCHEMA_STOP"
        report["error_class"]=type(e).__name__
        report["error_code"]=str(e)[:165] if isinstance(e,ValueError) else ""
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("HISTORICAL_SURVEY_GEOGRAPHY_STATUS",report["status"])
    r=report.get("historical_independent_project_survey_coverage",{})
    print("ELIGIBLE_TARGET_POINT_YEARS",r.get("target_2016_2025_project_point_years",0))
    print("INDEPENDENT_PRIOR_PROJECT_WITHIN_100KM",
          r.get("target_with_historical_independent_project_within_100km",0))
    print("SOURCE_TAXA_RESPONSES_OPENED",report["response_beetle_species_taxon_abundance_rows_accessed"])

if __name__=="__main__":
    main()
