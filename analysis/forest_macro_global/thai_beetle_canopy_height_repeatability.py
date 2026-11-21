#!/usr/bin/env python3
"""Original Event-only canopy trap height stability across Thai sampling seasons.

This diagnoses whether one stable canopy trap-height predictor can be attached
to each physical station. It does NOT open beetle Occurrence extensions.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,statistics
from collections import Counter,defaultdict
from pathlib import Path

from thai_beetle_thermal_height_gate import (
    UID, API, SOURCE_SHA, fetch_json, get_archive_endpoint,
    download_small_archive, source_event_rows, extract_named_numeric,
    CANOPY_HEIGHT_NAMES, protocol_category
)
from thai_beetle_pairing_diagnostic import campaigns


def height_of(e):
    vals=[]
    for field in ("dynamicProperties","eventRemarks","locationRemarks"):
        for key,v in extract_named_numeric(e.get(field)):
            if key in CANOPY_HEIGHT_NAMES:vals.append(round(float(v),3))
    if len(set(vals))!=1:
        raise ValueError("source_Event_trap_height_missing_or_ambiguous")
    h=vals[0]
    if not 1<=h<=60:raise ValueError("source_trap_height_out_of_range")
    return h


def audit(events):
    if len(events)!=288:raise ValueError("original_Event_total_drift")
    byf=defaultdict(list)
    methods=Counter()
    for e in events:
        method,layer=protocol_category(e["samplingProtocol"])
        if method is None:raise ValueError("source_unrecognized_sampling_protocol")
        methods[method,layer]+=1
        if method!="SLAM":continue
        f=e.get("locationID")
        date=e.get("eventDate")
        if not f or not date:raise ValueError("source_no_forest_or_census_date")
        try:
            pos=(round(float(e["decimalLatitude"]),6),round(float(e["decimalLongitude"]),6))
        except (TypeError,ValueError):
            raise ValueError("source_missing_original_coordinate")
        byf[f].append((e,layer,pos,datetime.date.fromisoformat(date[:10]),height_of(e)))
    if len(byf)!=2:raise ValueError("exactly_two_original_forests_required")
    perforest=[]
    site_change_deltas=[]
    canopy_heights=[]
    under_heights=[]
    for f,rr in sorted(byf.items()):
        dates,clusters=campaigns([str(q[3]) for q in rr])
        if len(clusters)!=2:raise ValueError("source_campaigns_not_two")
        which={day:i for i,mapping in enumerate(dates) for day in mapping}
        strata=defaultdict(list)
        for e,layer,pos,day,h in rr:
            strata[(layer,pos,which[day])].append(h)
            if layer=="understorey":under_heights.append(h)
            else:canopy_heights.append(h)
        for layer in ("understorey","canopy"):
            positions={key[1] for key in strata if key[0]==layer}
            if len(positions)!=9:raise ValueError("expected_nine_sites_in_each_layer")
            for pos in positions:
                for phase in range(2):
                    vals=strata.get((layer,pos,phase),[])
                    if len(vals)!=2:raise ValueError("missing_top_bottom_jar_for_site_phase")
                    if max(vals)-min(vals)>2:
                        raise ValueError("jar_pair_height_disagreement")
        ca=sorted({key[1] for key in strata if key[0]=="canopy"})
        deltas=[]
        for pos in ca:
            h1=statistics.mean(strata["canopy",pos,0])
            h2=statistics.mean(strata["canopy",pos,1])
            delta=abs(h2-h1)
            deltas.append(delta)
            site_change_deltas.append(delta)
        perforest.append({
            "anonymous_forest":len(perforest)+1,
            "physical_canopy_station_n":len(ca),
            "median_absolute_height_change_between_campaigns_m":statistics.median(deltas),
            "max_absolute_height_change_m":max(deltas),
            "sites_height_change_gt4m":sum(x>4 for x in deltas),
            "sites_height_change_gt2m":sum(x>2 for x in deltas)
        })
    if any(abs(h-2)>.2 for h in under_heights):
        raise ValueError("understorey_height_unexpected")
    return {
      "schema":"structural.thai_canopy_beetle_original_trap_height_repeatability.v1",
      "original_source_archive_sha256":SOURCE_SHA,
      "original_Event_rows":len(events),
      "SLAM_jar_Event_rows":sum(v for (method,layer),v in methods.items() if method=="SLAM"),
      "original_forest_n":len(byf),
      "physical_canopy_station_n":sum(x["physical_canopy_station_n"] for x in perforest),
      "canopy_trap_measured_height_min_m":min(canopy_heights),
      "canopy_trap_measured_height_max_m":max(canopy_heights),
      "understorey_trap_height_m":statistics.median(under_heights),
      "median_absolute_canopy_height_shift_per_station_m":statistics.median(site_change_deltas),
      "max_absolute_canopy_height_shift_per_station_m":max(site_change_deltas),
      "sites_canopy_trap_height_change_gt4m":sum(x>4 for x in site_change_deltas),
      "sites_canopy_trap_height_change_gt2m":sum(x>2 for x in site_change_deltas),
      "constant_canopy_height_per_station_site_level_model_eligible":
          all(x<=4 for x in site_change_deltas),
      "forest_source_summary":perforest,
      "original_beetle_Occurrence_extension_rows_read":0,
      "temporal_height_variation_not_assumed_station_constant":True,
      "no_thermal_movement_or_causal_effect_scored":True,
      "no_source_coordinates_or_plotIDs_exported":True
    }


def run(out,request=fetch_json,download=download_small_archive):
    ds=request(API+UID)
    if str(ds.get("key"))!=UID:raise ValueError("source_identity_changed")
    license=str(ds.get("license") or "").lower()
    if license not in ("cc_by_4_0","http://creativecommons.org/licenses/by/4.0/legalcode",
                       "https://creativecommons.org/licenses/by/4.0/legalcode"):
        raise ValueError("original_dataset_license_changed")
    data=download(get_archive_endpoint(ds))
    if hashlib.sha256(data).hexdigest()!=SOURCE_SHA:
        raise ValueError("source_original_version_drift")
    report=audit(source_event_rows(data,include_internal_geometry=True))
    dest=Path(out);dest.mkdir(parents=True,exist_ok=True)
    (dest/"thai_canopy_height_repeatability_Event_only.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    opt=parser.parse_args()
    run(opt.out)
