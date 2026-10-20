#!/usr/bin/env python3
"""Read source-verified dated 2020 Sao Jorge field observations, NOT colonization.

Published Azores PRIBES Darwin Core Event+Occurrence field sampling; compare
to already-exposed historical confirmed Macaronesia S1 loss taxa without
opening S2/S3/S4. No non-detection, recolonization or rescue is inferred.
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

from azores_2016_dwca_structure_v1_267 import summarize_archive
from azores2016_s1_loss_presence_crosswalk_v1_268 import canonical_binomial,normalized_locality,normalized_text
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
from macaronesia_extirpation_source_profile_v1_263 import download_original

SRC_URL="https://ipt.gbif.pt/ipt/archive.do?r=sao_jorge_plants&v=1.2"
S1_SHA="767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1"
S1_URL="https://digital.csic.es/bitstream/10261/377677/5/Extinct_species_biogeographical_variables_%26_biological_traits_Macaronesian_flora.xlsx"


def parse_event_occurrence(raw,source_island="São Jorge"):
    if len(raw)>10_000_000 or not raw.startswith(b"PK\x03\x04"):
        raise ValueError("Author archive exceeds limit or is not DwC-A")
    meta=summarize_archive(raw,"9e53efa1-18a2-429f-8411-17d273bfc479")
    c=meta["core"]
    ex=[x for x in meta["extensions"] if x["rowtype"].endswith("/Occurrence")]
    if not c["rowtype"].endswith("/Event") or len(ex)!=1:
        raise ValueError("Published sampling event core and occurrence extension missing")
    d=ex[0]
    def columns(table):
        return {str(x["term"]).rsplit("/",1)[-1]:int(x["index"])
                for x in table["fields"] if x["term"] and x["index"] is not None}
    ec,oc=columns(c),columns(d)
    if "eventDate" not in ec or "scientificName" not in oc:
        raise ValueError("Original field date or species name missing")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        import xml.etree.ElementTree as ET
        xml=ET.fromstring(z.read("meta.xml"))
        rootcore=next((x for x in xml if x.tag.endswith("}core")),None)
        rootext=next((x for x in xml if x.tag.endswith("}extension")),None)
        if rootcore is None or rootext is None:
            raise ValueError("Malformed original Event core/Occurrence extension")
        eid=next((x for x in rootcore if x.tag.endswith("}id")),None)
        xid=next((x for x in rootext if x.tag.endswith("}coreid")),None)
        if eid is None or xid is None or eid.attrib.get("index")!="0" or xid.attrib.get("index")!="0":
            raise ValueError("Field event ID foreign key not original index0")
        import csv
        def parse(table,cols):
            with z.open(table["record_path"]) as stream:
                with io.TextIOWrapper(stream,encoding="utf-8-sig",newline="") as reader:
                    lines=csv.reader(reader,delimiter="\t")
                    for _ in range(int(table["ignore_header_lines"] or 0)):
                        next(lines,None)
                    for line in lines:
                        if not line or not any(line):continue
                        if any(i>=len(line) for i in cols.values()):
                            raise ValueError("Malformed original author DwC-A record fewer than metadata columns")
                        yield {"coreid":line[0],
                               **{k:line[i] for k,i in cols.items()}}
        events=list(parse(c,ec))
        occurrences=list(parse(d,oc))
    event_by_id={}
    valid_event_years=Counter()
    invalid_events=0
    for event in events:
        eid=event["coreid"]
        if eid in event_by_id:raise ValueError("Original source repeats same event coreid")
        when=(event.get("eventDate") or "").strip()
        try:dt=date.fromisoformat(when)
        except ValueError:
            invalid_events+=1;continue
        if dt<date(2017,1,1) or dt>date(2026,10,20):
            invalid_events+=1;continue
        island=normalized_locality(event.get("island"))
        if island!=source_island:
            raise ValueError("Original provider event island differs from frozen Sao Jorge location")
        event_by_id[eid]=(dt.year,island)
        valid_event_years[dt.year]+=1
    valid_occs=[]
    oc_by_year=Counter()
    unlinked=0
    for ob in occurrences:
        eid=ob["coreid"]
        if eid not in event_by_id:
            unlinked+=1;continue
        name=(ob.get("scientificName") or "").strip()
        if not canonical_binomial(name):
            continue
        rank=normalized_text(ob.get("taxonRank"))
        if rank and rank!="species":
            continue
        status=normalized_text(ob.get("occurrenceStatus"))
        if status=="absent":
            continue
        year,island=event_by_id[eid]
        valid_occs.append({"scientificName":name,"year":year,"island":island})
        oc_by_year[year]+=1
    return {
        "core_event_row_count":len(events),
        "occurrence_row_count":len(occurrences),
        "valid_post_2017_event_count":len(event_by_id),
        "invalid_or_nominal_date_event_count":invalid_events,
        "source_event_years":{str(k):v for k,v in sorted(valid_event_years.items())},
        "observations_by_event_year":{str(k):v for k,v in sorted(oc_by_year.items())},
        "unlinked_or_undated_occurrences":unlinked,
        "valid_occurrences":valid_occs,
        "source_island_location_validated":True,
        "source_name_and_date_respondents_limited_to_SaoJorge":True,
    }


def audit_dated_matches(record,losses):
    """Counts only, never expose literal source taxa or individual occurrence."""
    cases=[]
    for r in losses:
        if (normalized_text(r.get("Archipelago")) not in {"azores","acores"}
            or normalized_text(r.get("Extinction category"))!="extirpation (island level)"
            or normalized_text(r.get("Category"))!="well-supported"):
            continue
        binomial=canonical_binomial(r.get("Species"))
        if not binomial:
            continue
        isl=normalized_locality(r.get("Island"))
        if isl is None:raise ValueError("S1 Azores loss island not matched")
        cases.append((binomial,isl))
    bytax=defaultdict(set)
    for name,isl in cases:bytax[name].add(isl)
    observations=defaultdict(set)
    for r in record["valid_occurrences"]:
        n=canonical_binomial(r["scientificName"])
        if n and r["year"]>=2017 and r["island"]=="São Jorge":
            observations[n].add((r["island"],r["year"]))
    matched=set(bytax)&set(observations)
    same_lost={n for n in matched if "São Jorge" in bytax[n]}
    return {
        "strict_S1_Azores_taxa_submitted":len(bytax),
        "historically_lost_on_SaoJorge_taxa":sum("São Jorge" in x for x in bytax.values()),
        "matched_taxa_2020_recorded_on_saojorge":len(matched),
        "S1_taxa_with_source_confirmed_post_2017_field_occurrence":len(matched),
        "historically_lost_on_SaoJorge_taxa_with_2020_field_records":len(same_lost),
        "observed_years_for_matched_taxa":dict(sorted(Counter(
            yr for taxon in matched for _,yr in observations[taxon]).items())),
        "evidence_of_documented_later_field_detection_not_recolonization":True,
        "not_confirmed_breeding_or_viable_source_populations":True,
        "no_unobserved_zero_imputation":True,
        "no_individual_scientific_names_or_sampled_occurrence_ids_exported":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    cfg=json.loads(args.contract.read_text(encoding="utf8"))
    if cfg.get("schema")!="structural.azores2020_SaoJorge_field_observations_vs_S1_cases.v1_269":
        raise ValueError("Original prospective field records contract missing")
    if cfg["status"]!="FROZEN_BEFORE_FIELD_EVENT_OCCURRENCE_RECORD_VALUES_OPENED":
        raise ValueError("Field record exposure status changed")
    if cfg["source"]["exact_original_DwCA"]!=SRC_URL or cfg["loss_source"]["sha256"]!=S1_SHA:
        raise ValueError("Original source URL or historical source provenance changed")
    result={
        "schema":"structural.azores2020_SaoJorge_field_record_case_crosscheck.v1_269",
        "status":"STOP_BEFORE_FIELD_RECORD_ECOLOGICAL_INTERPRETATION",
        "historical_S1_source_sha256":S1_SHA,
        "S2_S3_S4_values_opened":0,
        "GEB_scientific_HOLD":True,"eBird_used":False,
    }
    try:
        req=urllib.request.Request(SRC_URL,headers={
            "User-Agent":"Structural-2020-SaoJorge-DatedFieldSourceAudit/1.0",
            "Accept":"application/zip,application/octet-stream"})
        with urllib.request.urlopen(req,timeout=60) as stream:
            raw=stream.read(10_000_001)
        if len(raw)>10_000_000:raise ValueError("Original Sao Jorge source exceeds 10MB limit")
        source_sha=hashlib.sha256(raw).hexdigest()
        records=parse_event_occurrence(raw,cfg["source"]["target_island"])
        s1=download_original(S1_URL,332776,5_000_000)
        if hashlib.sha256(s1).hexdigest()!=S1_SHA:
            raise ValueError("CSIC S1 original publisher hash mismatch")
        losses=parse_sheet_s1(s1)
        if len(losses)!=168:raise ValueError("CSIC published S1 case frame changed")
        matched=audit_dated_matches(records,losses)
        if matched["strict_S1_Azores_taxa_submitted"]!=20:
            raise ValueError("Previously frozen 20 Azorean S1 taxon names changed")
        safe={k:v for k,v in records.items() if k!="valid_occurrences"}
        result.update({
            "source_DwCA_sha256":source_sha,"source_DwCA_bytes":len(raw),
            "original_archive":safe,"field_result":matched,
            "strict_S1_Azores_source_loss_cases":24,
            "strict_S1_Azores_source_loss_taxa":20,
            "status":"ORIGINAL_DATED_FIELD_OBSERVATION_CROSSCHECK",
        })
    except Exception as e:
        result["stop_type"]=type(e).__name__
        result["stop_reason"]=str(e)[:450]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({
        "status":result["status"],
        "event_rows":result.get("original_archive",{}).get("core_event_row_count"),
        "2020_S1_taxa_with_field_observations":result.get("field_result",{}).get("matched_taxa_2020_recorded_on_saojorge"),
        "loss_island_field_overlap":result.get("field_result",{}).get("historically_lost_on_SaoJorge_taxa_with_2020_field_records"),
        "error":result.get("stop_reason")},sort_keys=True))
    if result["status"]!="ORIGINAL_DATED_FIELD_OBSERVATION_CROSSCHECK":
        raise SystemExit(2)


if __name__=="__main__":
    main()
