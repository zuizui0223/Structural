#!/usr/bin/env python3
"""PRIBES v1.321 original source Event ONLY: physical site, island and effort.

No original occurrence file is decompressed or read, no species/status seen.
The 79 physical-site / 80 Event source discrepancy is evaluated explicitly
using pre-frozen locationID grammar and deterministic original coreID choice.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,unicodedata,urllib.request,zipfile
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=pribes_arthropods&v=1.3"
SHA="9b4eb77c15de7a900c391a17e781a99521f00d9b2fe433807607ebe462235b6e"
MAX_SOURCE=2_000_000
ISLAND_LABELS={"COR":"Corvo","FLO":"Flores","FAI":"Faial","PIC":"Pico",
               "TER":"Terceira","SMG":"São Miguel","SMR":"Santa Maria"}
OVERLAP=("FAI","FLO","PIC","TER","SMG","SMR")

def local(x):return x.rsplit("}",1)[-1]
def term(x):return x.rstrip("/").split("/")[-1].split("#")[-1]
def alphabetize(value):
    x=unicodedata.normalize("NFKD",str(value or ""))
    x="".join(v for v in x if not unicodedata.combining(v))
    return "".join(c for c in x.upper() if ("A"<=c<="Z" or "0"<=c<="9"))
def normalized_island(source,aliases):
    v=alphabetize(source)
    for code,labels in aliases.items():
        if any(alphabetize(name)==v for name in labels):
            return code
    return None

def event_source_only(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        cores=[x for x in root if local(x.tag)=="core"]
        if len(cores)!=1:raise ValueError("Unexpected original event core count")
        node=cores[0]
        cols={};idx=None;locations=[]
        for v in node.iter():
            tag=local(v.tag)
            if tag=="field" and "term" in v.attrib and "index" in v.attrib:
                cols[term(v.attrib["term"])]=int(v.attrib["index"])
            elif tag=="id" and "index" in v.attrib:idx=int(v.attrib["index"])
            elif tag=="location" and v.text:locations.append(v.text.strip())
        required={"eventID","eventDate","island","locationID","samplingProtocol",
                  "sampleSizeValue","sampleSizeUnit","decimalLatitude","decimalLongitude"}
        if idx is None or len(locations)!=1 or not required.issubset(cols):
            raise ValueError("Original Event metadata missing frozen identity/effort coordinate roles")
        delimiter=node.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        skip=int(node.attrib.get("ignoreHeaderLines","0"))
        if len(delimiter)!=1 or skip not in (0,1):
            raise ValueError("Unrecognized original source TSV serialization")
        results=[]
        with z.open(locations[0]) as src:
            with io.TextIOWrapper(src,encoding="utf-8-sig",newline="") as f:
                reader=csv.reader(f,delimiter=delimiter)
                for _ in range(skip):next(reader,None)
                for row in reader:
                    if not row or not any(row):continue
                    if max(idx,*(cols[x] for x in required))>=len(row):
                        raise ValueError("Source Event original row missing required columns")
                    value={key:row[pos] for key,pos in cols.items() if pos<len(row)}
                    value["original_coreid"]=row[idx]
                    results.append(value)
        return results

def audit(events,contract):
    if len(events)!=contract["field_contract"]["source_event_rows_expected"]:
        raise ValueError("Source Event row count not original 80")
    aliases=contract["field_contract"]["island_mapping_predeclared"]
    seen=set(); grouped=defaultdict(list);years_by_island=defaultdict(Counter)
    methods=defaultdict(Counter); effort=defaultdict(Counter); unknown=Counter()
    for e in events:
        core=str(e.get("original_coreid","")).strip()
        if not core or core in seen:raise ValueError("Original Event coreID duplicate/empty")
        seen.add(core)
        island=normalized_island(e.get("island"),aliases)
        if island not in ISLAND_LABELS:raise ValueError("Unrecognized original PRIBES island source code")
        location=alphabetize(e.get("locationID"))
        if not location:
            unknown["missing_original_locationID"]+=1
            continue
        year_str=str(e.get("eventDate","")).strip()[:4]
        if not year_str.isdigit() or not 2019<=int(year_str)<=2025:
            raise ValueError("Original source Event date outside predeclared 2019–2025")
        if e.get("year") and str(e.get("year")).strip()!=year_str:
            raise ValueError("Original Event year and date mismatch")
        try:
            lat=float(e.get("decimalLatitude"))
            lon=float(e.get("decimalLongitude"))
        except (TypeError,ValueError):
            unknown["source_coordinate_not_parseable"]+=1
            continue
        if not math.isfinite(lat) or not math.isfinite(lon):
            unknown["source_coordinate_not_finite"]+=1
            continue
        proto=" ".join(str(e.get("samplingProtocol","")).casefold().split())
        unit=" ".join(str(e.get("sampleSizeUnit","")).casefold().split())
        sval=str(e.get("sampleSizeValue","")).strip()
        try:size=float(sval)
        except (TypeError,ValueError):size=float("nan")
        if not proto or not unit or not math.isfinite(size) or size<=0:
            unknown["sampling_effort_missing_or_invalid"]+=1
            continue
        grouped[(island,location)].append({
            "core":core,"year":int(year_str),
            "lat":lat,"lon":lon,"proto":proto,"unit":unit,"sample_size":size})
    problem=""
    duplicate_mismatched=0
    chosen=[]
    for key,rows in sorted(grouped.items()):
        representative=min(rows,key=lambda x:x["core"])
        for e in rows:
            if (e["proto"]!=representative["proto"] or e["unit"]!=representative["unit"]
                or e["sample_size"]!=representative["sample_size"]
                or max(abs(e["lat"]-representative["lat"]),
                       abs(e["lon"]-representative["lon"]))>0.0003):
                duplicate_mismatched+=1
        chosen.append((key,representative))
        island=key[0]
        years_by_island[island][representative["year"]]+=1
        methods[island][representative["proto"]]+=1
        effort[island][(representative["sample_size"],representative["unit"])]+=1
    counts=Counter(key[0] for key,_ in chosen)
    source_unique=len(chosen)
    count_gate=(source_unique in (79,80) and
        set(counts)==set(ISLAND_LABELS)
        and all(counts[i]>=4 for i in OVERLAP))
    effort_values=set()
    method_values=set()
    for key,record in chosen:
        if key[0] in OVERLAP:
            effort_values.add((record["sample_size"],record["unit"]))
            method_values.add(record["proto"])
    effort_gate=(len(effort_values)==1 and len(method_values)==1)
    qualify=(count_gate and effort_gate and not unknown and duplicate_mismatched==0)
    selected=[record["core"] for _,record in chosen if _[0] in OVERLAP]
    all_selected=sorted(record["core"] for _,record in chosen)
    return {
        "schema":"structural.pribes_original_event_only_result.v1_321",
        "status":"PRIBES_6_ISLAND_SOURCE_PHYSICAL_EFFORT_ELIGIBLE_TAXA_SEALED"
            if qualify else "PRIBES_EVENT_SOURCE_SITE_OR_EFFORT_TERMINAL_NO_SPECIES_OPEN",
        "original_Event_rows_examined":len(events),
        "source_physical_location_key_n":source_unique,
        "source_duplicate_Event_over_physical_key_n":len(events)-source_unique,
        "source_duplicate_site_conflicts":duplicate_mismatched,
        "source_rows_missing_source_site_coordinate_effort":dict(unknown),
        "observed_island_physical_site_counts":dict(sorted(counts.items())),
        "observed_island_source_event_year_counts":{
           code:dict(sorted(years_by_island[code].items())) for code in sorted(ISLAND_LABELS)
        },
        "observed_overlap_method_vocabulary_counts":{
           str(method):sum(methods[i][method] for i in OVERLAP)
           for method in sorted(set().union(*(methods[i] for i in OVERLAP)))
        },
        "observed_overlap_effort_vocabulary_counts":{
           f"{n:g} {unit}":sum(effort[i][(n,unit)] for i in OVERLAP)
           for n,unit in sorted(effort_values)
        },
        "physical_site_count_matches_published_79_or_80":count_gate,
        "overlapping_BALA_island_site_count":sum(counts[i] for i in OVERLAP),
        "has_exactly_six_BALA_overlap_islands":all(counts[i]>=4 for i in OVERLAP),
        "source_method_and_effort_identical_across_six_islands":effort_gate,
        "selected_all_original_source_coreids_sha256":hashlib.sha256("\n".join(all_selected).encode()).hexdigest(),
        "selected_six_overlap_island_original_coreids_sha256":hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest(),
        "selected_six_overlap_original_Event_count":len(selected),
        "pre_frozen_BALA_overlap":["FAI","FLO","PIC","TER","SMG","SMR"],
        "original_raw_locationIDs_coords_or_timestamps_exported":False,
        "PRIBES_Original_Occurrence_rows_opened":0,
        "BALA_original_species_response_reopened":False,
        "original_GEB_mammal_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.pribes_ruderal_original_event_site_design.v1_321"
        or c.get("status")!="FROZEN_BEFORE_OPENING_PRIBES_V1_3_ORIGINAL_EVENT_VALUE_ROWS"
        or c["source"]["url"]!=SOURCE or c["source"]["sha256"]!=SHA):
        raise ValueError("Author source-Event eligibility not frozen")
    out={"schema":"structural.pribes_original_event_only_result.v1_321",
         "status":"SOURCE_EVENT_FORMAT_OR_TRANSPORT_STOP","original_Event_rows_examined":0,
         "PRIBES_Original_Occurrence_rows_opened":0,"BALA_original_species_response_reopened":False,
         "original_GEB_mammal_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-PRIBES-EventOnly-v1.321"})
        with urllib.request.urlopen(req,timeout=60) as src:blob=src.read(MAX_SOURCE+1)
        if len(blob)>MAX_SOURCE or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Published original v1.3 ZIP identity changed")
        out=audit(event_source_only(blob),c)
        out["source_original_archive_sha256"]=SHA
    except Exception as e:
        out["stop_type"]=type(e).__name__;out["stop_reason"]=str(e)[:280]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:out.get(key) for key in (
       "status","original_Event_rows_examined","source_physical_location_key_n",
       "observed_island_physical_site_counts",
       "overlapping_BALA_island_site_count",
       "source_method_and_effort_identical_across_six_islands",
       "source_rows_missing_source_site_coordinate_effort",
       "source_duplicate_site_conflicts","stop_reason"
    )},sort_keys=True))
    if out["status"]=="SOURCE_EVENT_FORMAT_OR_TRANSPORT_STOP":
        raise SystemExit(2)
if __name__=="__main__":
    main()
