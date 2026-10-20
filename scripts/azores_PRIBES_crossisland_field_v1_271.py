#!/usr/bin/env python3
"""Dated 2020+ island field occurrence crosswalk, four original Azores PRIBES islands.

Uses only published author Event/Occurrence rows from three exact original
SHA256-locked archives. Source Event core id joins Occurrence extension coreid.
A new field occurrence is NOT true historical persistence/colonization/rescue.
Nothing absent from a new field survey is imputed an island-level absence.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
import csv

from azores_2016_dwca_structure_v1_267 import summarize_archive
from azores2016_s1_loss_presence_crosswalk_v1_268 import canonical_binomial,normalized_locality,normalized_text
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
from macaronesia_extirpation_source_profile_v1_263 import download_original

SCHEMA="structural.azores_PRIBES_four_island_field_cases.v1_271"
SOURCE_SHA_S1="767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1"
FULL_ISLANDS={"Pico","Graciosa","Santa Maria","São Jorge"}
NATIVE={"native","indigenous","endemic"}
SOURCE_MAX=10_000_000


def field_columns(table):
    return {str(field["term"]).rsplit("/",1)[-1]:int(field["index"])
            for field in table["fields"] if field.get("term") and field.get("index") is not None}


def _table_records(archive,table,fields):
    with archive.open(table["record_path"]) as source:
        with io.TextIOWrapper(source,encoding="utf-8-sig",newline="") as fp:
            reader=csv.reader(fp,delimiter="\t")
            for _ in range(int(table.get("ignore_header_lines") or "0")):
                next(reader,None)
            for line in reader:
                if not line or not any(line):continue
                if not line[0] or any(i>=len(line) for i in fields.values()):
                    raise ValueError("Invalid source Event/Occurrence row width or coreid")
                yield {"coreid":line[0], **{k:line[i] for k,i in fields.items()}}


def read_dated_field(raw,permitted_islands):
    """Source-verified true day-level field positives. Return local-only row details."""
    if not raw.startswith(b"PK\x03\x04") or len(raw)>SOURCE_MAX:
        raise ValueError("Original Event DwC-A exceeds size/signature limit")
    if not set(permitted_islands)<=FULL_ISLANDS or not permitted_islands:
        raise ValueError("Unfrozen island requested")
    meta=summarize_archive(raw,"ORIGINAL_AUTHOR_SOURCE_VALIDATED")
    core=meta["core"]
    extensions=[x for x in meta["extensions"] if x["rowtype"].endswith("/Occurrence")]
    if not core["rowtype"].endswith("/Event") or len(extensions)!=1:
        raise ValueError("Original Event core and single Occurrence extension not available")
    ext=extensions[0]
    ce=field_columns(core); co=field_columns(ext)
    if not {"island","eventDate"}<=set(ce) or "scientificName" not in co:
        raise ValueError("Source lacks exact island, date or scientificName")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        xml=ET.fromstring(z.read("meta.xml"))
        cores=[x for x in xml if x.tag.endswith("}core")]
        occurrences=[x for x in xml if x.tag.endswith("}extension") and x.attrib.get("rowType","").endswith("/Occurrence")]
        if len(cores)!=1 or len(occurrences)!=1:
            raise ValueError("Author ID provenance ambiguous")
        id_fields=[x for x in cores[0] if x.tag.endswith("}id")]
        oid_fields=[x for x in occurrences[0] if x.tag.endswith("}coreid")]
        if (len(id_fields)!=1 or len(oid_fields)!=1
            or id_fields[0].attrib.get("index")!="0" or oid_fields[0].attrib.get("index")!="0"):
            raise ValueError("DwC-A original Event/Occurrence ID fields not aligned")
        events=list(_table_records(z,core,ce))
        occurrences=list(_table_records(z,ext,co))
    lookup={}
    event_dates=Counter()
    island_dates=defaultdict(Counter)
    invalid_date=0
    for e in events:
        key=e["coreid"]
        if key in lookup:raise ValueError("Duplicate Event coreid in published source")
        isl=normalized_locality(e.get("island"))
        if isl not in permitted_islands:
            raise ValueError("Original source Event island outside frozen source islands")
        d=str(e.get("eventDate") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",d):
            invalid_date+=1
            continue
        try:
            when=date.fromisoformat(d)
        except ValueError:
            invalid_date+=1;continue
        if not date(2017,1,1)<=when<=date(2026,10,20):
            invalid_date+=1;continue
        lookup[key]=(isl,when.year,d)
        event_dates[str(when.year)]+=1
        island_dates[isl][str(when.year)]+=1

    field_rows=[]
    skipped=Counter()
    byyear=Counter()
    island_observations=Counter()
    for r in occurrences:
        key=r["coreid"]
        if key not in lookup:
            skipped["invalid_or_unlinked_event"]+=1
            continue
        rank=normalized_text(r.get("taxonRank"))
        if rank!="species":
            skipped["rank_not_exactly_species"]+=1
            continue
        status=normalized_text(r.get("occurrenceStatus"))
        if status=="absent":
            skipped["explicit_absent"]+=1;continue
        name=canonical_binomial(r.get("scientificName"))
        if not name:
            skipped["unparseable_binomial"]+=1;continue
        island,yr,d=lookup[key]
        means=normalized_text(r.get("establishmentMeans"))
        field_rows.append({"name":name,"island":island,"year":yr,
                           "native":means in NATIVE,"status":status or "[MISSING]",
                           "establishment":means or "[MISSING]"})
        byyear[str(yr)]+=1
        island_observations[island]+=1
    # A taxon can have many occurrence rows in one dated sampling year.
    # Preserve the raw observation count separately, but count only one
    # taxon × island × year positive when matching historical case taxa.
    annual={}
    for row in field_rows:
        key=(row["name"],row["island"],row["year"])
        if key not in annual:
            annual[key]=row.copy()
        elif row["native"]!=annual[key]["native"]:
            annual[key]["native"]=False  # disagreeing annotations are not known native
            annual[key]["establishment"]="[CONFLICTING]"
    distinct_field_rows=list(annual.values())
    pairs={(r["name"],r["island"]) for r in distinct_field_rows}
    return {
        "raw_event_rows":len(events),
        "raw_occurrence_rows":len(occurrences),
        "valid_dated_event_rows":len(lookup),
        "excluded_invalid_dates":invalid_date,
        "field_event_year_counts":dict(sorted(event_dates.items())),
        "island_event_counts":{isl:sum(island_dates[isl].values()) for isl in sorted(permitted_islands)},
        "field_species_observations_by_year":dict(sorted(byyear.items())),
        "field_species_observations_by_island":dict(sorted(island_observations.items())),
        "excluded_occurrence_rows":dict(sorted(skipped.items())),
        "valid_field_species_observations":len(field_rows),
        "unique_species_island_positive_pairs":len(pairs),
        "field_taxa":distinct_field_rows,
    }


def synthesize_observations(field_sources,S1_records,islands):
    """Aggregate dated field positives; no negative cells, no implied source/rescue."""
    source_cases=[]
    for row in S1_records:
        if (normalized_text(row.get("Archipelago")) not in {"azores","acores"}
            or normalized_text(row.get("Category"))!="well-supported"
            or normalized_text(row.get("Extinction category"))!="extirpation (island level)"):
            continue
        isl=normalized_locality(row.get("Island"))
        if not isl:raise ValueError("Unrecognized original CSIC island label")
        name=canonical_binomial(row.get("Species"))
        if not name:raise ValueError("Unparseable S1 taxon in strict island-loss cases")
        source_cases.append((name,isl))
    if len(set(source_cases))!=len(source_cases):
        raise ValueError("Duplicate strict taxon × island case; stop")
    bytax=defaultdict(set)
    for name,isl in source_cases:bytax[name].add(isl)
    complete=[]
    for source in field_sources.values():
        complete.extend(source["field_taxa"])
    if not set(x["island"] for x in complete)<=islands:
        raise ValueError("Field presence outside preselected four source islands")

    positives=defaultdict(set)
    native=defaultdict(set)
    island_names=defaultdict(set)
    year_counts=Counter()
    field_means=Counter()
    for x in complete:
        taxon=x["name"];isl=x["island"]
        positives[taxon].add(isl)
        island_names[isl].add(taxon)
        year_counts[str(x["year"])]+=1
        field_means[x["establishment"]]+=1
        if x["native"]:
            native[taxon].add(isl)
    matched=set(positives)&set(bytax)
    elsewhere=set()
    native_elsewhere=set()
    same_pairs=set()
    repeat_loss_others=set()
    field_twoislands=set()
    source_cases_by_field_coverage=Counter()
    for name,lost in bytax.items():
        observed=positives.get(name,set())
        others=observed-lost
        if others:
            elsewhere.add(name)
            if len(lost)>=2:repeat_loss_others.add(name)
        if others&native.get(name,set()):
            native_elsewhere.add(name)
        for island in lost&observed:
            same_pairs.add((name,island))
        if len(observed)>=2:
            field_twoislands.add(name)
        source_cases_by_field_coverage[len(observed)]+=1

    per_island={}
    for island in sorted(islands):
        observed=set(island_names[island])
        originally_lost={(nm,isl) for nm,isl in source_cases if isl==island}
        seen_same={(nm,island) for nm in observed}&originally_lost
        per_island[island]={
            "distinct_field_positive_species":len(observed),
            "historically_lost_Azores_taxa_with_day_level_field_positive":len(observed&set(bytax)),
            "strict_S1_lost_species_island_pairs_on_this_island":len(originally_lost),
            "strict_S1_lost_pairs_with_day_level_field_positive_here":len(seen_same),
            "native_flagged_field_positive_species":sum(island in native.get(nm,set()) for nm in observed),
        }

    return {
        "strict_S1_case_pairs":len(source_cases),
        "S1_strict_azores_taxa_in_synthetic_loss_input":len(bytax),
        "S1_taxa_with_any_dated_field_positive":len(matched),
        "S1_taxa_with_dated_field_detection_on_other_island":len(elsewhere),
        "S1_taxa_with_native_flagged_dated_field_positive_on_other_island":len(native_elsewhere),
        "S1_cases_same_island_dated_field_detection":len(same_pairs),
        "S1_taxa_with_dated_field_positive_on_2plus_islands":len(field_twoislands),
        "twice_lost_taxa_with_field_positive_on_other_unlost_island":len(repeat_loss_others),
        "field_current_observed_islands":sorted({x["island"] for x in complete}),
        "total_valid_species_rank_field_observation_rows":len(complete),
        "total_distinct_species_island_positive_pairs":len({(x["name"],x["island"]) for x in complete}),
        "per_island":per_island,
        "field_observation_years":dict(sorted(year_counts.items())),
        "field_establishmentMeans_categories":dict(sorted(field_means.items())),
        "strict_S1_taxa_by_number_of_dated_field_islands":{str(k):v for k,v in sorted(source_cases_by_field_coverage.items())},
        "unrecorded_taxa_are_never_negative_labels":True,
        "confirmed_demographic_recolonization_events":0,
        "measured_inter_island_dispersal":False,
        "verified_pre_loss_source_population_viability":False,
        "no_individual_species_names_in_public_artifact":True,
    }


def locked_archive_size(src):
    """Original SaoJorge receipt names its count 'bytes'; newer sources use 'expected_bytes'."""
    values={int(src[k]) for k in ("bytes","expected_bytes") if src.get(k) is not None}
    if len(values)!=1 or next(iter(values))<=0:
        raise ValueError("Ambiguous/missing source-author archive byte count")
    return next(iter(values))


def get_original(src):
    request=urllib.request.Request(src["url"],headers={
        "User-Agent":"Structural-Azores-Four-Island-Original-Survey-Join/1.0",
        "Accept":"application/zip,application/octet-stream"})
    with urllib.request.urlopen(request,timeout=70) as f:
        raw=f.read(SOURCE_MAX+1)
    if len(raw)!=locked_archive_size(src) or hashlib.sha256(raw).hexdigest()!=src["sha256"]:
        raise ValueError("Original source SHA or bytes changed: "+src["label"])
    return raw


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract",required=True,type=Path)
    ap.add_argument("--manifest",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf8"))
    manifest=json.loads(args.manifest.read_text(encoding="utf8"))
    if (contract["schema"]!="structural.azores_modern_field_observation_cross_island_S1_protocol.v1_270"
        or contract["status"]!="PREDECLARED_BEFORE_PICO_AND_GRACIOSA_SANTA_MARIA_BIOLOGICAL_OCCURRENCES"
        or manifest["schema"]!="structural.azores_pribes_two_original_source_manifest.v1_270"
        or manifest["status"]!="BOTH_ORIGINAL_NEW_SOURCES_METADATA_VERIFIED_BEFORE_BIOLOGICAL_DATA_ACCESS"):
        raise ValueError("Original pre-response field source admission changed")

    info={x["label"]:x for x in manifest["sources"]+[manifest["existing_source"]]}
    labels=[
        ("Sao Jorge PRIBES",{"São Jorge"}),
        ("Pico PRIBES",{"Pico"}),
        ("Graciosa Santa Maria PRIBES",{"Graciosa","Santa Maria"})
    ]
    out={
        "schema":SCHEMA,
        "status":"STOP_ORIGINAL_PUBLISHED_FIELD_SOURCE_VERIFICATION",
        "S2_S3_S4_values_accessed":0,
        "original_mammal_BioTIME_RLS_holdouts_opened":0,
        "GEB_scientific_HOLD":True,"eBird_used":False,
        "source_historic_S1_SHA256":SOURCE_SHA_S1,
        "source_island_count":4,
    }
    try:
        if contract["S1"]["sha256"]!=SOURCE_SHA_S1:
            raise ValueError("Published CSIC S1 author-defined loss source changed")
        detail={}
        for label,islands in labels:
            src=info.get(label)
            if not src or not src.get("url") or not src.get("sha256"):
                raise ValueError("Incomplete frozen source manifest "+label)
            original=get_original(src)
            rec=read_dated_field(original,islands)
            detail[label]=rec
        s1=download_original(contract["S1"]["CSIC_original_url"],332776,5_000_000)
        if hashlib.sha256(s1).hexdigest()!=SOURCE_SHA_S1:
            raise ValueError("Official CSIC S1 changed")
        original_cases=parse_sheet_s1(s1)
        if len(original_cases)!=168:raise ValueError("Original S1 168-case source frame changed")
        comparison=synthesize_observations(detail,original_cases,FULL_ISLANDS)
        if comparison["strict_S1_case_pairs"]!=24 or comparison["S1_strict_azores_taxa_in_synthetic_loss_input"]!=20:
            raise ValueError("Already frozen 24/20 strict Azores source cases changed")
        if (detail["Sao Jorge PRIBES"]["raw_event_rows"]!=1655
            or detail["Sao Jorge PRIBES"]["raw_occurrence_rows"]!=4523):
            raise ValueError("Previous original SaoJorge source row count not reproducible")
        out.update({
            "source_manifests":[{
                "label":label,"sha256":info[label]["sha256"],"original_bytes":info[label]["expected_bytes"],
                "event_rows":detail[label]["raw_event_rows"],
                "occurrence_rows":detail[label]["raw_occurrence_rows"],
                "valid_dated_events":detail[label]["valid_dated_event_rows"],
                "invalid_or_out_of_date_events":detail[label]["excluded_invalid_dates"],
                "field_event_years":detail[label]["field_event_year_counts"],
                "event_count_by_island":detail[label]["island_event_counts"],
                "eligible_species_rank_occurrences":detail[label]["valid_field_species_observations"],
                "excluded_occurrence_rows":detail[label]["excluded_occurrence_rows"]
            } for label,_ in labels],
            "comparison":comparison,
            "S1_strict_Azores_taxa":20,
            "S1_strict_Azores_loss_pairs":24,
            "status":"VERIFIED_DATED_PRIBES_FIELD_S1_CROSSCHECK",
        })
    except Exception as exc:
        out["error_type"]=type(exc).__name__
        out["stop_reason"]=str(exc)[:500]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({
        "status":out["status"],
        "error":out.get("stop_reason"),
        "dated_S1_taxa":out.get("comparison",{}).get("S1_taxa_with_any_dated_field_positive"),
        "historic_lost_island_positive":out.get("comparison",{}).get("S1_cases_same_island_dated_field_detection"),
        "biological_rescue_events_claimed":0},sort_keys=True))
    if out["status"]!="VERIFIED_DATED_PRIBES_FIELD_S1_CROSSCHECK":
        raise SystemExit(2)


if __name__=="__main__":
    main()
