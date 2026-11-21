#!/usr/bin/env python3
"""Inspect publisher-original Thai beetle scientificName morphospecies semantics.

Read only the same frozen CC-BY DwC-A original Coleoptera source; report counts
of scientificName pattern classes and their agreement with the published 437
species/morphospecies, never infer species identities from genus/family ranks.
Do NOT export verbatim names, event IDs, counts per taxon, or coordinates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from thai_beetle_canopy_family_response import (
    UID, API, fetch_json, get_archive_endpoint, download_small_archive,
    original_tables,
)

SOURCE_SHA="1565cf6d7f1e7289e28756367e3d137f64723dc1fa0a06d799f6abdb523e1339"

MORPHO=re.compile(
    r"(?i)(?<![a-z])(?:sp|spp|morphospecies|morpho(?:type)?)"
    r"\.?\s*[-_:#( ]*\s*(?:[0-9]{1,5}|[A-Za-z]{1,3}[0-9]{1,5}|[0-9]{1,5}[A-Za-z]{1,3}|[A-Z](?![a-z]))\b")
GENERIC_SP=re.compile(r"(?i)(?<![a-z])spp?\.?\s*(?:$|\b)")
BINOMIAL=re.compile(r"^[A-Z][a-zA-Z-]+\s+[a-z][a-z-]{2,}(?:\s+[A-Za-z.-]+)?$")

def identify_class(value, rank):
    name=re.sub(r"\s+"," ",str(value or "").strip())
    rank=str(rank or "").strip().lower()
    if not name:return "empty_source_scientificName"
    if MORPHO.search(name):return "explicit_morphospecies_code"
    if BINOMIAL.fullmatch(name) and not GENERIC_SP.search(name):
        return "binomial_label_no_morphocode"
    if GENERIC_SP.search(name):return "generic_sp_without_unique_code"
    if rank in ("family","order","class","phylum","subfamily","genus"):
        return "higher_rank_or_genus_label_no_explicit_species_key"
    return "other_unresolved_source_name"

def inspect(events, occurrences):
    if len(events)!=288:raise ValueError("frozen_source_288_events_expected")
    if len(occurrences)!=1073:raise ValueError("frozen_source_1073_occurrences_expected")
    core_ids={x["_core_id"] for x in events}
    if len(core_ids)!=288:raise ValueError("source_EventIDs_not_unique")
    classes=Counter()
    individuals=Counter()
    label_set=defaultdict(set)
    rank_classes=Counter()
    source_names=defaultdict(set)
    no_name_count=0
    counted=0
    for r in occurrences:
        if r["_core_id"] not in core_ids:raise ValueError("source_occurrence_dangling_Event")
        label=re.sub(r"\s+"," ",str(r.get("scientificName") or "").strip())
        cl=identify_class(label,r.get("taxonRank"))
        rank=str(r.get("taxonRank") or "").strip().lower()
        try:
            n=float(r.get("individualCount") or "")
            if not n.is_integer() or n<=0:raise ValueError()
            n=int(n)
        except ValueError:
            raise ValueError("source_arthropod_individualCount_noninteger_or_missing")
        counted+=n
        classes[cl]+=1
        individuals[cl]+=n
        rank_classes[rank,cl]+=1
        if label:
            source_names[cl].add(label)
            label_set[cl].add(label)
        else:no_name_count+=1
    if counted!=1622:raise ValueError("source_original_individual_total_not_reproduced")
    distinct={k:len(v) for k,v in label_set.items()}
    strong_names=source_names["explicit_morphospecies_code"] | source_names["binomial_label_no_morphocode"]
    strong_rows=classes["explicit_morphospecies_code"] + classes["binomial_label_no_morphocode"]
    strong_specimens=individuals["explicit_morphospecies_code"] + individuals["binomial_label_no_morphocode"]
    aggregate={
        "schema":"structural.thai_beetle_original_morphospecies_semantics_audit.v1",
        "source_original_archive_sha256":SOURCE_SHA,
        "publisher_event_rows":288,
        "publisher_occurrence_rows":len(occurrences),
        "source_original_beetle_individuals":counted,
        "published_species_and_morphospecies_count_REFERENCE_ONLY":437,
        "source_scientificName_pattern_record_counts":dict(classes),
        "source_scientificName_pattern_specimen_counts":dict(individuals),
        "source_unique_verbatim_scientificName_by_pattern_NOT_species_richness":distinct,
        "source_unique_verbatim_scientificName_total_NOT_species_richness":len(set().union(*label_set.values())),
        "morphospecies_or_binomial_distinct_LABELS_candidate_lower_bound_not_validated":len(strong_names),
        "potential_species_like_scientificName_rows":strong_rows,
        "potential_species_like_scientificName_individuals":strong_specimens,
        "source_taxonRank_x_scientificName_pattern_counts":{
            f"{rank} / {cl}":n for (rank,cl),n in sorted(rank_classes.items())
        },
        "has_any_unresolved_identification_labels":strong_rows<len(occurrences),
        "source_species_identity_admission_not_proven":True,
        "original_paper_reported_437_morphospecies_not_assumed_reconstructible":True,
        "raw_taxon_labels_coreIDs_and_locations_not_exported":True,
        "new_vertical_niche_or_thermal_effect_estimated":False,
        "source_taxon_records_are_mixed_rank":True,
        "eBird_used":False,
    }
    return aggregate


def run(out, *, request=fetch_json, download=download_small_archive):
    meta=request(API+UID)
    if str(meta.get("key"))!=UID or str(meta.get("type"))!="SAMPLING_EVENT":
        raise ValueError("original_dataset_identity_changed")
    license=str(meta.get("license") or "").lower()
    if license not in ("cc_by_4_0","http://creativecommons.org/licenses/by/4.0/legalcode",
                       "https://creativecommons.org/licenses/by/4.0/legalcode"):
        raise ValueError("original_license_changed")
    data=download(get_archive_endpoint(meta))
    if hashlib.sha256(data).hexdigest()!=SOURCE_SHA:
        raise ValueError("source_original_archive_hash_changed")
    events,occ=original_tables(data)
    report=inspect(events,occ)
    path=Path(out);path.mkdir(parents=True,exist_ok=True)
    (path/"thai_beetle_morphospecies_label_quality.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    arg=parser.parse_args()
    run(arg.out)
