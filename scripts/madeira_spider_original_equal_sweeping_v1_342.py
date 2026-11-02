#!/usr/bin/env python3
"""Madeira spiders v1.342: author Event-only physical plot and common sweep effort.

Official v1.8 ZIP and meta.xml plus original Event core member ONLY.
Original 3281 Occurrence species/biogeographic records remain UNOPENED.
The 12 Madeira forest vs 5 Madeira dry comparison is observational,
as forest August 2016 versus dry April 2017 are fully confounded in time.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,unicodedata,urllib.request,zipfile
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=spiders_madeira&v=1.8"
SHA="e6703c8e0c74bb65f93bd54993a27628a3b800d97a8a21cec19855c500db438d"
MAX_BYTES=400000

def local(tag):return tag.rsplit("}",1)[-1]
def term(uri):return uri.rstrip("/").split("/")[-1].split("#")[-1]
def canon(s):
    t=unicodedata.normalize("NFKD",str(s or ""))
    t="".join(c for c in t if not unicodedata.combining(c)).casefold()
    return " ".join(re.sub(r"[^a-z0-9]+"," ",t).split())
def plot_id(s):
    return "".join(c.upper() for c in canon(s) if c.isascii() and c.isalnum())
def island(s):
    t=canon(s)
    if t=="madeira":return "Madeira"
    if t=="porto santo" or t=="portosanto":return "Porto_Santo"
    return None
def habitat(s,contract):
    v=canon(s)
    h=contract["physical_site_rule"]
    f={canon(x) for x in h["forest_habitat_source_exact"]}
    d={canon(x) for x in h["dry_habitat_source_exact"]}
    return "forest" if v in f else "dry" if v in d else None
def sweep(s,contract):
    v=canon(s)
    labels=contract["sampling"]["source_method_parser"]
    # Source-independent explicit synonyms fixed in prose.
    day={"day sweeping","sweeping day","day sweep","sweep day","ds","d sweep"}
    night={"night sweeping","sweeping night","night sweep","sweep night","ns","n sweep"}
    return "DAY_SWEEP" if v in day else "NIGHT_SWEEP" if v in night else "OTHER"

def original_event_core_only(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        core=[x for x in root if local(x.tag)=="core"]
        if len(core)!=1:raise ValueError("Original Madeira source has no unique Event core")
        node=core[0];fields={};paths=[];ident=None
        for x in node.iter():
            key=local(x.tag)
            if key=="field" and "term" in x.attrib and "index" in x.attrib:
                fields[term(x.attrib["term"])]=int(x.attrib["index"])
            elif key=="location" and x.text:paths.append(x.text.strip())
            elif key=="id" and "index" in x.attrib:ident=int(x.attrib["index"])
        required={"locationID","island","habitat","samplingProtocol","eventDate"}
        if ident is None or len(paths)!=1 or not required.issubset(fields):
            raise ValueError("Original Event source lacks author site/method/habitat/time")
        delim=node.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        head=int(node.attrib.get("ignoreHeaderLines","0"))
        if len(delim)!=1 or head not in (0,1):
            raise ValueError("Unknown original Event delimiter/header format")
        out=[]
        with z.open(paths[0]) as stream:
            with io.TextIOWrapper(stream,encoding="utf-8-sig",newline="") as f:
                records=csv.reader(f,delimiter=delim)
                for _ in range(head):next(records,None)
                for row in records:
                    if not row or not any(row):continue
                    if max(ident,*(fields[x] for x in required))>=len(row):
                        raise ValueError("Original source Event row shorter than declared schema")
                    obj={key:row[pos] for key,pos in fields.items() if pos<len(row)}
                    obj["__source_coreid"]=row[ident]
                    out.append(obj)
        return out

def audit(rows,contract):
    if len(rows)!=562:raise ValueError("Original Madeira source Event denominator not 562")
    sites=defaultdict(list);seen=set();problems=Counter();vocab=Counter()
    for row in rows:
        core=str(row.get("__source_coreid","")).strip()
        if not core or core in seen:raise ValueError("Original author Event ID duplicated or absent")
        seen.add(core)
        isl=island(row.get("island"))
        site=plot_id(row.get("locationID"))
        typ=habitat(row.get("habitat"),contract)
        smp=sweep(row.get("samplingProtocol"),contract)
        vocab[canon(row.get("samplingProtocol"))]+=1
        if isl is None or not site:
            problems["unknown_author_island_or_plot"]+=1;continue
        if typ is None:problems["unknown_author_habitat"]+=1
        dates=str(row.get("eventDate","")).strip()
        match=re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:$|[/T ])",dates)
        if not match:problems["unparseable_original_date"]+=1;year=None
        else:year=int(match.group(1))
        if year is not None and str(row.get("year","")).strip() not in ("",str(year)):
            problems["year_date_disagree"]+=1
        if year is not None:
            expected=2016 if (isl,typ)==("Madeira","forest") else 2017
            if year!=expected:problems["original_habitat_source_survey_year_unexpected"]+=1
        # Source coordinates are an independent metadata quality check.
        try:
            lat=float(row.get("decimalLatitude"));lon=float(row.get("decimalLongitude"))
        except (ValueError,TypeError):lat=lon=math.nan
        if not (math.isfinite(lat) and math.isfinite(lon)):
            problems["source_missing_coordinates"]+=1
        sample_size=canon(row.get("sampleSizeValue"))
        sample_unit=canon(row.get("sampleSizeUnit"))
        effort=canon(row.get("samplingEffort"))
        if smp in ("DAY_SWEEP","NIGHT_SWEEP"):
            # Original source may put the 1-hour duration in either
            # sampleSizeValue/Unit or the plain original samplingEffort.
            # Never manufacture durations from a taxon record.
            if sample_size and sample_unit:
                try:actual=float(sample_size)
                except ValueError:actual=math.nan
                if not math.isfinite(actual) or actual!=1 or sample_unit not in ("hour","hours","h"):
                    problems["sweep_original_duration_different_from_one_hour"]+=1
            elif effort and not ("1 hour" in effort or "60 min" in effort or effort=="1 h"):
                # Only a source field explicitly expressing one hour passes.
                problems["sweep_original_duration_unverifiable"]+=1
        sites[(isl,site)].append({
            "core":core,"habitat":typ,"method":smp,
            "year":year,"lat":lat,"lon":lon
        })
    group_sites=Counter();conflicts=Counter()
    selected=[];selected_sites=set();methods_by_plot=defaultdict(Counter)
    group_years=defaultdict(Counter)
    for (isl,site),records in sorted(sites.items()):
        kinds={r["habitat"] for r in records}
        if len(kinds)!=1 or None in kinds:
            conflicts["source_site_habitat_not_unique"]+=1;continue
        typ=next(iter(kinds))
        group=(isl+"_"+typ)
        group_sites[group]+=1
        coords=records[0]
        if any(not math.isfinite(r["lat"]) or not math.isfinite(r["lon"]) or
               max(abs(r["lat"]-coords["lat"]),abs(r["lon"]-coords["lon"]))>0.0003
               for r in records):
            conflicts["within_site_original_coordinates_conflict"]+=1
        for r in records:
            methods_by_plot[group][r["method"]]+=1
            if r["year"] is not None:group_years[group][str(r["year"])]+=1
        for mode in ("DAY_SWEEP","NIGHT_SWEEP"):
            original=sorted(r["core"] for r in records if r["method"]==mode)
            if len(original)<2:
                conflicts["source_plot_insufficient_common_"+mode]+=1
            else:
                selected.extend(original[:2])
        selected_sites.add((isl,site))
    expected=contract["physical_site_rule"]["source_plot_frame_expected"]
    eligible=(
        len(sites)==22 and not problems and not conflicts
        and dict(group_sites)==expected
        and len(selected)==88 and len(set(selected))==88
    )
    return {
       "schema":"structural.madeira_spider_original_sweep_site_gate.v1_342",
       "status":"MADEIRA_22_PLOT_88_EQUAL_SWEEP_EVENTS_SOURCE_LOCKED_TAXA_SEALED" if eligible
              else "TERMINAL_MADEIRA_NATURAL_HABITAT_SWEEP_SOURCE_NOT_COMPARABLE",
       "source_original_zip_sha256":SHA,
       "original_Event_rows_examined":len(rows),
       "original_Occurrence_rows_opened":0,
       "original_physical_source_sites":len(sites),
       "original_physical_sites_by_island_habitat":dict(sorted(group_sites.items())),
       "original_samplingProtocol_vocabulary_Event_counts":dict(sorted(vocab.items())),
       "source_selected_22_plot_sweeps_original_Event_n":len(selected),
       "selected_88_original_Event_coreid_SHA256":hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest(),
       "source_method_counts_by_group":{k:dict(v) for k,v in sorted(methods_by_plot.items())},
       "source_original_survey_year_counts_by_group":{k:dict(v) for k,v in sorted(group_years.items())},
       "source_Event_quality_problem_counts":dict(sorted(problems.items())),
       "source_physical_site_conflict_counts":dict(sorted(conflicts.items())),
       "original_site_IDs_geographical_coordinates_taxa_and_status_not_exported":True,
       "forest_2016_dry_2017_temporal_confound_unresolved":True,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.protocol.read_text())
    if (c.get("schema")!="structural.madeira_spider_original_event_sweeping_qualification.v1_342"
       or c.get("status")!="FROZEN_AFTER_SOURCE_METADATA_BEFORE_FIRST_EVENT_BODIES"
       or c["source"]["url"]!=SOURCE or c["source"]["sha256"]!=SHA):
        raise ValueError("Pre-original Madeira equal-sweep frame not frozen")
    result={
        "schema":"structural.madeira_spider_original_sweep_site_gate.v1_342",
        "status":"SOURCE_EVENT_TRANSPORT_OR_SCHEMA_TECHNICAL_STOP",
        "original_Event_rows_examined":0,"original_Occurrence_rows_opened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-MadeiraSpider-SourceEventOnly-v1.342"})
        with urllib.request.urlopen(req,timeout=65) as f:blob=f.read(400001)
        if len(blob)>400000 or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original source archive SHA or size changed")
        result=audit(original_event_core_only(blob),c)
    except Exception as ex:
        result["stop_type"]=type(ex).__name__;result["stop_reason"]=str(ex)[:280]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:result.get(k) for k in (
        "status","original_physical_source_sites","original_physical_sites_by_island_habitat",
        "source_selected_22_plot_sweeps_original_Event_n",
        "source_Event_quality_problem_counts","source_physical_site_conflict_counts",
        "original_samplingProtocol_vocabulary_Event_counts",
        "original_Occurrence_rows_opened","stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_EVENT_TRANSPORT_OR_SCHEMA_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":
    main()
