#!/usr/bin/env python3
"""Exploratory Thai beetle canopy-versus-understorey response using original DwC-A.

A forest-level comparison only: 2 independent forest locations, 9 paired
field stations each, seasons repeated. The primary 'Coleoptera' method is
SLAM aerial Malaise traps, two jars per trap; the Light and yellow FIT
strata are not silently pooled into the beetle denominator.
Taxon names below species rank do NOT become species richness; assemblage
summary uses valid family-level assignments. No causal or global inference.
"""
from __future__ import annotations
import argparse,hashlib,io,json,math,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from audit_thai_beetle_canopy_original import (
    UID,API,EVENT_TYPE,OCC_TYPE,fetch_json,get_archive_endpoint,
    download_small_archive,bare,definition,rows,col,stratum,strip_label
)
import xml.etree.ElementTree as ET

def protocol_category(v):
    x=strip_label(v)
    layer=stratum(x)
    if layer not in ("canopy","understorey"):return None,None
    if x.startswith("slam trap ("):return "SLAM",layer
    if x.startswith("light trap ("):return "LIGHT",layer
    if x.startswith("fit with yellow pan ("):return "YELLOW_FIT",layer
    return "OTHER",layer

def valid_family(name):
    t=str(name or "").strip()
    return t if t.endswith("idae") and len(t)>=6 and t[0].isupper() else None

def bray_relative(x,y):
    a=sum(x.values());b=sum(y.values())
    if not a or not b:return None
    return 0.5*sum(abs(x.get(z,0)/a-y.get(z,0)/b) for z in (x.keys()|y.keys()))

def original_tables(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        ml=[n for n in z.namelist() if n.rsplit("/",1)[-1]=="meta.xml"]
        if len(ml)!=1:raise ValueError("original_archive_meta_not_unique")
        root=ET.fromstring(z.read(ml[0]))
        c=[e for e in root if bare(e.tag)=="core"]
        x=[e for e in root if bare(e.tag)=="extension" and e.attrib.get("rowType")==OCC_TYPE]
        if len(c)!=1 or c[0].attrib.get("rowType")!=EVENT_TYPE or len(x)!=1:
            raise ValueError("expected_dwc_event_core_and_occurrence_extension")
        es,os=definition(z,c[0]),definition(z,x[0])
        return (
            [{**{q:col(row,es["fields"],q) for q in ("eventID","locationID","samplingProtocol",
              "sampleSizeUnit","sampleSizeValue","samplingEffort","eventDate",
              "parentEventID","decimalLatitude","decimalLongitude","dynamicProperties",
              "eventRemarks","locationRemarks","minimumElevationInMeters")},
              "_core_id":row[es["keyidx"]].strip()} for row in rows(z,es)],
            [{**{q:col(row,os["fields"],q) for q in ("family","scientificName",
               "individualCount","taxonRank")},
              "_core_id":row[os["keyidx"]].strip()} for row in rows(z,os)]
        )

def analyze(data):
    events,occs=original_tables(data)
    if len(events)!=288:raise ValueError("original_thai_event_number_drift")
    if len({e["_core_id"] for e in events})!=len(events):raise ValueError("event_core_duplicate")
    if len({e["eventID"] for e in events})!=len(events):raise ValueError("publisher_eventID_duplicate")
    byid={e["_core_id"]:e for e in events}
    protocols=Counter()
    denominators=Counter()
    effort=defaultdict(Counter)
    site_ids=set()
    for e in events:
        method,layer=protocol_category(e["samplingProtocol"])
        if method is None:raise ValueError("unknown_original_canopy_stratum")
        e["_method"]=method;e["_layer"]=layer
        loc=e["locationID"]
        if not loc:raise ValueError("original_forest_identity_missing")
        site_ids.add(loc)
        protocols[e["samplingProtocol"]]+=1
        denominators[method,layer]+=1
        effort[method,layer]["events"]+=1
        if e["sampleSizeValue"]:effort[method,layer]["sample_size_value_present"]+=1
        if e["samplingEffort"]:effort[method,layer]["sampling_effort_present"]+=1
        if e["sampleSizeUnit"]:effort[method,layer]["sample_size_unit_present"]+=1
    if len(site_ids)!=2:raise ValueError("two_original_forest_networks_expected")
    for layer in ("canopy","understorey"):
        if denominators["SLAM",layer]!=72:raise ValueError("unequal_slAM_event_effort_by_stratum")
    raw_counts=Counter()
    family_counts=defaultdict(Counter)
    records=Counter()
    ranks=Counter()
    unknown_family_rows=Counter()
    for row in occs:
        e=byid.get(row["_core_id"])
        if e is None:raise ValueError("orphan_original_occurrence_coreid")
        method,layer=e["_method"],e["_layer"]
        try:
            n=float(row["individualCount"])
        except ValueError:
            raise ValueError("original_occurrence_invalid_individualCount")
        if not n.is_integer() or n<1:raise ValueError("non_positive_or_fractional_beetle_individualCount")
        n=int(n)
        group=e["locationID"],method,layer
        raw_counts[group]+=n
        records[group]+=1
        ranks[strip_label(row["taxonRank"]) or "missing"]+=1
        f=valid_family(row["family"])
        if f:family_counts[group][f]+=n
        else:unknown_family_rows[group]+=1
    if sum(raw_counts.values())!=1622:raise ValueError("published_beetle_total_1622_not_reproduced")
    if any(method!="SLAM" for _,method,_ in raw_counts):
        raise ValueError("non_SLAM_beetle_specimens_present_requires_method_gate")
    forest_out=[]
    pooled={s:Counter() for s in ("canopy","understorey")}
    for forest in sorted(site_ids):
        a=family_counts[forest,"SLAM","canopy"]
        b=family_counts[forest,"SLAM","understorey"]
        pooled["canopy"].update(a);pooled["understorey"].update(b)
        forest_out.append({
          "anonymous_forest_index":len(forest_out)+1,
          "canopy_SLAM_jar_events":sum(e["_method"]=="SLAM" and e["_layer"]=="canopy" and e["locationID"]==forest for e in events),
          "understorey_SLAM_jar_events":sum(e["_method"]=="SLAM" and e["_layer"]=="understorey" and e["locationID"]==forest for e in events),
          "canopy_individuals":raw_counts[forest,"SLAM","canopy"],
          "understorey_individuals":raw_counts[forest,"SLAM","understorey"],
          "canopy_occurrence_rows":records[forest,"SLAM","canopy"],
          "understorey_occurrence_rows":records[forest,"SLAM","understorey"],
          "canopy_identified_families":len(a),
          "understorey_identified_families":len(b),
          "shared_identified_families":len(a.keys()&b.keys()),
          "exclusive_canopy_family_labels":len(a.keys()-b.keys()),
          "exclusive_understorey_family_labels":len(b.keys()-a.keys()),
          "family_composition_relative_abundance_BrayCurtis":bray_relative(a,b),
          "individual_count_rate_ratio_canopy_over_understorey_equal_jar_events":(
              raw_counts[forest,"SLAM","canopy"]/raw_counts[forest,"SLAM","understorey"]
              if raw_counts[forest,"SLAM","understorey"] else None)
        })
    canopy=sum(v["canopy_individuals"] for v in forest_out)
    lower=sum(v["understorey_individuals"] for v in forest_out)
    rank_species=ranks.get("species",0)
    ca,un=pooled["canopy"],pooled["understorey"]
    fam_diff=[]
    for f in sorted(ca.keys()|un.keys()):
        fam_diff.append({"family":f,"canopy_individuals":ca[f],"understorey_individuals":un[f],
                         "canopy_minus_understorey":ca[f]-un[f]})
    fam_diff.sort(key=lambda x:-abs(x["canopy_minus_understorey"]))
    result={
      "schema":"structural.thai_forest_beetle_canopy_SLAM_original_response.v1",
      "source_gbif_dataset_key":UID,
      "source_original_sha256":hashlib.sha256(data).hexdigest(),
      "source_field_original_event_count":len(events),
      "source_original_occurrence_rows":len(occs),
      "published_beetle_specimens_reproduced":canopy+lower,
      "unique_forest_study_regions":len(site_ids),
      "original_9_sampling_points_per_forest":True,
      "SLAM_jar_events_per_layer":dict((z,denominators["SLAM",z]) for z in ("canopy","understorey")),
      "canopy_SLAM_beetle_individuals":canopy,
      "understorey_SLAM_beetle_individuals":lower,
      "canopy_vs_understorey_ratio_individuals_equal_jar_events":canopy/lower if lower else None,
      "canopy_vs_understorey_difference_in_individuals":canopy-lower,
      "canopy_family_labels_count":len(ca),
      "understorey_family_labels_count":len(un),
      "shared_family_labels_count":len(ca.keys()&un.keys()),
      "canopy_only_family_labels":len(ca.keys()-un.keys()),
      "understorey_only_family_labels":len(un.keys()-ca.keys()),
      "pooled_family_relative_abundance_BrayCurtis":bray_relative(ca,un),
      "original_taxonRank_species_OCCURRENCE_ROWS_not_species_count":rank_species,
      "species_level_richness_estimable_from_publisher_rows":False,
      "sampling_effort_field_coverage":{
          method+"|"+layer:dict(v) for (method,layer),v in effort.items()},
      "original_arthropod_source_methods_with_specimens":["SLAM"],
      "rank_distribution":dict(ranks),
      "unresolved_family_occurrence_rows":sum(unknown_family_rows.values()),
      "original_forest_stratum_summaries":forest_out,
      "largest_family_differences":fam_diff[:12],
      "data_release_covers_only_two_forest_regions":True,
      "causal_canopy_height_effect_estimated":False,
      "cross_biome_replication_estimated":False,
      "paired_stations_temporal_dependence_not_yet_modeled":True,
      "no_raw_coordinates_or_source_eventIDs_exported":True
    }
    return result

def run(out,request=fetch_json,download=download_small_archive):
    ds=request(API+UID)
    if str(ds.get("key"))!=UID:raise ValueError("GBIF_source_UUID_mismatch")
    license=str(ds.get("license") or "")
    if license.lower() not in ("cc_by_4_0","http://creativecommons.org/licenses/by/4.0/legalcode",
                             "https://creativecommons.org/licenses/by/4.0/legalcode"):
        raise ValueError("GBIF_CC_BY_license_expected")
    data=download(get_archive_endpoint(ds))
    result=analyze(data)
    dst=Path(out);dst.mkdir(parents=True,exist_ok=True)
    (dst/"thai_beetle_canopy_SLAM_forest_family_results.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args();run(a.out)
