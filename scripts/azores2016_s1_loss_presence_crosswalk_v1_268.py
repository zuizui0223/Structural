#!/usr/bin/env python3
"""Published 2016 Azores island species checklist × already-opened 2025 S1 cases.

This is a retrospective documentation-coverage audit: not an occupancy risk
regression or measured pre-extinction source/rescue. No Macaronesia S2/S3/S4
or earlier Structural mammal/BioTIME/RLS protected outcome values are read.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

from azores_2016_dwca_structure_v1_267 import summarize_archive
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
from macaronesia_extirpation_source_profile_v1_263 import download_original

SCHEMA="structural.azores2016_S1_case_current_distribution_coverage.v1_268"
NINE=("Corvo","Flores","Faial","Pico","Graciosa","São Jorge","Terceira","São Miguel","Santa Maria")
GBIF_SHA="07be180d52f08e5051d63c5364dc856d8b0e811a83a9c26c920780138bb3fc79"
S1_SHA="767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1"
GBIF_URL="https://ipt.gbif.pt/ipt/archive.do?r=uac_checklist_acores&v=1.2"
S1_URL="https://digital.csic.es/bitstream/10261/377677/5/Extinct_species_biogeographical_variables_%26_biological_traits_Macaronesian_flora.xlsx"
VASCULAR={"magnoliophyta","pteridophyta","lycopodiophyta",
          "pinophyta","spermatophyta","tracheophyta"}
NATIVE={"native","indigenous","endemic"}


def normalized_text(v):
    x=unicodedata.normalize("NFKD",str(v or "").strip().casefold())
    x="".join(ch for ch in x if not unicodedata.combining(ch))
    return " ".join(x.split())


ISLAND_CODES={normalized_text(x):x for x in NINE}
ISLAND_CODES.update({"s. jorge":"São Jorge","s. miguel":"São Miguel"})


def normalized_locality(value):
    x=normalized_text(value)
    if x.startswith(("azores ","acores ")):
        x=re.sub(r"^(?:azores|acores)\s*[-,:;/|]\s*","",x)
    x=re.sub(r"^(?:ilha\s+de\s+|island\s+of\s+)","",x)
    x=re.sub(r"\s+island$","",x)
    x=x.strip(" \t.")
    return ISLAND_CODES.get(x)


def canonical_binomial(value):
    x=normalized_text(value)
    if not x or re.search(r"\b(?:subsp|ssp|var|forma|sp\.|cf\.|aff\.)\b",x):
        return None
    # trailing numeric footnote annotation may follow the species epithet
    # but no fuzzy spelling changes or taxonomic-synonym inference is made.
    m=re.match(r"^([a-z][a-z-]*)\s+([a-z][a-z-]*)(?:[0-9]+)?(?=\s|$|[.,;])",x)
    if not m or m.group(2) in {"sp","cf","aff","spp"}:
        return None
    return f"{m.group(1)} {m.group(2)}"


def valid_vascular_species(taxon):
    return (normalized_text(taxon.get("taxonRank"))=="species" and
            normalized_text(taxon.get("kingdom"))=="plantae" and
            normalized_text(taxon.get("phylum")) in VASCULAR)


def summary_join(taxa,observations,losses):
    """Join verified checklist positives only; missing/unmatched is UNKNOWN."""
    taxon_by_id={}
    for t in taxa:
        tid=str(t.get("taxonID","")).strip()
        if not tid: continue
        if tid in taxon_by_id:
            raise ValueError("Duplicate checklist taxonID: do not prefer later name")
        taxon_by_id[tid]=t
    all_status=Counter()
    means_counts=Counter()
    island_species=defaultdict(set)
    native_island_species=defaultdict(set)
    positives=defaultdict(set)
    other_localities=Counter()
    recorded_island_taxon_pairs=set()
    records_count=0
    for rec in observations:
        records_count+=1
        tid=str(rec.get("taxonID","")).strip()
        status=normalized_text(rec.get("occurrenceStatus"))
        means=normalized_text(rec.get("establishmentMeans"))
        all_status[status or "[MISSING]"]+=1
        means_counts[means or "[MISSING]"]+=1
        island=normalized_locality(rec.get("locality"))
        loc=normalized_text(rec.get("locality"))
        if island is None:
            if loc in {"azores","acores"}:
                other_localities["archipelago_only"]+=1
            elif any(x in loc for x in ISLAND_CODES):
                other_localities["ambiguous_or_combined_island_location"]+=1
            elif not loc:
                other_localities["missing"]+=1
            else:
                other_localities["non_island_or_unknown_location"]+=1
            continue
        if status!="present":
            continue
        if tid not in taxon_by_id:
            other_localities["source_orphan_distribution_taxonID"]+=1
            continue
        taxon=taxon_by_id[tid]
        if not valid_vascular_species(taxon):
            continue
        island_species[island].add(tid)
        recorded_island_taxon_pairs.add((tid,island))
        positives[tid].add(island)
        if means in NATIVE:
            native_island_species[island].add(tid)

    accepted=[t for t in taxa if valid_vascular_species(t) and str(t.get("taxonID","")).strip()]
    full=defaultdict(set)
    bi=defaultdict(set)
    for t in accepted:
        tid=str(t["taxonID"]).strip()
        full[normalized_text(t.get("scientificName"))].add(tid)
        bp=canonical_binomial(t.get("scientificName"))
        if bp:bi[bp].add(tid)

    cases=[]
    for r in losses:
        if (normalized_text(r.get("Archipelago")) not in {"azores","acores"}
            or normalized_text(r.get("Category"))!="well-supported"
            or normalized_text(r.get("Extinction category"))!="extirpation (island level)"):
            continue
        isl=normalized_locality(r.get("Island"))
        if not isl:
            raise ValueError("Publisher Azores S1 loss island not on frozen nine-island roster")
        name=normalized_text(r.get("Species"))
        if not name:
            raise ValueError("Source reported extirpation without taxon name")
        cases.append((name,isl))
    if len(set(cases))!=len(cases):
        raise ValueError("Original S1 Azores duplicate taxon-island cases not expected")
    by_species=defaultdict(set)
    for name,isl in cases:by_species[name].add(isl)
    matched={}
    method_counts=Counter()
    for name in by_species:
        exact=full.get(name,set())
        binomial=bi.get(canonical_binomial(name),set())
        if len(exact)==1:
            matched[name]=next(iter(exact))
            method_counts["exact_full_name"]+=1
        elif len(exact)>1 or len(binomial)>1:
            matched[name]=None
            method_counts["ambiguous"]+=1
        elif len(binomial)==1:
            matched[name]=next(iter(binomial))
            method_counts["unique_binomial"]+=1
        else:
            matched[name]=None
            method_counts["not_matched"]+=1

    same_island=0
    other_taxa=0
    other_native_taxa=0
    repeated_other_taxa=0
    recorded_other_by_case=0
    other_island_counts=Counter()
    for name,loss_islands in by_species.items():
        tid=matched[name]
        if tid is None:continue
        check=positives.get(tid,set())
        same_island+=len(check & loss_islands)
        elsewhere=check-loss_islands
        other_island_counts[len(elsewhere)]+=1
        if elsewhere:
            other_taxa+=1
            recorded_other_by_case+=len(loss_islands)
            if len(loss_islands)>=2:repeated_other_taxa+=1
            if any(tid in native_island_species[x] for x in elsewhere):
                other_native_taxa+=1

    result={
        "source_taxon_core_rows":len(taxa),
        "source_distribution_rows":records_count,
        "source_distribution_status_vocab":dict(sorted(all_status.items())),
        "source_establishment_means_vocab":dict(sorted(means_counts.items())),
        "source_accepted_vascular_species_taxon_records":len(accepted),
        "source_accepted_vascular_species_unique_IDs":len(set(str(t["taxonID"]) for t in accepted)),
        "current_present_species_island_pairs":len(recorded_island_taxon_pairs),
        "current_present_island_located_native_species_pairs":sum(len(x) for x in native_island_species.values()),
        "current_vascular_species_by_island":{isl:len(island_species[isl]) for isl in NINE},
        "current_native_vascular_species_by_island":{isl:len(native_island_species[isl]) for isl in NINE},
        "unlocated_archipelago_distribution_rows":other_localities["archipelago_only"],
        "multi_island_or_ambiguous_locality_rows":other_localities["ambiguous_or_combined_island_location"],
        "other_unassigned_distribution_rows":sum(v for k,v in other_localities.items() if k not in {"archipelago_only","ambiguous_or_combined_island_location"}),
        "strict_S1_azores_source_loss_pairs":len(cases),
        "strict_S1_azores_source_taxa":len(by_species),
        "strict_S1_azores_repeat_loss_taxa":sum(len(x)>=2 for x in by_species.values()),
        "S1_taxa_uniquely_joined_to_2016_species":sum(x is not None for x in matched.values()),
        "S1_taxa_with_ambiguous_2016_species_identity":method_counts["ambiguous"],
        "S1_taxa_with_no_2016_species_match":method_counts["not_matched"],
        "S1_source_match_methods":dict(method_counts),
        "loss_pairs_with_2016_same_island_present":same_island,
        "confirmed_other_island_present_loss_taxa":other_taxa,
        "confirmed_native_other_island_present_loss_taxa":other_native_taxa,
        "S1_two_island_loss_taxa_with_current_other_island_present":repeated_other_taxa,
        "confirmed_other_island_present_2016_loss_cases":recorded_other_by_case,
        "taxa_by_2016_other_documented_island_count":{str(k):v for k,v in sorted(other_island_counts.items())},
        "2016_missing_is_never_filled_as_absent":True,
        "2016_state_is_not_pre_loss_t0":True,
        "no_manual_synonym_or_fuzzy_matching":True,
        "not_observed_migration_or_rescue":True,
        "individual_species_or_taxon_IDs_exported":False,
    }
    if len(cases)!=sum(len(x) for x in by_species.values()):
        raise ValueError("S1 strict island case accounting changed")
    return result


def _read_author_tables(archive_bytes):
    schema=summarize_archive(archive_bytes,"ec1a0bfb-7d8e-4c6b-bc4d-dfd68a1e844f")
    c=schema["core"]
    extensions=schema["extensions"]
    chosen=[x for x in extensions
            if x["rowtype"]=="http://rs.gbif.org/terms/1.0/Distribution"]
    if (c["rowtype"]!="http://rs.tdwg.org/dwc/terms/Taxon"
        or len(chosen)!=1):
        raise ValueError("2016 original taxon/distribution schema no longer matches predeclared source")
    d=chosen[0]
    required_taxa={"taxonID","scientificName","kingdom","phylum","taxonRank","acceptedNameUsageID"}
    required_dist={"locality","occurrenceStatus","establishmentMeans"}
    def fields(table):
        return {str(x["term"]).rsplit("/",1)[-1]:int(x["index"]) for x in table["fields"]
                if x["term"] and x["index"] is not None}
    ct,dt=fields(c),fields(d)
    if not required_taxa<=set(ct) or not required_dist<=set(dt):
        raise ValueError("2016 required core or island/distribution field terms missing")
    if c["encoding"].lower()!="utf-8" or d["encoding"].lower()!="utf-8":
        raise ValueError("Unexpected original archive text encoding")
    key_audit=Counter()
    def parse(zip_obj,table,indices,fields_to_keep):
        with zip_obj.open(table["record_path"]) as zstream:
            with io.TextIOWrapper(zstream,encoding="utf-8-sig",newline="") as handle:
                rd=csv.reader(handle,delimiter="\t")
                skip=int(table["ignore_header_lines"] or 0)
                for _ in range(skip):next(rd,None)
                for line in rd:
                    if not line or not any(line):continue
                    if any(index>=len(line) for index in indices.values()):
                        raise ValueError("Original DwC-A row shorter than declared schema columns")
                    value={col:line[indices[col]] for col in fields_to_keep if col in indices}
                    # Darwin Core extension coreid points to the <core><id index="0"/>,
                    # not necessarily the core field with term dct:taxonID.
                    if table["rowtype"].endswith("/Taxon") and value.get("taxonID","")!=line[0]:
                        key_audit["published_taxonID_field_differs_from_coreid"]+=1
                    value["taxonID"]=line[0]
                    yield value
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        manifest=ET.fromstring(archive.read("meta.xml"))
        core=next((x for x in manifest if x.tag.endswith("}core")),None)
        extension=next((x for x in manifest if x.tag.endswith("}extension")),None)
        if core is None or extension is None:
            raise ValueError("Original Darwin Core manifest lacks core/extension")
        id_node=next((x for x in core if x.tag.endswith("}id")),None)
        coreid_node=next((x for x in extension if x.tag.endswith("}coreid")),None)
        if id_node is None or coreid_node is None or id_node.attrib.get("index")!="0" or coreid_node.attrib.get("index")!="0":
            raise ValueError("Original Darwin Core id/coreid join key is not aligned at index0")
        taxa=list(parse(archive,c,ct,required_taxa))
        distributions=list(parse(archive,d,dt,required_dist))
    return taxa,distributions,dict(key_audit)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    cfg=json.loads(args.contract.read_text(encoding="utf-8"))
    if (cfg.get("schema")!="structural.azores2016_macaronesia_s1_current_checklist_crosswalk_contract.v1_268"
        or cfg.get("status")!="FROZEN_BEFORE_AZORES2016_BIOLOGICAL_CHECKLIST_VALUES_OPENED"):
        raise ValueError("Frozen source pairing and current-vs-historic interpretation missing")
    gb=cfg["sources"]["azores2016"]
    s=cfg["sources"]["S1"]
    if gb["sha256"]!=GBIF_SHA or s["sha256"]!=S1_SHA or gb["url"]!=GBIF_URL or s["exact_url"]!=S1_URL:
        raise ValueError("Original two-source authority or hashes changed")

    out={
        "schema":SCHEMA,"status":"AUTHOR_SOURCE_STOP_BEFORE_NEW_ECOLOGICAL_COVERAGE",
        "source_gbif2016_sha256":GBIF_SHA,
        "source_macaronesia_S1_sha256":S1_SHA,
        "S2_S3_S4_values_opened":0,
        "original_mammal_BioTIME_RLS_holdouts_opened":0,
        "eBird_used":False,"GEB_scientific_HOLD":True,
    }
    try:
        request=urllib.request.Request(GBIF_URL,headers={
            "User-Agent":"Structural-2016-Azores-Checklist-Case-Coverage/1.0",
            "Accept":"application/zip,application/octet-stream"})
        with urllib.request.urlopen(request,timeout=55) as response:
            dwca=response.read(25_000_001)
        if len(dwca)!=1603288 or hashlib.sha256(dwca).hexdigest()!=GBIF_SHA:
            raise ValueError("Original 2016 Azores source archive no longer matches publisher-signed input")
        s1=download_original(S1_URL,332776,5_000_000)
        if hashlib.sha256(s1).hexdigest()!=S1_SHA:
            raise ValueError("Original CSIC published S1 source changed")
        taxa,distributions,key_audit=_read_author_tables(dwca)
        losses=parse_sheet_s1(s1)
        crosswalk=summary_join(taxa,distributions,losses)
        if (crosswalk["strict_S1_azores_source_loss_pairs"]!=24 or
            crosswalk["strict_S1_azores_source_taxa"]!=20):
            raise ValueError("Frozen 24/20 Azores S1 confirmed local-loss denominators changed")
        out["crosswalk"]=crosswalk
        out["archive_join_key_audit"]=key_audit
        out["status"]="SOURCE_AUTHENTICATED_AZORES2016_S1_COVERAGE_ANALYSIS"
        out["S1_strict_azores_pairs"]=24
        out["S1_strict_azores_taxa"]=20
    except Exception as exc:
        out["stop_type"]=type(exc).__name__
        out["stop_reason"]=str(exc)[:500]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({
        "status":out["status"],
        "source_taxon_rows":out.get("crosswalk",{}).get("source_taxon_core_rows"),
        "source_distribution_rows":out.get("crosswalk",{}).get("source_distribution_rows"),
        "unique_joined_S1_taxa":out.get("crosswalk",{}).get("S1_taxa_uniquely_joined_to_2016_species"),
        "2016_missing_not_absence":True,
        "stop_reason":out.get("stop_reason")},sort_keys=True))
    if out["status"]!="SOURCE_AUTHENTICATED_AZORES2016_S1_COVERAGE_ANALYSIS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
