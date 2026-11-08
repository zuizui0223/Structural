#!/usr/bin/env python3
"""Original Thai forest beetle Event-only trap-height / thermal metadata gate.

The published 2024 article measured paired canopy/understory HOBO hourly air
temperature and light (doi:10.1002/inc3.76), but this does not imply the time
series is distributed in the GBIF sampling-event archive. Check that separately.
Read the *Event* core only, not the beetle occurrence species/abundance.
No original field text, coordinates, site names or Event IDs are exported.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter,defaultdict
from pathlib import Path

from audit_thai_beetle_canopy_original import (
    UID, API, EVENT_TYPE, bare, definition, rows, col,
    fetch_json, get_archive_endpoint, download_small_archive
)
from thai_beetle_canopy_family_response import protocol_category

SOURCE_SHA="1565cf6d7f1e7289e28756367e3d137f64723dc1fa0a06d799f6abdb523e1339"
KNOWN_FIELDS=("dynamicProperties","eventRemarks","locationRemarks",
              "minimumElevationInMeters","maximumElevationInMeters",
              "samplingProtocol","samplingEffort","sampleSizeUnit")
CANOPY_HEIGHT_NAMES={"canopytrapheight","trapheight","trapheightm","heightoftrap","trapheightmeters","trapsuspensionheight"}
AMBIENT_T_NAMES={"airtemperature","airtemperaturec","temperaturec","ambienttemperature","meanairtemperature"}
LIGHT_NAMES={"lightintensity","lux","lightintensitylux","illuminationlux"}


def normal_key(t):
    return re.sub(r"[^a-z0-9]","",str(t or "").lower())


def parse_numeric(v):
    if isinstance(v,(int,float)):
        num=float(v)
    else:
        s=str(v or "").strip()
        match=re.fullmatch(r"([-+]?\d+(?:\.\d+)?)\s*(?:°?\s*C|m|metres?|meters?|lux)?",s,re.I)
        if not match:return None
        num=float(match.group(1))
    return num if math.isfinite(num) else None


def extract_named_numeric(text):
    """Parse only unambiguous key/value pairs; no free-floating numbers."""
    text=str(text or "").strip()
    if not text:return []
    def flatten(v):
        if isinstance(v,dict):
            for k,entry in v.items():
                if isinstance(entry,dict):yield from flatten(entry)
                else:yield normal_key(k),parse_numeric(entry)
        elif isinstance(v,list):
            for entry in v:yield from flatten(entry)
    try:
        item=json.loads(text)
    except (ValueError,TypeError):
        item=None
    if item is not None:
        return [(k,v) for k,v in flatten(item) if v is not None]
    out=[]
    # Conservative English metadata phrases with the unit specified or a
    # key/value delimiter. Height mentioned in forest descriptions is excluded.
    for match in re.finditer(
        r"(?i)\b(trap(?:\s+height)?|height\s+of\s+(?:the\s+)?trap|"
        r"air\s+temperature|ambient\s+temperature|light\s+intensity|lux)\b"
        r"\s*(?:\(\s*(?:m|meters?|°?C|lux)\s*\))?\s*[:=]\s*"
        r"([-+]?\d+(?:\.\d+)?)\s*(m|°?C|lux)?",text):
        key=normal_key(match.group(1))
        v=parse_numeric(match.group(2))
        if v is not None:
            out.append((key,v))
    return out


def source_event_rows(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        ml=[n for n in z.namelist() if n.rsplit("/",1)[-1]=="meta.xml"]
        if len(ml)!=1:raise ValueError("archive_meta_not_unique")
        root=ET.fromstring(z.read(ml[0]))
        cores=[e for e in root if bare(e.tag)=="core"]
        if len(cores)!=1 or cores[0].attrib.get("rowType")!=EVENT_TYPE:
            raise ValueError("original_core_not_Event")
        spec=definition(z,cores[0])
        return [
            {name:col(r,spec["fields"],name) for name in KNOWN_FIELDS}
            for r in rows(z,spec)
        ]


def audit_rows(events):
    if len(events)!=288:raise ValueError("original_event_count_not_288")
    coverage=defaultdict(Counter)
    height_values=defaultdict(list)
    temp_values=defaultdict(list)
    light_values=defaultdict(list)
    key_presence=defaultdict(Counter)
    season_strata=Counter()
    field_keyword_counts=defaultdict(Counter)
    dynamic_json_count=0
    for e in events:
        method,layer=protocol_category(e["samplingProtocol"])
        if method not in ("SLAM","LIGHT","YELLOW_FIT") or layer not in ("canopy","understorey"):
            raise ValueError("original_sampling_protocol_unrecognized")
        tag=f"{method}|{layer}"
        coverage[tag]["event_rows"]+=1
        for field in KNOWN_FIELDS:
            if e.get(field):coverage[tag][f"field_{field}_nonempty"]+=1
        # Only metadata linked to the specific Event. No inferred hourly loggers.
        named=[]
        for field in ("dynamicProperties","eventRemarks","locationRemarks"):
            value=str(e.get(field) or "")
            lowered=value.lower()
            for term in ("height","trap","above ground","meter","metre",
                         "temperature","temp","thermal","light","lux","sensor","logger"):
                if term in lowered:
                    field_keyword_counts[field][term]+=1
            if field=="dynamicProperties" and value:
                try:
                    if isinstance(json.loads(value),(dict,list)):
                        dynamic_json_count+=1
                except (ValueError,TypeError):
                    pass
            named.extend(extract_named_numeric(value))
        for key,val in named:
            if key in CANOPY_HEIGHT_NAMES:
                if 1<=val<=75:
                    height_values[tag].append(val)
                    key_presence[tag]["explicit_trap_height"]+=1
            elif key in AMBIENT_T_NAMES:
                if -20<=val<=60:
                    temp_values[tag].append(val)
                    key_presence[tag]["event_numeric_air_temperature"]+=1
            elif key in LIGHT_NAMES:
                if 0<=val<=250000:
                    light_values[tag].append(val)
                    key_presence[tag]["event_numeric_light"]+=1
    def stats(vals):
        if not vals:return {"source_rows":0,"min":None,"median":None,"max":None}
        return {"source_rows":len(vals),"min":min(vals),
                "median":statistics.median(vals),"max":max(vals)}
    tags=sorted(coverage)
    report={
        "schema":"structural.thai_beetle_original_event_microclimate_height_gate.v1",
        "original_event_rows":len(events),
        "independent_original_forests_from_methods":2,
        "source_event_metadata_field_coverage":{t:dict(coverage[t]) for t in tags},
        "event_metadata_allowlisted_keyword_counts_by_source_field":{k:dict(v) for k,v in field_keyword_counts.items()},
        "dynamicProperties_JSON_object_or_array_rows":dynamic_json_count,
        "explicit_numeric_trap_height_by_event_method_layer":{
            t:stats(height_values[t]) for t in tags},
        "explicit_numeric_event_air_temperature_by_method_layer":{
            t:stats(temp_values[t]) for t in tags},
        "explicit_numeric_event_light_by_method_layer":{
            t:stats(light_values[t]) for t in tags},
        "original_hobo_hourly_logger_timeseries_extracted_from_Event_core":False,
        "original_paper_describes_hobo_temperature_and_lux_but_not_verified_in_this_archive":True,
        "canopy_trap_height_hypothesis_estimable_from_source_Event_metadata":(
            len(height_values["SLAM|canopy"])>=36 and len(height_values["SLAM|understorey"])>=36),
        "source_timeseries_thermal_escape_test_eligible":False,
        "beetle_occurrence_species_or_abundance_rows_read":0,
        "all_raw_site_ids_text_coordinates_suppressed":True,
        "new_thermal_effect_estimated":False
    }
    return report


def run(out,request=fetch_json,download=download_small_archive):
    meta=request(API+UID)
    if str(meta.get("key"))!=UID:raise ValueError("dataset_uuid_mismatch")
    license=str(meta.get("license") or "").lower()
    if license not in ("cc_by_4_0","http://creativecommons.org/licenses/by/4.0/legalcode",
                       "https://creativecommons.org/licenses/by/4.0/legalcode"):
        raise ValueError("original_source_license_changed")
    data=download(get_archive_endpoint(meta))
    if hashlib.sha256(data).hexdigest()!=SOURCE_SHA:
        raise ValueError("original_source_archive_hash_changed")
    results=audit_rows(source_event_rows(data))
    results["original_source_archive_sha256"]=SOURCE_SHA
    dest=Path(out);dest.mkdir(parents=True,exist_ok=True)
    (dest/"thai_beetle_original_height_temperature_availability.json").write_text(
        json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(results,ensure_ascii=False,indent=2))
    return results


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    run(args.out)
