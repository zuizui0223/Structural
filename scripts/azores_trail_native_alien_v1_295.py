#!/usr/bin/env python3
"""v1.295 one-shot observational trail-edge/interior plant composition test.

Only run if frozen v1.294 Event-only source frame fingerprint matches.
The response of this 2026-published source is independent from 2013 MOVECLIM
and 2017/2018 ForestEco2, but this is NOT a pristine confirmatory experiment.
One publication-source response opening; no post-hoc relabel/tuning/replay.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,urllib.request,xml.etree.ElementTree as ET,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from azores_trail_plants_event_hierarchy_v1_292 import SHA,SOURCE,parse_source_events
from azores_trail_new_event_frame_v1_294 import profile,parse_event
from azores_trail_plants_opaque_source_v1_291 import parse_opaque_archive

def local(x): return x.rsplit("}",1)[-1]
def term(x): return x.rstrip("/").split("/")[-1].split("#")[-1]
def norm(x):return " ".join(str(x or "").casefold().strip().replace("_"," ").replace("-"," ").split())

def original_occurrence(archive):
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        xml=ET.fromstring(z.read("meta.xml"))
        nodes=[v for v in xml if local(v.tag)=="extension" and v.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(nodes)!=1: raise ValueError("Original source does not declare one Occurrence extension")
        cols={};coreindex=None;path=None
        for v in nodes[0].iter():
            t=local(v.tag)
            if t=="field" and "term" in v.attrib and "index" in v.attrib:cols[term(v.attrib["term"])]=int(v.attrib["index"])
            elif t=="coreid" and "index" in v.attrib:coreindex=int(v.attrib["index"])
            elif t=="location" and v.text:path=v.text.strip()
        required={"scientificName","establishmentMeans","taxonRank"}
        if coreindex is None or not path or not required.issubset(cols):
            raise ValueError("Biological source has no frozen nativeness, taxon-rank or event join")
        sep=nodes[0].attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        if len(sep)!=1:raise ValueError("Bad source taxon occurrence delimiter")
        ignore=int(nodes[0].attrib.get("ignoreHeaderLines","0"))
        if ignore<0 or ignore>2:raise ValueError("Bad source biological header length")
        records=[]
        with z.open(path) as stream:
            with io.TextIOWrapper(stream,encoding="utf-8-sig",newline="") as f:
                r=csv.reader(f,delimiter=sep)
                for _ in range(ignore):next(r,None)
                for values in r:
                    if not values or not any(values):continue
                    if max(coreindex,*(cols[k] for k in required))>=len(values):
                        raise ValueError("Malformed published plant record width")
                    rec={k:values[v] for k,v in cols.items() if v<len(values)}
                    rec["original_coreid"]=values[coreindex]
                    records.append(rec)
        return records

def frame_membership(events,physical_contract):
    # Reproduce event-only v1.294 exactly from original author Event values.
    result=profile(events,physical_contract)
    if result["status"]!="RETROSPECTIVE_MATCHED_FRAME_PASS_ONLY_OCCURRENCE_STILL_SEALED":
        raise ValueError("Response-independent v1.294 sampling eligibility not achieved")
    need=set(("50","100","150"))
    by_group=defaultdict(lambda:defaultdict(set))
    parsed={}
    for e in events:
        p,reason=parse_event(e)
        if reason:continue
        core=str(e["original_coreid"]).strip()
        parsed[core]=p
        by_group[p[:4]][p[4]].add(p[5])
    groups={}
    for key,by_plot in by_group.items():
        if not need.issubset(by_plot.get("1",set())):continue
        intr=[x for x in ("2","3") if need.issubset(by_plot.get(x,set()))]
        if not intr:continue
        groups[key]={"1",*intr}
    ids={k for k,p in parsed.items() if p[:4] in groups and p[4] in groups[p[:4]] and p[5] in need}
    digest=hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
    if digest!=result["future_scoring_event_coreids_sha256"] or len(ids)!=result["number_source_Event_rows_qualifying_for_future_score"]:
        raise AssertionError("Original source Event inclusion fingerprint does not replay")
    return ids,parsed,groups,result

def score_from_records(events,occ,contract,physical_contract,receipt):
    allowed_ids,parsed,groups,frame=frame_membership(events,physical_contract)
    expected=receipt["future_scoring_event_coreids_sha256"]
    if (frame["future_scoring_event_coreids_sha256"]!=expected
        or len(allowed_ids)!=receipt["number_original_Event_rows_eligible_for_score"]
        or frame["original_2026_v1_4_Event_rows"]!=receipt["source_original_Event_rows"]
        or receipt["status"]!="RETROSPECTIVE_MATCHED_FRAME_PASS_ONLY_OCCURRENCE_STILL_SEALED"):
        raise ValueError("Committed original physical design receipt mismatch; do not open score")
    # Exact source identity and all source rows are already verified above by CLI.
    all_event_ids={str(x["original_coreid"]).strip() for x in events}
    matched=0
    recognized=0;unknown=0;species_rank_rows=0
    classifications=defaultdict(set)
    observed=set()
    eligible_status={"native":set(map(norm,contract["physical_sample_fixed"]["origin_status"].split("as native;")[0].replace("Normalize exact DarwinCore establishmentMeans values ","").split("/")))}
    # Use explicit fixed dictionary from contract's frozen status sentence.
    native={"native","indigenous","endemic","azorean endemic","native nonendemic"}
    alien={"introduced","invasive","naturalized","naturalised"}
    for row in occ:
        core=str(row.get("original_coreid","")).strip()
        if core in all_event_ids:matched+=1
        else:continue
        if norm(row.get("taxonRank"))!="species":continue
        name=str(row.get("scientificName","")).strip()
        if not name:continue
        species_rank_rows+=1
        kind=norm(row.get("establishmentMeans"))
        island=parsed[core][0] if core in parsed else None
        if kind in native:c="native";recognized+=1
        elif kind in alien:c="alien";recognized+=1
        else:c="unknown";unknown+=1
        if island is not None:
            classifications[(island,name)].add(c)
        if core in allowed_ids:observed.add((core,name))
    coverage=matched/len(occ) if occ else 0
    unknown_fraction=unknown/species_rank_rows if species_rank_rows else 1
    result={
      "schema":"structural.azores_trail_native_alien_result.v1_295",
      "status":"STOP_ORIGINAL_BIOLOGICAL_QUALITY_OR_SUPPORT",
      "source_archived_Event_rows":len(events),
      "source_archived_Occurrence_rows":len(occ),
      "source_Event_join_coverage":coverage,
      "species_rank_records_with_name":species_rank_rows,
      "species_rank_unknown_nativeness_count":unknown,
      "species_rank_unknown_nativeness_fraction":unknown_fraction,
      "observed_original_species_core_pairs_within_frozen_frame":len(observed),
      "frozen_eligible_Event_rows":len(allowed_ids),
      "frozen_original_eligible_Event_SHA256":expected,
      "original_v1_292_terminal":True,
      "source_from_2017_19_tourism_trails_not_original_Pico":True,
      "score":None,
      "per_trail":None,"per_island":None,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False,
      "not_causal_trampling_or_natal_dispersal":True,
      "no_original_Pico_mammal_BioTIME_RLS_response_reopened":True,
    }
    quality=contract["estimability"]
    if coverage<quality["min_original_Occurrence_join_fraction"]:
        result["stop_reason"]="insufficient_original_occurrence_Event_join_coverage";return result
    if unknown_fraction>quality["max_ambiguous_status_fraction_of_original_species_rank_Records"]:
        result["stop_reason"]="unclassified_native_introduced_status_exceeds_frozen_gate";return result
    if not species_rank_rows:
        result["stop_reason"]="no_original_species_rank_records";return result
    # Each (island,species) must have a consistent original author origin status.
    # No fuzzy taxonomic or status repair after outcome exposure.
    pairs=defaultdict(lambda:{"native":set(),"alien":set()})
    for core,name in observed:
        p=parsed[core]
        types=classifications[(p[0],name)]
        if types=={"native"}:pairs[p[:5]]["native"].add(name)
        elif types=={"alien"}:pairs[p[:5]]["alien"].add(name)
    per_group=defaultdict(lambda:defaultdict(dict))
    for key,who in groups.items():
        for plot in who:
            per_group[key][plot]=pairs.get(key+(plot,),{"native":set(),"alien":set()})
    taxa_native=defaultdict(set);taxa_alien=defaultdict(set)
    for key,plots in per_group.items():
        for p,v in plots.items():
            taxa_native[key[0]].update(v["native"])
            taxa_alien[key[0]].update(v["alien"])
    if any(len(taxa_alien[i])<quality["min_intro_species_by_island"] or
           len(taxa_native[i])<quality["min_native_species_by_island"]
           for i in ("Terceira","São Miguel")):
        result["stop_reason"]="insufficient_native_or_introduced_species_on_one_island";return result
    if len(per_group)<quality["min_matched_area_groups"]:
        result["stop_reason"]="insufficient_trail_groups";return result
    d_by_trail=defaultdict(list);nat_d=defaultdict(list);alien_d=defaultdict(list)
    for key,plots in per_group.items():
        island,year,trail,area=key
        def counts(plot):
            val=plots[plot];return len(val["native"]),len(val["alien"])
        e_nat,e_alien=counts("1")
        e=math.log((e_nat+0.5)/(e_alien+0.5))
        interior=[p for p in ("2","3") if p in plots]
        vals=[counts(p) for p in interior]
        i=sum(math.log((v[0]+0.5)/(v[1]+0.5)) for v in vals)/len(vals)
        d_by_trail[(island,trail)].append(i-e)
        nat_d[(island,trail)].append(sum(v[0] for v in vals)/len(vals)-e_nat)
        alien_d[(island,trail)].append(sum(v[1] for v in vals)/len(vals)-e_alien)
    trailers=[]
    for i in ("Terceira","São Miguel"):
        tracks=sorted({k[1] for k in d_by_trail if k[0]==i})
        for no,name in enumerate(tracks,1):
            key=(i,name)
            trailers.append({
              "island":i,"within_island_anonymized_trail_number":no,
              "matched_area_year_groups":len(d_by_trail[key]),
              "native_relative_to_alien_logratio_interior_minus_edge":sum(d_by_trail[key])/len(d_by_trail[key]),
              "native_richness_interior_minus_edge":sum(nat_d[key])/len(nat_d[key]),
              "alien_richness_interior_minus_edge":sum(alien_d[key])/len(alien_d[key])
            })
    by_island={i:{
       "distinct_trails":len([z for z in trailers if z["island"]==i]),
       "matched_area_year_groups":sum(z["matched_area_year_groups"] for z in trailers if z["island"]==i),
       "mean_over_trails_log_native_vs_alien_interior_minus_edge":
           sum(z["native_relative_to_alien_logratio_interior_minus_edge"] for z in trailers if z["island"]==i)/
           len([z for z in trailers if z["island"]==i]),
       "native_taxa_in_original_matched_frame":len(taxa_native[i]),
       "alien_taxa_in_original_matched_frame":len(taxa_alien[i])
       } for i in ("Terceira","São Miguel")}
    result["status"]="SOURCE_OBSERVATIONAL_TRAIL_COMPOSITION_DESCRIPTIVE_SCORE"
    result["score"]={
       "mean_across_original_independent_trails_log_native_vs_alien_interior_minus_edge":
           sum(z["native_relative_to_alien_logratio_interior_minus_edge"] for z in trailers)/len(trailers),
       "trails_positive_direction":sum(z["native_relative_to_alien_logratio_interior_minus_edge"]>0 for z in trailers),
       "independent_trails":len(trailers),
       "note":"Descriptive, not p-value, confidence interval or 2-independent-archipelago replication."
    }
    result["per_trail"]=trailers
    result["per_island"]=by_island
    return result

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--contract",required=True,type=Path)
    a.add_argument("--event-contract",required=True,type=Path)
    a.add_argument("--event-receipt",required=True,type=Path)
    a.add_argument("--out",required=True,type=Path)
    args=a.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    ec=json.loads(args.event_contract.read_text(encoding="utf-8"))
    receipt=json.loads(args.event_receipt.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.azores_trail_independent_native_alien_v1_295"
       or c.get("status")!="PROSPECTIVE_TO_PLANT_RESPONSE_RETROSPECTIVE_TO_EVENT_DESIGN_FROZEN"
       or c["source"]["sha256"]!=SHA
       or ec.get("status")!="NEW_RETROSPECTIVE_EVENT_EXPOSED_RESPONSE_SEALED_PROTOCOL_FROZEN"
       or receipt.get("status")!="RETROSPECTIVE_MATCHED_FRAME_PASS_ONLY_OCCURRENCE_STILL_SEALED"):
        raise ValueError("New independent plant response not prospectively frozen")
    output={"schema":"structural.azores_trail_native_alien_result.v1_295",
            "status":"SOURCE_OR_REPLAY_TECHNICAL_TERMINAL_STOP",
            "original_occurrence_rows_opened":0,
            "score":None,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-Azores-Trail-v1.295-OneShot-Biological"})
        with urllib.request.urlopen(req,timeout=60) as r:original=r.read(1_000_001)
        if len(original)>1_000_000 or hashlib.sha256(original).hexdigest()!=SHA:
            raise ValueError("Original 2026 source ZIP sha256 mismatch")
        if parse_opaque_archive(original)["status"]!="SCHEMA_POSSIBLE_EVENT_UNOPENED":
            raise ValueError("Original source schema changed")
        events=parse_source_events(original)
        # Strong gate BEFORE first species record: frozen Event-only receipt.
        ids,parsed,groups,frame=frame_membership(events,ec)
        if frame["future_scoring_event_coreids_sha256"]!=receipt["future_scoring_event_coreids_sha256"]:
            raise ValueError("Matched original Event fingerprint differs")
        # First and only original plant response read follows eligibility gate.
        occurrences=original_occurrence(original)
        output["original_occurrence_rows_opened"]=len(occurrences)
        output=score_from_records(events,occurrences,c,ec,receipt)
        output["original_occurrence_rows_opened"]=len(occurrences)
        output["original_source_sha256"]=SHA
    except Exception as e:
        output["stop_type"]=type(e).__name__
        output["stop_reason"]=str(e)[:350]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:output.get(k) for k in ("status","original_occurrence_rows_opened",
      "species_rank_unknown_nativeness_fraction","source_Event_join_coverage","score","per_island","stop_reason")},sort_keys=True))
    # Gate STOP is a completed scientific negative eligibility decision, not
    # evidence for/against an ecological sign. Terminal technical STOP is CI failure.
    if output["status"]=="SOURCE_OR_REPLAY_TECHNICAL_TERMINAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
