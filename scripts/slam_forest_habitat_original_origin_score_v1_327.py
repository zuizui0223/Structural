#!/usr/bin/env python3
"""SLAM v1.327: three-island same-quarter native/altered forest taxon response.

One-shot original v1.7 source analysis. v1.326 42 physical site/664 source
Event IDs and habitat ontology were fixed BEFORE first taxonomic response
access. Measures per-source-Event absolute indigenous, endemic and introduced
species richness, then native-minus-altered WITHIN each island×year×quarter.
Three island equal means, no 664-sampling-Event pseudo-independent p-values.

Separate Beetle/within-forest spatial similarity endpoints remain secondary.
Neither original BALA nor PRIBES species records is reopened. Not direct
observed invasion, causal canopy manipulation or population persistence.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,itertools,json,math,statistics,unicodedata
import urllib.request,zipfile,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path

from slam_forest_original_event_habitat_gate_v1_326 import (
    SOURCE,SHA,MAX_BYTES,event_core_only,audit as event_audit,
    _island,_calendar,habitat,mode,siteid,local,term
)

GUILDS=("all_arthropods","coleoptera")
ORIGINS=("endemic","native","introduced")
ISLANDS=("FLO","PIC","TER")
EXPECTED_QUARTERS={"FLO":6,"PIC":30,"TER":34}
SOURCE_SELECT_SHA="105842bd22226d88810d8d816e629a5e8829a2971f58a45b1ed69d2594712686"
SOURCE_SITE_SHA="703cfb63183b7c46095f6349f24a7a84114cec18b744b6d38332de717bb3cf50"

def original_occurrence_rows(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        ext=[x for x in root if local(x.tag)=="extension"
             and x.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(ext)!=1:raise ValueError("Original source must have one Occurrence extension")
        node=ext[0];data=[];columns={};coreidx=None
        for v in node.iter():
            tag=local(v.tag)
            if tag=="field" and "index" in v.attrib and "term" in v.attrib:
                columns[term(v.attrib["term"])]=int(v.attrib["index"])
            elif tag=="location" and v.text:data.append(v.text.strip())
            elif tag=="coreid" and "index" in v.attrib:coreidx=int(v.attrib["index"])
        fields={"scientificName","taxonRank","order","establishmentMeans"}
        if coreidx is None or len(data)!=1 or not fields.issubset(columns):
            raise ValueError("Source original Occurrence name, order, rank and origin link missing")
        sep=node.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        header=int(node.attrib.get("ignoreHeaderLines","0"))
        if len(sep)!=1 or header not in (0,1):
            raise ValueError("Unrecognized source original Occurrence TSV serialization")
        records=[]
        with z.open(data[0]) as raw:
            with io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as source:
                rows=csv.reader(source,delimiter=sep)
                for _ in range(header):next(rows,None)
                for row in rows:
                    if not row or not any(row):continue
                    if max(coreidx,*(columns[x] for x in fields))>=len(row):
                        raise ValueError("Original source Occurrence row incomplete")
                    entry={key:row[pos] for key,pos in columns.items() if pos<len(row)}
                    entry["__foreign_event_coreid"]=row[coreidx]
                    records.append(entry)
        return records

def status_token(s):
    v=unicodedata.normalize("NFKC",str(s or "")).casefold()
    return " ".join(v.replace("-"," ").replace("_"," ").split())

def taxon_token(s):
    return " ".join(unicodedata.normalize("NFKC",str(s or "")).casefold().split())

def category(raw,contract):
    ontology=contract["taxon_ontology_frozen"]
    k=status_token(raw)
    matched=[
       typ for typ,source_field in (("endemic","endemic_exact"),
                                    ("native","native_exact"),
                                    ("introduced","introduced_exact"))
       if k in ontology[source_field]
    ]
    return matched[0] if len(matched)==1 else None

def reconstruct_event_sample(events,event_contract,receipt):
    previous=event_audit(events,event_contract)
    if (
      previous["status"]!="ORIGINAL_SLAM_FOREST_HABITAT_STRATA_ELIGIBLE_TAXON_RESPONSES_SEALED"
      or previous["source_selected_original_Event_coreids_SHA256"]!=SOURCE_SELECT_SHA
      or previous["source_selected_original_physical_plot_key_SHA256"]!=SOURCE_SITE_SHA
      or previous["source_selected_original_Event_rows_in_matched_habitat_strata"]!=664
      or previous["source_selected_physical_plots_with_matched_habitat_period_method"]!=33
      or previous["source_original_SHA256"]!=SHA
      or receipt.get("selected_source_Event_coreid_SHA256")!=SOURCE_SELECT_SHA
      or receipt.get("selected_original_physical_plot_key_SHA256")!=SOURCE_SITE_SHA
      or receipt.get("original_source_Event_n")!=893
      or receipt.get("original_selected_islands")!=list(ISLANDS)
      or receipt.get("matched_source_island_year_quarter_stratum_counts")!=EXPECTED_QUARTERS
    ):
        raise ValueError("Original response-independent 664 source Event/33 site fingerprint changed")
    aliases=event_contract["fixed_island_aliases"]
    ontology=event_contract["habitat_ontology_frozen"]
    method_count=Counter(mode(row.get("samplingProtocol")) for row in events)
    maximum=max(method_count.values())
    method=min(k for k,v in method_count.items() if k and v==maximum)
    if hashlib.sha256(method.encode()).hexdigest()!=receipt["original_sampling_protocol_sha256"]:
        raise ValueError("Original source samplingProtocol SHA changed")
    rows=defaultdict(list)
    for e in events:
        isl=_island(e.get("island"),aliases)
        if not isl:raise ValueError("Original source island code not normalized")
        ident=siteid(e.get("locationID"))
        year,quarter=_calendar(e.get("eventDate"))
        kind=habitat(e.get("habitat"),ontology)
        if kind is None:raise ValueError("Original source habitat ontology became unknown")
        if mode(e.get("samplingProtocol"))!=method:continue
        key=(isl,year,quarter,ident)
        rows[key].append((str(e["__original_coreid"]).strip(),kind))
    by_window=defaultdict(list)
    for (isl,year,quarter,ident),values in rows.items():
        label={x[1] for x in values}
        if len(label)!=1:raise ValueError("Original same-site source habitat changed")
        kind=next(iter(label))
        chosen=min(x[0] for x in values)
        habitat_group="native" if kind=="native" else "altered"
        by_window[(isl,year,quarter)].append((chosen,ident,habitat_group,kind))
    selected={}
    windows=defaultdict(list)
    source_sites=set()
    for key,values in sorted(by_window.items()):
        isl,year,quarter=key
        if isl not in ISLANDS:continue
        groups=Counter(x[2] for x in values)
        if groups["native"]<2 or groups["altered"]<2:continue
        windows[isl].append(key)
        for core,ident,group,kind in values:
            if core in selected:raise ValueError("Source original sample Event reused across separate seasons")
            selected[core]=(isl,year,quarter,ident,group,kind)
            source_sites.add((isl,ident))
    if (
      len(selected)!=664 or len(source_sites)!=33
      or {isl:len(windows[isl]) for isl in ISLANDS}!=EXPECTED_QUARTERS
      or hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest()!=SOURCE_SELECT_SHA
      or hashlib.sha256("\n".join(f"{isl}|{site}" for isl,site in sorted(source_sites)).encode()).hexdigest()!=SOURCE_SITE_SHA
    ):
        raise ValueError("Source original v1.326 Event ID selection not reproduced exactly")
    return selected,windows

def _mean(xs):
    return statistics.fmean(xs) if xs else None

def _jaccard(a,b):
    if not a or not b:return None
    return len(a&b)/len(a|b)

def _richness(tax_sets,origin,core,guild):
    if origin=="indigenous":
        return len(tax_sets.get((core,guild,"native"),set()) |
                   tax_sets.get((core,guild,"endemic"),set()))
    return len(tax_sets.get((core,guild,origin),set()))

def guild_score(selected,windows,tax_sets,guild,min_quarters):
    source_quarter_means={}
    sitepair_similarity=defaultdict(lambda:defaultdict(lambda:defaultdict(list)))
    selected_nonempty=sum(
        bool(set().union(*(tax_sets.get((core,guild,status),set()) for status in ORIGINS)))
        for core in selected)
    for island in ISLANDS:
        original_period_rows=[]
        for key in windows[island]:
            candidates=[(core,row) for core,row in selected.items()
                        if row[:3]==key]
            native=[core for core,row in candidates if row[4]=="native"]
            altered=[core for core,row in candidates if row[4]=="altered"]
            if len(native)<2 or len(altered)<2:
                raise ValueError("Original source equal-time habitat plot contrast changed")
            metrics={}
            for origin in ("indigenous","endemic","native","introduced"):
                nv=_mean([_richness(tax_sets,origin,c,guild) for c in native])
                al=_mean([_richness(tax_sets,origin,c,guild) for c in altered])
                metrics[f"{origin}_richness_native_forest"]=nv
                metrics[f"{origin}_richness_altered_forest"]=al
                metrics[f"{origin}_richness_native_minus_altered"]=nv-al
                # Community spatial similarity within habitat, not independent
                # site-pair samples or strong formal inference.
                for label,cores in (("native",native),("altered",altered)):
                    sets=[
                      (tax_sets.get((c,guild,"native"),set()) |
                       tax_sets.get((c,guild,"endemic"),set()))
                      if origin=="indigenous" else tax_sets.get((c,guild,origin),set())
                      for c in cores
                    ]
                    vals=[_jaccard(a,b) for a,b in itertools.combinations(sets,2)]
                    sitepair_similarity[island][origin][label].extend(v for v in vals if v is not None)
            metrics["origin_habitat_double_contrast"]=(
                metrics["indigenous_richness_native_minus_altered"]-
                metrics["introduced_richness_native_minus_altered"]
            )
            original_period_rows.append(metrics)
        if not original_period_rows:
            raise ValueError("No original matched seasonal plots")
        source_quarter_means[island]={
            "original_matched_source_year_quarter_strata":len(original_period_rows),
            "original_season_mean_community_statistics":{
               k:_mean([r[k] for r in original_period_rows]) for k in original_period_rows[0]
            },
            "quarter_strata_with_positive_indigenous_relative_double_contrast":
                sum(r["origin_habitat_double_contrast"]>0 for r in original_period_rows),
        }
    island_values=[source_quarter_means[i]["original_season_mean_community_statistics"] for i in ISLANDS]
    overall={
        metric:_mean([row[metric] for row in island_values])
        for metric in island_values[0]
    }
    sim={
      isl:{
        origin:{
          label:{
             "dependent_original_plot_pairs_with_two_nonempty_taxon_sets":len(sitepair_similarity[isl][origin][label]),
             "mean_same_habitat_source_site_pair_jaccard_similarity":_mean(sitepair_similarity[isl][origin][label])
          }
          for label in ("native","altered")
        }
        for origin in ("indigenous","introduced")
      } for isl in ISLANDS
    }
    qualifies=(guild=="all_arthropods" or (
        selected_nonempty/len(selected)>=0.5
        and all(source_quarter_means[i]["original_matched_source_year_quarter_strata"]>=4
                for i in ISLANDS)))
    return {
        "status":"OBSERVED_ORIGIN_SPECIFIC_HABITAT_RICHNESS_CONTRAST" if qualifies else
             "STOP_SECONDARY_COLEOPTERA_DETECTION_FLOOR_NOT_MET",
        "source_original_selected_Event_n":len(selected),
        "source_Events_with_named_detected_taxa_in_this_guild":selected_nonempty,
        "source_named_taxon_source_Event_detection_fraction":selected_nonempty/len(selected),
        "original_islands":list(ISLANDS),
        "original_island_equal_season_mean":overall if qualifies else None,
        "original_per_island_source_quarter_mean":source_quarter_means if qualifies else None,
        "source_within_habitat_site_pair_similarity_by_island":sim if qualifies else None,
        "source_quarters_are_repeated_sampling_not_independent":True
    }

def score_original(events,occ,study,event_contract,receipt):
    selected,windows=reconstruct_event_sample(events,event_contract,receipt)
    if len(occ)!=14922:
        raise ValueError("Original source Occurrence record total changed from official version v1.7")
    all_core={str(r["__original_coreid"]).strip() for r in events}
    joined=0;event_with_any=set();accepted=Counter();taxa=defaultdict(set);origins=defaultdict(set)
    ontology=study["taxon_ontology_frozen"]
    ranks=set(ontology["taxon_rank_exact"])
    for rec in occ:
        core=str(rec.get("__foreign_event_coreid","")).strip()
        if core in all_core:joined+=1
        if core not in selected:continue
        event_with_any.add(core)
        accepted["selected_occurrence_records"]+=1
        taxon=taxon_token(rec.get("scientificName"))
        rank=taxon_token(rec.get("taxonRank"))
        if not taxon or rank not in ranks:
            accepted["unknown_or_higher_rank_named_species_records"]+=1
            continue
        accepted["eligible_named_species_rank_records"]+=1
        origin=category(rec.get("establishmentMeans"),study)
        if origin is None:
            accepted["eligible_species_rank_origin_UNKNOWN"]+=1
            continue
        accepted["recognized_source_origin_"+origin]+=1
        island=selected[core][0]
        origins[(island,taxon)].add(origin)
        taxa[(core,"all_arthropods",origin)].add(taxon)
        if taxon_token(rec.get("order"))=="coleoptera":
            taxa[(core,"coleoptera",origin)].add(taxon)
    full_join=joined/len(occ)
    sampled_cov=len(event_with_any)/len(selected)
    known=accepted["eligible_named_species_rank_records"]
    unclassified=accepted["eligible_species_rank_origin_UNKNOWN"]/known if known else 1.0
    conflicts=sum(len(group)>1 for group in origins.values())
    quality=study["quality_and_scientific_stop"]
    base={
        "schema":"structural.slam_three_island_original_forest_habitat_response.v1_327",
        "status":"STOP_ORIGINAL_SPECIES_STATUS_OR_CAPTURE_QUALITY",
        "original_source_archive_sha256":SHA,
        "source_original_Event_rows_reexamined":len(events),
        "source_original_Occurrence_rows_opened_once":len(occ),
        "original_source_Event_Occurrence_join_fraction":full_join,
        "original_selected_matched_source_Event_rows":len(selected),
        "original_selected_source_Events_with_any_occurrence":len(event_with_any),
        "original_selected_source_Event_record_coverage_fraction":sampled_cov,
        "source_species_filter_counts":dict(accepted),
        "source_origin_UNCLASSIFIED_fraction_selected_named_species":unclassified,
        "source_taxon_biogeographic_origin_conflicts_among_islands":conflicts,
        "original_source_islands_with_matched_native_altered_periods":list(ISLANDS),
        "original_source_periods_by_island":{island:len(windows[island]) for island in ISLANDS},
        "main_all_arthropods":None,
        "secondary_coleoptera":None,
        "not_true_local_extinction_colonization_or_invasion_source_flux":True,
        "source_original_habitat_gradient_observational_not_causal":True,
        "old_BALA_PRIBES_original_species_rows_reopened":0,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False
    }
    if (
        full_join<quality["min_original_Event_Occurrence_join_fraction"]
        or sampled_cov<quality["min_fraction_selected_Event_cores_with_at_least_one_original_occurrence"]
        or unclassified>quality["max_fraction_unclassified_origin_among_named_species_subspecies_selected_all_arthropod_records"]
        or conflicts>0
        or any(len(windows[i])<quality["minimum_valid_quarters_per_island"][i] for i in ISLANDS)
    ):
        base["stop_reason"]="Original source taxonomic origin, join or selected capture-period quality below frozen threshold"
        return base
    main=guild_score(selected,windows,taxa,"all_arthropods",quality["minimum_valid_quarters_per_island"])
    if main["status"]!="OBSERVED_ORIGIN_SPECIFIC_HABITAT_RICHNESS_CONTRAST":
        base["stop_reason"]="Original arthropod primary source score not estimable"
        return base
    beetle=guild_score(selected,windows,taxa,"coleoptera",quality["minimum_valid_quarters_per_island"])
    base["main_all_arthropods"]=main
    base["secondary_coleoptera"]=beetle
    base["status"]="SOURCE_OBSERVED_THREE_ISLAND_NATIVE_ALTERED_HABITAT_ORIGIN_CONTRAST_COMPLETE"
    return base

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("--protocol","--event-contract","--event-receipt"):
        p.add_argument(key,type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    study=json.loads(args.protocol.read_text(encoding="utf-8"))
    event=json.loads(args.event_contract.read_text(encoding="utf-8"))
    receipt=json.loads(args.event_receipt.read_text(encoding="utf-8"))
    src=study["source_frozen"]
    if (study.get("schema")!="structural.slam_42forest_origin_habitat_original_response.v1_327"
        or study.get("status")!="FROZEN_AFTER_ORIGINAL_EVENT_664_SAMPLES_BEFORE_FIRST_SLAM_OCCURRENCE_VALUE_READ"
        or src["original_archive_SHA256"]!=SHA
        or src["source_selected_event_coreids_SHA256"]!=SOURCE_SELECT_SHA
        or src["selected_eligible_source_Event_rows"]!=664
        or event.get("schema")!="structural.slam_forest_explicit_habitat_event_gate.v1_326"
        or receipt["source_original_v17_archive_SHA256"]!=SHA):
        raise ValueError("SLAM source original 3-island habitat response contract not frozen")
    result={
       "schema":"structural.slam_three_island_original_forest_habitat_response.v1_327",
       "status":"SOURCE_OR_ORIGINAL_SPECIES_READER_TECHNICAL_STOP",
       "source_original_Occurrence_rows_opened_once":0,
       "old_BALA_PRIBES_original_species_rows_reopened":0,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-SLAM-ThreeIsland-NativeForestHabitat-v1.327-one-shot"})
        with urllib.request.urlopen(req,timeout=75) as response:blob=response.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original source archive bytes changed")
        e=event_core_only(blob)
        reconstruct_event_sample(e,event,receipt)  # BEFORE first Occurrence read
        o=original_occurrence_rows(blob)
        result["source_original_Occurrence_rows_opened_once"]=len(o)
        result=score_original(e,o,study,event,receipt)
    except Exception as exc:
        result["stop_type"]=type(exc).__name__
        result["stop_reason"]=str(exc)[:330]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
       "status":result["status"],
       "original_occurrences_opened":result.get("source_original_Occurrence_rows_opened_once"),
       "selected_original_Event_n":result.get("original_selected_matched_source_Event_rows"),
       "unclassified_fraction":result.get("source_origin_UNCLASSIFIED_fraction_selected_named_species"),
       "main_habitat_contrasts":result.get("main_all_arthropods",{}).get("original_island_equal_season_mean") if result.get("main_all_arthropods") else None,
       "secondary_beetle_status":result.get("secondary_coleoptera",{}).get("status") if result.get("secondary_coleoptera") else None,
       "secondary_beetle_contrasts":result.get("secondary_coleoptera",{}).get("original_island_equal_season_mean") if result.get("secondary_coleoptera") else None,
       "stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="SOURCE_OR_ORIGINAL_SPECIES_READER_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":main()
