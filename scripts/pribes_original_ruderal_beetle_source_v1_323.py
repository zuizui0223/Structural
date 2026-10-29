#!/usr/bin/env python3
"""PRIBES v1.323 original introduced-beetle ruderal source-pool test.

One separately frozen, explicitly retrospective 72-source-site study (six
overlap islands only). BALA 1997–2022 original species values NEVER reopened.
PRIBES source-wide 80 Event and expected 2836 Occurrence originals read
once, only AFTER the v1.322 original source 1-hour 72-site Event hash
is independently recomputed. No taxon selection after inspecting labels.

Primary: across six island CONTEXTS, higher similarity of identified
introduced Beetle species among independently sampled ruderal sites
predicts stronger historical forest Beetle spatial homogenization?
Correlation is not dispersal observation, environmental causation or
cross-archipelago generalization. Native source pool negative control.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,itertools,json,math,statistics,unicodedata
import urllib.request,zipfile,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path

from pribes_original_event_sites_v1_321 import (
    SOURCE,SHA,MAX_SOURCE,OVERLAP,event_source_only,alphabetize,normalized_island
)
from pribes_original_onehour_sites_v1_322 import original_onehour_cohort

MAIN="coleoptera"
SECONDARY="araneae"
GUILDS=(MAIN,SECONDARY)
EXPECTED_OCC=2836
ORIGINAL_RECEIPT_SHA="ce4fb208cd02960c60e612e34a79d06c35dd08f06b181f5e687581549ede6178"
OLD_BALA_V318_SHA="f4e61ddbbd255d3a35a46fb0254273889516984b82479b3949e5edd79853af02"

def norm(s):
    return " ".join(unicodedata.normalize("NFKC",str(s or "")).casefold().split())

def origin_token(s):
    return " ".join(norm(s).replace("_"," ").replace("-"," ").split())

def local(s):return s.rsplit("}",1)[-1]
def term(s):return s.rstrip("/").split("/")[-1].split("#")[-1]

def occurrence_source_only_for_first_scoring(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        extensions=[e for e in root if local(e.tag)=="extension"
                    and e.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(extensions)!=1:raise ValueError("Missing original one-to-one Occurrence extension")
        node=extensions[0]
        cols={};coreidx=None;location=None
        for v in node.iter():
            k=local(v.tag)
            if k=="field" and "term" in v.attrib and "index" in v.attrib:
                cols[term(v.attrib["term"])]=int(v.attrib["index"])
            elif k=="coreid" and "index" in v.attrib:
                coreidx=int(v.attrib["index"])
            elif k=="location" and v.text:
                location=v.text.strip()
        required=("scientificName","order","taxonRank","establishmentMeans")
        if coreidx is None or location is None or any(k not in cols for k in required):
            raise ValueError("Original scientific name, order or origin schema not complete")
        sep=node.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        ignored=int(node.attrib.get("ignoreHeaderLines","0"))
        if len(sep)!=1 or ignored not in (0,1):
            raise ValueError("Unsupported original source Occurrence delimiter")
        records=[]
        with z.open(location) as raw:
            with io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as f:
                reader=csv.reader(f,delimiter=sep)
                for _ in range(ignored):next(reader,None)
                for row in reader:
                    if not row or not any(row):continue
                    if max(coreidx,*(cols[k] for k in required))>=len(row):
                        raise ValueError("Original source occurrence row is incomplete")
                    item={k:row[i] for k,i in cols.items() if i<len(row)}
                    item["__original_event_coreid"]=row[coreidx]
                    records.append(item)
        return records

def source_frame(events,onehour_contract,older,receipt):
    frame=original_onehour_cohort(events,onehour_contract,older)
    if (frame.get("status")!="NEW_SEPARATE_72_RUDERAL_SITES_ONEHOUR_EACH_TAXON_RESPONSES_SEALED"
        or receipt.get("source_v322_artifact_inner_JSON_sha256")!=ORIGINAL_RECEIPT_SHA
        or receipt.get("source_onehour_selected_original_Event_coreids_sha256")!=
           frame.get("source_onehour_selected_original_Event_coreids_sha256")
        or receipt.get("source_fullhour_physical_sites_six_overlap")!=72
        or frame.get("onehour_source_physical_sites_by_BALA_overlap_island")!=
           receipt.get("source_fullhour_sites_by_island")):
        raise ValueError("Original 72-site source response-blind Event fingerprint changed")
    aliases=older["field_contract"]["island_mapping_predeclared"]
    chosen={}
    for event in events:
        isl=normalized_island(event.get("island"),aliases)
        if isl not in OVERLAP:continue
        method=norm(event.get("samplingProtocol"))
        unit=norm(event.get("sampleSizeUnit"))
        try:value=float(str(event.get("sampleSizeValue","")).strip())
        except (TypeError,ValueError):continue
        if not (method=="vegetation beating" and unit=="hour" and value==1.0):
            continue
        site=alphabetize(event.get("locationID"))
        if not site:continue
        core=str(event.get("original_coreid","")).strip()
        if not core:continue
        key=(isl,site)
        if key not in chosen or core<chosen[key]:
            chosen[key]=core
    selected={core:key for key,core in chosen.items()}
    digest=hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest()
    if (len(selected)!=72 or len(chosen)!=72 or
        digest!=receipt["source_onehour_selected_original_Event_coreids_sha256"]):
        raise ValueError("Source Event inclusion fingerprint changed after original physical gate")
    return selected,frame

def ranks(values):
    ordering=sorted(range(len(values)),key=lambda i:values[i])
    result=[0.]*len(values)
    idx=0
    while idx<len(values):
        j=idx+1
        while j<len(values) and values[ordering[j]]==values[ordering[idx]]:
            j+=1
        average=(idx+1+j)/2.
        for k in range(idx,j):
            result[ordering[k]]=average
        idx=j
    return result

def spearman(xs,ys):
    if len(xs)!=len(ys) or len(xs)<3:raise ValueError("Invalid source island rank sample")
    a=ranks(xs);b=ranks(ys)
    ma=statistics.fmean(a);mb=statistics.fmean(b)
    va=math.fsum((v-ma)**2 for v in a)
    vb=math.fsum((v-mb)**2 for v in b)
    if va<=0 or vb<=0:return None
    return math.fsum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(va*vb)

def exact_island_permutation(xs,ys):
    if len(xs)!=6 or len(ys)!=6:raise ValueError("Must have all six fixed overlap islands")
    obs=spearman(xs,ys)
    if obs is None:return None
    values=[spearman(xs,v) for v in itertools.permutations(ys)]
    if len(values)!=720 or any(x is None for x in values):
        raise AssertionError("Exhaustive original source island null not computed")
    return {"spearman_rho":obs,
            "exact_island_label_permutations":720,
            "one_sided_positive_association_permutation_p":
                 sum(x>=obs-1e-12 for x in values)/720.,
            "two_sided_absolute_association_permutation_p":
                 sum(abs(x)>=abs(obs)-1e-12 for x in values)/720.}

def island_site_similarity(site_sets,sites,minimum=4,distinct_min=2):
    nonempty=[site_sets.get(s,set()) for s in sorted(sites) if site_sets.get(s)]
    taxa=set().union(*nonempty) if nonempty else set()
    summary={
        "original_onehour_physical_sites":len(sites),
        "sites_with_nonempty_recognized_source_taxon_set":len(nonempty),
        "distinct_recognized_taxa":len(taxa),
        "dependent_source_site_pairs":len(nonempty)*(len(nonempty)-1)//2,
        "mean_source_site_pair_Jaccard_similarity":None,
        "source_site_similarity_admissible":False
    }
    if len(nonempty)<minimum or len(taxa)<distinct_min:
        return summary
    sim=[]
    for a,b in itertools.combinations(nonempty,2):
        union=a|b
        if not union:raise AssertionError("Empty pooled source site taxa")
        sim.append(len(a&b)/len(union))
    summary["mean_source_site_pair_Jaccard_similarity"]=statistics.fmean(sim)
    summary["source_site_similarity_admissible"]=True
    return summary

def score_original(events,occ,study,onehour_contract,older,receipt):
    selected,source_gate=source_frame(events,onehour_contract,older,receipt)
    if len(events)!=80 or len(occ)!=EXPECTED_OCC:
        raise ValueError("Original official PRIBES v1.3 Event/Occurrence row count differs")
    all_events={str(e.get("original_coreid","")).strip() for e in events}
    joined=sum(str(row.get("__original_event_coreid","")).strip() in all_events for row in occ)
    if joined/len(occ)<0.99:
        raise ValueError("Original PRIBES Occurrence-to-Event completeness below 99%")
    taxonomy=study["taxon_guild_and_origin"]
    categories={
       "introduced":set(taxonomy["introduced_status_exact_normalized"]),
       "native":set(taxonomy["native_nonendemic_exact_normalized"]),
       "endemic":set(taxonomy["endemic_exact_normalized"])
    }
    included=set(taxonomy["eligible_source_taxonRank_exact_normalized"])
    source_sites=defaultdict(set)
    for site in selected.values():
        source_sites[site[0]].add(site)
    by_site=defaultdict(set)
    status_by_taxon=defaultdict(set)
    counts=Counter()
    for row in occ:
        core=str(row.get("__original_event_coreid","")).strip()
        if core not in selected:continue
        order=norm(row.get("order"))
        if order not in GUILDS:continue
        counts["observed_araneae_and_coleoptera_original_records"]+=1
        rank=norm(row.get("taxonRank"))
        taxon=norm(row.get("scientificName"))
        if rank not in included or not taxon:
            counts["excluded_non_species_rank_or_unnamed"]+=1
            continue
        counts["identified_rank_named_records"]+=1
        status=origin_token(row.get("establishmentMeans"))
        kinds=[kind for kind,terms in categories.items() if status in terms]
        if len(kinds)!=1:
            counts["unclassified_source_origin_record"]+=1
            continue
        kind=kinds[0]
        counts["classified_source_origin_"+kind]+=1
        island,site=selected[core]
        status_by_taxon[(island,order,taxon)].add(kind)
        by_site[(island,site,order,kind)].add(taxon)
    conflicting=[k for k,v in status_by_taxon.items() if len(v)>1]
    source_unknown=(counts["unclassified_source_origin_record"]/
        counts["identified_rank_named_records"] if counts["identified_rank_named_records"] else 1.)
    per_island={}
    p={}
    control={}
    secondary={}
    for island in OVERLAP:
        sites=source_sites[island]
        p[island]=island_site_similarity({
            s:by_site.get((s[0],s[1],MAIN,"introduced"),set()) for s in sites
        },sites)
        control[island]=island_site_similarity({
            s:(by_site.get((s[0],s[1],MAIN,"native"),set()) |
               by_site.get((s[0],s[1],MAIN,"endemic"),set())) for s in sites
        },sites)
        secondary[island]=island_site_similarity({
            s:by_site.get((s[0],s[1],SECONDARY,"introduced"),set()) for s in sites
        },sites)
        per_island[island]={
            "original_source_1hour_sites":len(sites),
            "survey_year":receipt["source_fullhour_survey_year_by_island"][island],
            "introduced_beetle_source":p[island],
            "native_endemic_beetle_source_negative_control":control[island],
            "introduced_spider_source_secondary":secondary[island],
        }
    output={
       "schema":"structural.pribes_ruderal_external_beetle_source_result.v1_323",
       "status":"STOP_ORIGINAL_INTRO_BEETLE_SOURCE_SUPPORT_OR_ORIGIN",
       "source_original_archive_sha256":SHA,
       "source_original_Event_rows_opened":len(events),
       "source_original_Occurrence_rows_opened_once":len(occ),
       "source_original_Event_Occurrence_join_fraction":joined/len(occ),
       "source_original_BALA_independent_island_overlap_n":6,
       "source_onehour_physical_sites":len(selected),
       "source_onehour_original_coreid_sha256":receipt["source_onehour_selected_original_Event_coreids_sha256"],
       "source_taxonomic_filter_counts":dict(sorted(counts.items())),
       "source_unclassified_rank_named_origin_fraction":source_unknown,
       "original_conflicting_island_taxon_status_count":len(conflicting),
       "per_island":per_island,
       "primary_introduced_beetle_source_similarity_vs_forest_homogenization":None,
       "negative_control_native_endemic_beetle_source_similarity_vs_forest_homogenization":None,
       "secondary_introduced_spider_source_similarity_vs_forest_homogenization":None,
       "source_year_confounder_rank_correlation":None,
       "primary_specific_intro_source_signal_exploratory":False,
       "no_PRIBES_to_BALA_species_or_physical_site_join":True,
       "original_BALA_source_Event_and_Occurrence_rows_REOPENED":0,
       "source_original_full_80_Event_effort_gate_v1_321_TERMINAL":True,
       "source_original_72_site_study_post_Event_exploratory":True,
       "original_6_island_source_only_years_not_time_synchronous":True,
       "no_causal_dispersal_or_invasion_inferred":True,
       "GEB_scientific_HOLD":True,
       "new_confirmatory_systems":0,"eBird_used":False
    }
    if len(conflicting):
        output["stop_reason"]="Conflicting original taxon origin within same island";return output
    if (source_unknown>taxonomy["unclassified_status_max_fraction_among_all_original_selected_species_rank_colopepera_plus_araneae_records"]
        or counts["identified_rank_named_records"]==0):
        output["stop_reason"]="Original source species-rank origin ontology >20% unidentified";return output
    if any(not p[i]["source_site_similarity_admissible"] for i in OVERLAP):
        output["stop_reason"]="At least one source island lacks 4 nonempty introduced Beetle sites / 2 taxa";return output
    ys=[-study["frozen_BALA_island_forest_response"]["forest_beetle_spatial_simpson_B3_minus_B1_by_overlap_island"][i] for i in OVERLAP]
    xs=[p[i]["mean_source_site_pair_Jaccard_similarity"] for i in OVERLAP]
    primary=exact_island_permutation(xs,ys)
    if primary is None:
        output["stop_reason"]="All six source islands have no variation in introduced Beetle similarity";return output
    output["primary_introduced_beetle_source_similarity_vs_forest_homogenization"]=primary
    native=None
    if all(control[i]["source_site_similarity_admissible"] for i in OVERLAP):
        native=exact_island_permutation(
            [control[i]["mean_source_site_pair_Jaccard_similarity"] for i in OVERLAP],ys)
        output["negative_control_native_endemic_beetle_source_similarity_vs_forest_homogenization"]=native
    if all(secondary[i]["source_site_similarity_admissible"] for i in OVERLAP):
        output["secondary_introduced_spider_source_similarity_vs_forest_homogenization"]=exact_island_permutation(
            [secondary[i]["mean_source_site_pair_Jaccard_similarity"] for i in OVERLAP],ys)
    years=[receipt["source_fullhour_survey_year_by_island"][i] for i in OVERLAP]
    output["source_year_confounder_rank_correlation"]={
        "PRIBES_introduced_beetle_source_similarity_vs_source_survey_year":spearman(xs,years),
        "BALA_forest_beetle_homogenization_vs_PRIBES_source_survey_year":spearman(ys,years)
    }
    output["status"]="SOURCE_OBSERVED_SIX_ISLAND_ASSOCIATION_SCORED_NOT_CAUSAL"
    output["primary_specific_intro_source_signal_exploratory"]=bool(
        primary["spearman_rho"]>0
        and primary["one_sided_positive_association_permutation_p"]<0.05
        and native is not None
        and native["spearman_rho"]<primary["spearman_rho"])
    return output

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("--contract","--onehour-contract","--older-event-contract","--original-event-receipt"):
        p.add_argument(key,type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    study=json.loads(args.contract.read_text(encoding="utf-8"))
    onehour=json.loads(args.onehour_contract.read_text(encoding="utf-8"))
    older=json.loads(args.older_event_contract.read_text(encoding="utf-8"))
    receipt=json.loads(args.original_event_receipt.read_text(encoding="utf-8"))
    if (study.get("schema")!="structural.pribes_ruderal_source_vs_forest_homogenization.v1_323"
        or study.get("status")!="FROZEN_AFTER_SOURCE_EVENT_ONLY_72_SITES_BEFORE_FIRST_PRIBES_TAXON_ROW_ACCESS"
        or study["previous_original_source_event_conditions"]["PRIBES_v1_3_archive_SHA256"]!=SHA
        or receipt["source_v322_artifact_inner_JSON_sha256"]!=ORIGINAL_RECEIPT_SHA
        or study["frozen_BALA_island_forest_response"]["original_v318_source_JSON_sha256"]!=OLD_BALA_V318_SHA
        or receipt["source_original_event_rows_inspected"]!=80):
        raise ValueError("BALA and PRIBES six-island cross-source source-locked protocol not frozen")
    result={
       "schema":"structural.pribes_ruderal_external_beetle_source_result.v1_323",
       "status":"SOURCE_OR_ORIGINAL_TAXON_READER_TECHNICAL_STOP",
       "source_original_Occurrence_rows_opened_once":0,
       "original_BALA_source_Event_and_Occurrence_rows_REOPENED":0,
       "source_original_full_80_Event_effort_gate_v1_321_TERMINAL":True,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-PRIBES-Beetle-RuderalSource-v1.323-OneShot"})
        with urllib.request.urlopen(req,timeout=65) as f:blob=f.read(MAX_SOURCE+1)
        if len(blob)>MAX_SOURCE or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original PRIBES v1.3 source ZIP SHA changed")
        events=event_source_only(blob)
        source_frame(events,onehour,older,receipt)
        original=occurrence_source_only_for_first_scoring(blob)
        result["source_original_Occurrence_rows_opened_once"]=len(original)
        result=score_original(events,original,study,onehour,older,receipt)
    except Exception as exc:
        result["stop_type"]=type(exc).__name__;result["stop_reason"]=str(exc)[:330]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":result["status"],
      "original_occurrence_rows_read":result.get("source_original_Occurrence_rows_opened_once"),
      "six_source_sites":result.get("source_onehour_physical_sites"),
      "unknown_origin_fraction":result.get("source_unclassified_rank_named_origin_fraction"),
      "primary":result.get("primary_introduced_beetle_source_similarity_vs_forest_homogenization"),
      "source_site_n_intro_beetle":{i:d["introduced_beetle_source"]["sites_with_nonempty_recognized_source_taxon_set"]
                                  for i,d in result.get("per_island",{}).items()},
      "stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="SOURCE_OR_ORIGINAL_TAXON_READER_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":
    main()
