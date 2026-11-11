#!/usr/bin/env python3
"""THERA: outcome-unopened 20-plot geographical support and taxon-schema gate.

Read ONLY source event IDs, sampling original plot, decimal coordinates, and
DwC-A META.XML FIELD NAMES (never scientific names, taxa, occurrences or counts).
All coordinates and sample identifiers remain inside GitHub Actions runner.
Haversine proximity is a geometric diagnostic, NOT proof of independent forests.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,statistics,zipfile
from collections import defaultdict
from pathlib import Path
from datasaprox_project_method_table7_gate import source_sample_events
from datasaprox_thera_subplots_gate import TARGET,source_optional_field_metadata
from datasaprox_source_metadata_gate import schema

FIELDS={
 "scientificName","taxonID","taxonRank","specificEpithet","genus",
 "occurrenceStatus","individualCount","organismQuantity",
 "identificationQualifier","identificationRemarks","basisOfRecord",
 "decimalLatitude","decimalLongitude","coordinateUncertaintyInMeters"
}
RADII_KM=(0.5,1,5,20)
def haversine(a,b):
    p,q=map(math.radians,(a[0],b[0]))
    dlat=q-p;dlon=math.radians(b[1]-a[1])
    h=math.sin(dlat/2)**2+math.cos(p)*math.cos(q)*math.sin(dlon/2)**2
    return 6371.0088*2*math.asin(min(1.,math.sqrt(h)))

def balanced_source_plots(events,bad,extra):
    groups=defaultdict(lambda:{"upper":[],"lower":[]})
    for k,v in events.items():
        if k[:2]!=TARGET or k in bad or len(extra.get(k,set()))!=1:continue
        stratum,plot,model,typ,cond,bait,colour,yearmonth,days=v
        if stratum not in ("upper","lower") or not(plot and model and yearmonth and days is not None):
            continue
        name=next(iter(extra[k]))[2]
        g=(plot,yearmonth,model,typ,bait,colour)
        groups[g][stratum].append((k,days,name))
    balanced={}
    for g,layers in groups.items():
        up=layers["upper"];lo=layers["lower"]
        if len(up)!=2 or len(lo)!=2:continue
        all_four=up+lo
        if not all(7<=v[1]<=35 and v[2] for v in all_four):continue
        if max(v[1] for v in all_four)-min(v[1] for v in all_four)>7:continue
        if len({v[2] for v in all_four})!=4:continue
        balanced[g]=all_four
    return balanced

def study_spatial_qc(balanced,event_coords,coordinate_conflict_events):
    plots={g[0] for g in balanced}
    plot_event_ids=defaultdict(set)
    for g,all_four in balanced.items():
        for key,days,name in all_four:plot_event_ids[g[0]].add(key)
    medians={};spread=[];missing=0;fieldplot_bad=0
    for plot,ev in plot_event_ids.items():
        if ev & coordinate_conflict_events:
            fieldplot_bad+=1
            continue
        coords=[event_coords[k] for k in ev if k in event_coords]
        if len(coords)<len(ev):missing+=1
        if not coords:continue
        med=(statistics.median(c[0] for c in coords),
             statistics.median(c[1] for c in coords))
        medians[plot]=med
        spread.append(max(haversine(med,c) for c in coords))
    points=list(medians.values())
    distances=[haversine(points[i],points[j])
               for i in range(len(points)) for j in range(i+1,len(points))]
    def components(r):
        parent=list(range(len(points)))
        def find(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]]
                i=parent[i]
            return i
        for i in range(len(points)):
            for j in range(i+1,len(points)):
                if haversine(points[i],points[j])<=r:
                    parent[find(i)]=find(j)
        return len({find(i) for i in range(len(points))})
    return {
        "source_balanced_four_trap_plot_month_units":len(balanced),
        "source_distinct_balanced_original_field_plot_keys":len(plots),
        "source_balanced_original_plot_keys_with_coordinate_evidence":len(medians),
        "source_balanced_original_plot_keys_with_missing_event_coordinates":missing,
        "source_balanced_original_plot_keys_with_conflicting_event_coordinates":fieldplot_bad,
        "source_plot_maximum_within_plot_event_offset_km_median":(
            statistics.median(spread) if spread else None),
        "source_plot_maximum_within_plot_event_offset_km_max":max(spread) if spread else None,
        "source_pairwise_original_plot_centroid_distance_km_median":(
            statistics.median(distances) if distances else None),
        "source_pairwise_original_plot_centroid_distance_km_min":min(distances) if distances else None,
        "source_pairwise_original_plot_centroid_distance_km_max":max(distances) if distances else None,
        "source_plot_center_connected_components_at_0p5_1_5_20_km":{
            str(x):components(x) for x in RADII_KM},
        "source_coordinates_alone_do_not_certify_independent_forests":True,
        "source_georeferencing_accuracy_not_verified":True,
        "source_original_response_taxon_values_read":False,
        "source_locations_and_original_site_ids_NOT_EXPORTED":True,
    }

def audit(archive):
    events,bad,n=source_sample_events(archive)
    extra=source_optional_field_metadata(archive,events,bad)
    balanced=balanced_source_plots(events,bad,extra)
    if len(balanced)>55 or len({g[0] for g in balanced})>20:
        raise ValueError("STOP_THERA_ORIGINAL_FOUR_TRAP_SUPPORT_INFLATION")
    strict_all_four_effort_denominator=len(balanced)
    strict_original_plot_denominator=len({g[0] for g in balanced})
    selected={k for four in balanced.values() for k,_,_ in four}
    coords={};conflicts=set()
    with zipfile.ZipFile(archive) as z:
        src=schema(z);fields=src["fields"]
        schema_avail={k:k in fields for k in sorted(FIELDS)}
        if not all(schema_avail.get(k,False) for k in ("decimalLatitude","decimalLongitude")):
            return {"status":"STOP_THERA_SOURCE_EVENT_GEO_FIELDS_NOT_FOUND",
                    "source_original_taxonomic_field_presence_only":schema_avail,
                    "source_species_values_read":False}
        required=("eventID","ownerInstitutionCode","datasetName",
                  "decimalLatitude","decimalLongitude")
        if any(k not in fields for k in required):
            raise ValueError("STOP_EVENT_IDENTITY_GEO_SCHEMA_DRIFT")
        with z.open(src["file"]) as binary:
            file=io.TextIOWrapper(binary,encoding="utf-8-sig",newline="")
            reader=csv.reader(file,delimiter=src["delimiter"],quotechar=src["quote"] or '"',
                 quoting=csv.QUOTE_MINIMAL if src["quote"] else csv.QUOTE_NONE)
            for _ in range(src["header"]):next(reader)
            for row in reader:
                if not row:continue
                def val(k):
                    i=fields[k];return row[i].strip() if i<len(row) else ""
                if (val("ownerInstitutionCode"),val("datasetName"))!=TARGET:continue
                k=(*TARGET,val("eventID"))
                if k not in selected:continue
                try:
                    lat,lon=float(val("decimalLatitude")),float(val("decimalLongitude"))
                except ValueError:continue
                if not(math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180):
                    continue
                xy=(lat,lon)
                if k in coords and haversine(coords[k],xy)>0.0002:
                    conflicts.add(k)
                else:coords.setdefault(k,xy)
    geo=study_spatial_qc(balanced,coords,conflicts)
    return {
      "schema":"structural.datasaprox_THERA_outcome_unopened_spatial_taxon_schema_gate.v1",
      "status":"SCHEMA_AND_SITE_GEOGRAPHY_AUDITED_WITHOUT_SPECIES_RESPONSE",
      "source_original_records_metadata_streamed":n,
      "source_original_archive_SHA256":hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
      "original_source_taxonomic_field_presence_only":schema_avail,
      "four_trap_all_original_duration_within_7_days_paired_period_count":strict_all_four_effort_denominator,
      "strict_balanced_paired_periods_retain_original55_count":strict_all_four_effort_denominator==55,
      "four_trap_all_duration_strict_source_plot_count":strict_original_plot_denominator,
      "strict_all_four_source_effort_is_additional_pre_response_attrition":True,
      "selected_original_four_trap_event_ID_count":len(selected),
      "selected_original_source_event_coordinate_conflict_count":len(conflicts),
      **geo,
    }

def main(archive,out):
    result=audit(archive)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"datasaprox_thera_spatial_taxon_schema_gate.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--archive",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    main(args.archive,args.out)
