#!/usr/bin/env python3
"""BALA v1.314: original seven-island species-replacement decomposition.

ONE original 2024 published Occurrence read, only AFTER the original 29-site
4620-Event response-free selection checksum and protocol are authenticated.
No taxon-specific source outcomes were used to choose sites, methods, epochs,
names, thresholds or original sample counts. The 2026 BALA abundance/richness
stability findings are PRIOR ART, not a new Structural confirmation.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,statistics,urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter,defaultdict
from pathlib import Path
from bala_repeated_transect_event_only_v1_311 import (
    SRC,SHA,MAX_BYTES,original_event_rows,assign_phase,_trim,_norm
)
from bala_equal_original_event_samples_v1_313 import METHODS,ISLANDS,select as selected_receipt

EXPECTED_SELECTED_SHA="39db7c6db04e022b495e233506e9c9774d8e1cf9e2e1c35830bbe6aadce9d6ac"
EXPECTED_SITE_SHA="31a323a378f29e60ff656699081ccbbb47b546568f13f43e6472391adc8b7c72"
GUILDS=("araneae","coleoptera")
RANKS={"species","subspecies","morphospecies"}

def local(t):return t.rsplit("}",1)[-1]
def term(t):return t.rstrip("/").split("/")[-1].split("#")[-1]

def original_occurrence_rows(original):
    with zipfile.ZipFile(io.BytesIO(original)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        nodes=[n for n in root if local(n.tag)=="extension"
               and n.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(nodes)!=1:raise ValueError("BALA source must declare one original Occurrence table")
        node=nodes[0]
        cols={};coreidx=None;member=None
        for x in node.iter():
            typ=local(x.tag)
            if typ=="field" and "term" in x.attrib and "index" in x.attrib:
                cols[term(x.attrib["term"])]=int(x.attrib["index"])
            elif typ=="coreid" and "index" in x.attrib:coreidx=int(x.attrib["index"])
            elif typ=="location" and x.text:member=x.text.strip()
        required={"scientificName","taxonRank","order","establishmentMeans"}
        if coreidx is None or member is None or not required.issubset(cols):
            raise ValueError("Original Occurrence source roles differ from v1.310 schema")
        delim=node.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        if len(delim)!=1:raise ValueError("Original occurrence delimiter unsupported")
        skip=int(node.attrib.get("ignoreHeaderLines","0"))
        if not 0<=skip<=2:raise ValueError("Unexpected original Occurrence header count")
        out=[]
        with z.open(member) as source:
            with io.TextIOWrapper(source,encoding="utf-8-sig",newline="") as file:
                reader=csv.reader(file,delimiter=delim)
                for _ in range(skip):next(reader,None)
                for row in reader:
                    if not row or not any(row):continue
                    if max(coreidx,*(cols[k] for k in required))>=len(row):
                        raise ValueError("Original Occurrence row truncated")
                    record={k:row[ix] for k,ix in cols.items() if ix<len(row)}
                    record["__foreign_coreid"]=row[coreidx]
                    out.append(record)
        return out

def reconstruct_selected_original_event_design(events,contract,source_receipt):
    old=selected_receipt(events)
    if (old["status"]!="SOURCE_EQUAL_EFFORT_FROZEN_EVENT_ONLY_OCCURRENCE_SEALED"
        or old["all_three_period_original_sites"]!=29
        or old["original_all_three_site_key_SHA256"]!=EXPECTED_SITE_SHA
        or old["selected_original_Event_coreids_SHA256"]!=EXPECTED_SELECTED_SHA
        or old["selected_original_Event_row_count_all_3_campaigns"]!=4620
        or source_receipt["status"]!=old["status"]
        or source_receipt["selected_original_Event_coreids_SHA256"]!=EXPECTED_SELECTED_SHA
        or source_receipt["selected_original_Event_per_campaign"]!=old["selected_original_Event_per_campaign"]):
        raise ValueError("Original BALA biological sample eligible source-Event fingerprint changed")
    group=defaultdict(list)
    all_ids=set()
    for e in events:
        core=_trim(e.get("__original_coreid"))
        if not core or core in all_ids:raise ValueError("Original BALA Event key missing/duplicated")
        all_ids.add(core)
        year=_trim(e.get("year"))
        phase=assign_phase(int(year)) if year.isdigit() else None
        island=_norm(e.get("island"));site=_trim(e.get("locationID"))
        method=_trim(e.get("samplingProtocol"))
        if phase is not None and island in ISLANDS and site and method in METHODS:
            group[(island,site,method,phase)].append(core)
    sites_by_phase={}
    for p in ("B1","B2","B3"):
        sites_by_phase[p]={(isl,site) for isl,site,mode,phase in group if phase==p}
    same_sites=set.intersection(*(sites_by_phase[p] for p in ("B1","B2","B3")))
    selected={}
    for isl,site in sorted(same_sites):
        for method in METHODS:
            byperiod=[sorted(group[(isl,site,method,p)]) for p in ("B1","B2","B3")]
            if any(not rows for rows in byperiod):
                raise ValueError("Equal survey method opportunity absent on original site")
            k=min(map(len,byperiod))
            for phase,rows in zip(("B1","B2","B3"),byperiod):
                for core in rows[:k]:
                    if core in selected:raise ValueError("Original sample Event in more than one physical unit")
                    selected[core]=(isl,site,method,phase)
    digest=hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest()
    if digest!=EXPECTED_SELECTED_SHA or len(selected)!=4620:
        raise ValueError("Original Event selection changed before species label access")
    return selected,all_ids,same_sites

def site_beta(a,b):
    """Observational replacement versus net richness change; no true extinction inferred."""
    if not a or not b:
        return None
    shared=len(a&b);loss=len(a-b);gain=len(b-a)
    changed=loss+gain
    rich1=shared+loss;rich3=shared+gain
    sor=changed/(2*shared+changed) if 2*shared+changed else 0.
    denom=shared+min(loss,gain)
    sim=min(loss,gain)/denom if denom else 0.
    return {"B1_richness":rich1,"B3_richness":rich3,
            "shared_taxa":shared,"B1_only_taxa":loss,"B3_only_taxa":gain,
            "net_species_richness_change":rich3-rich1,
            "absolute_net_richness_change":abs(rich3-rich1),
            "gross_detections_changed":changed,
            "balanced_replacement_taxon_incidence":2*min(loss,gain),
            "balanced_replacement_share":2*min(loss,gain)/changed if changed else 0.,
            "sorensen_beta_total":sor,
            "simpson_beta_replacement":sim,
            "nestedness_related_component":sor-sim}

def _avg(rows,key):
    return statistics.fmean(x[key] for x in rows) if rows else None

def _summary_by_guild_and_method(sets,sites,method,guild,period1,period2):
    by_island={}
    total_valid=0
    for island in ISLANDS:
        records=[]
        eligible_site_count=sum(s[0]==island for s in sites)
        for pair in sorted(sites):
            if pair[0]!=island:continue
            a=sets.get((pair[0],pair[1],method,guild,period1),set())
            b=sets.get((pair[0],pair[1],method,guild,period2),set())
            d=site_beta(a,b)
            if d:records.append(d)
        by_island[island]={
            "original_three_phase_matched_transect_count":eligible_site_count,
            "taxon_detected_in_both_periods_transects":len(records),
            "mean_sorensen_beta":_avg(records,"sorensen_beta_total"),
            "mean_simpson_replacement_beta":_avg(records,"simpson_beta_replacement"),
            "mean_nestedness_related_component":_avg(records,"nestedness_related_component"),
            "mean_balanced_replacement_share_of_changed_species_records":_avg(records,"balanced_replacement_share"),
            "mean_absolute_net_richness_change":_avg(records,"absolute_net_richness_change"),
            "mean_signed_net_richness_change":_avg(records,"net_species_richness_change"),
            "mean_B1_or_earlier_richness":_avg(records,"B1_richness"),
            "mean_B3_or_later_richness":_avg(records,"B3_richness"),
            "sites_with_any_species_change":sum(x["gross_detections_changed"]>0 for x in records),
            "sites_with_replacement_but_at_most_one_net_richness_change":sum(
                 x["balanced_replacement_taxon_incidence"]>0 and
                 x["absolute_net_richness_change"]<=1 for x in records)
        }
        total_valid+=len(records)
    island_entries=[v for v in by_island.values() if v["taxon_detected_in_both_periods_transects"]>0]
    mean=lambda key:statistics.fmean(v[key] for v in island_entries) if island_entries else None
    return {"method":method,"guild":guild,
       "period_pair":period1+"_"+period2,
       "original_matched_source_transects":len(sites),
       "eligible_with_both_period_taxon_detections":total_valid,
       "islands_with_at_least_one_valid_site":len(island_entries),
       "island_equal_mean_sorensen_beta":mean("mean_sorensen_beta"),
       "island_equal_mean_simpson_replacement_beta":mean("mean_simpson_replacement_beta"),
       "island_equal_mean_nestedness_component":mean("mean_nestedness_related_component"),
       "island_equal_mean_balanced_replacement_share":mean("mean_balanced_replacement_share_of_changed_species_records"),
       "island_equal_mean_absolute_net_richness_change":mean("mean_absolute_net_richness_change"),
       "island_equal_mean_signed_net_richness_change":mean("mean_signed_net_richness_change"),
       "total_sites_with_species_replacement_but_nearly_stable_richness":sum(
            v["sites_with_replacement_but_at_most_one_net_richness_change"] for v in by_island.values()),
       "per_island":by_island}

def calculate(events,occurrences,contract,source_receipt):
    original_selected,all_ids,sites=reconstruct_selected_original_event_design(events,contract,source_receipt)
    if len(events)!=10379 or len(occurrences)!=63904:
        raise ValueError("Source original published Event/Occurrence row universe changed")
    allowed=set(contract["taxon_reader"]["allowed_source_taxonRank_exact"])
    guilds=set(GUILDS)
    mapped=0;selected_guild_total=0;accepted=0;excluded=Counter();origin_counts=Counter()
    # First classify each original source species by source island and guild
    # with strictly exact original author establishment category; never
    # infer missing origin from island, guild, synonym or current ecology.
    origin_contract=contract["taxon_reader"]["biogeographic_origin"]
    origin_vocabulary={}
    for key in ("endemic","native","introduced"):
        for value in origin_contract[key+"_exact_normalized"]:
            if _norm(value) in origin_vocabulary:
                raise ValueError("Frozen original biogeographic origin ontology overlaps")
            origin_vocabulary[_norm(value)]=key
    raw=[];taxon_origin=defaultdict(set)
    for o in occurrences:
        core=_trim(o.get("__foreign_coreid"))
        if core in all_ids:mapped+=1
        else:
            excluded["original_foreign_Event_not_found"]+=1
            continue
        if core not in original_selected:continue
        isl,site,method,phase=original_selected[core]
        order=_norm(o.get("order"))
        if order not in guilds:continue
        selected_guild_total+=1
        name=_norm(o.get("scientificName"))
        rank=_norm(o.get("taxonRank"))
        origin=_norm(o.get("establishmentMeans"))
        if not name or rank not in allowed:
            excluded["source_higher_rank_or_empty_name"]+=1
            continue
        accepted+=1
        category=origin_vocabulary.get(origin,"unknown")
        origin_counts[category]+=1
        taxon_origin[(isl,order,name)].add(category)
        raw.append((isl,site,method,phase,order,name))
    match_fraction=mapped/len(occurrences)
    if match_fraction<contract["estimability"]["original_Event_to_Occurrence_join_fraction_min"]:
        return {"status":"STOP_ORIGINAL_EVENT_OCCURRENCE_JOIN_QUALITY",
                "original_coreid_join_fraction":match_fraction,
                "original_Occurrence_rows_opened":len(occurrences)}
    detected=defaultdict(set)
    origin_taxa=defaultdict(set)
    for isl,site,method,phase,order,name in raw:
        detected[(isl,site,method,order,phase)].add(name)
        status=taxon_origin[(isl,order,name)]
        if len(status)==1 and "unknown" not in status:
            origin_taxa[(isl,site,method,order,phase,next(iter(status)))].add(name)
    quality_fraction=(sum(v for k,v in origin_counts.items() if k!="unknown")/
                      accepted if accepted else 0.)
    primary=[]
    for method in METHODS:
        for guild in GUILDS:
            main=_summary_by_guild_and_method(detected,sites,method,guild,"B1","B3")
            admitted=(main["eligible_with_both_period_taxon_detections"]>=
                      contract["estimability"]["pitfall_primary_guild_source_site_min_count_each"]
                      and main["islands_with_at_least_one_valid_site"]>=
                      contract["estimability"]["pitfall_primary_island_min_count_each"])
            main["design_estimability_met"]=admitted
            main["scientific_category"]=(
                "QUALIFIED_OBSERVATIONAL_COMMUNITY_REPLACEMENT"
                if admitted else "STOP_WITHIN_GUILD_INSUFFICIENT_TAXON_DETECTION_SUPPORT")
            if not admitted:
                for key in ("island_equal_mean_sorensen_beta",
                  "island_equal_mean_simpson_replacement_beta",
                  "island_equal_mean_balanced_replacement_share",
                  "island_equal_mean_absolute_net_richness_change",
                  "island_equal_mean_signed_net_richness_change"):
                    main[key]=None
            primary.append(main)
    secondary_origin=[]
    if quality_fraction>=origin_contract["secondary_if_classified_rows_fraction_min"]:
        for status in ("endemic","native","introduced"):
            for guild in GUILDS:
                # Original PITFALL as the origin-stratified descriptive
                # secondary; source unknown statuses never relabelled.
                source_sets=defaultdict(set)
                for key,names in origin_taxa.items():
                    isl,site,method,order,phase,s=key
                    if s==status:
                        source_sets[(isl,site,method,order,phase)].update(names)
                v=_summary_by_guild_and_method(source_sets,sites,"Pitfall solution",guild,"B1","B3")
                v["original_source_origin"]=status
                secondary_origin.append(v)
    B1_B2=[];B2_B3=[]
    for method in METHODS:
        for guild in GUILDS:
            B1_B2.append(_summary_by_guild_and_method(detected,sites,method,guild,"B1","B2"))
            B2_B3.append(_summary_by_guild_and_method(detected,sites,method,guild,"B2","B3"))
    eligible_primary=sum(x["design_estimability_met"] for x in primary if x["method"]=="Pitfall solution")
    status=("OBSERVED_SEVEN_ISLAND_TEMPORAL_COMMUNITY_REPLACEMENT_SCORED"
             if eligible_primary==2 else
             "STOP_FROZEN_PITFALL_TWO_GUILD_ESTIMABILITY_INSUFFICIENT")
    return {"schema":"structural.bala_three_decade_arthropod_composition_result.v1_314",
       "status":status,"original_2024_source_archive_sha256":SHA,
       "original_Event_rows_examined":len(events),
       "original_Occurrence_rows_opened":len(occurrences),
       "original_Occurrence_Event_join_fraction":match_fraction,
       "exact_source_29_longitudinal_site_count":len(sites),
       "original_equal_Event_selected_total":len(original_selected),
       "original_equal_Event_selected_sha256":EXPECTED_SELECTED_SHA,
       "original_selected_guild_Occurrence_record_n":selected_guild_total,
       "species_rank_or_morphospecies_accepted_record_n":accepted,
       "excluded_record_reason_counts":dict(sorted(excluded.items())),
       "original_species_rank_origin_mapped_fraction":quality_fraction,
       "origin_status_source_counts":dict(sorted(origin_counts.items())),
       "source_Araneae_Coleoptera_original_taxa_total":{
          guild:len({name for isl,site,m,ph,g,name in raw if g==guild}) for guild in GUILDS},
       "B1_B3_main_and_method_results":primary,
       "B1_B2_temporal_secondary":B1_B2,
       "B2_B3_temporal_secondary":B2_B3,
       "B1_B3_original_origin_strata_secondary":secondary_origin,
       "source_original_3_period_event_samples_equal":True,
       "old_v1_311_English_island_code_gate_TERMINAL":True,
       "not_true_local_extinction_colonization_or_demographic_rescue":True,
       "not_independent_validation_of_2026_prior_richness_stability_paper":True,
       "no_source_site_IDs_taxon_names_coordinates_or_original_rows_exported":True,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--source-event-receipt",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    cfg=json.loads(args.protocol.read_text())
    receipt=json.loads(args.source_event_receipt.read_text())
    if (cfg.get("schema")!="structural.bala_longitudinal_community_replacement_scoring.v1_314"
        or cfg["status"]!="FROZEN_BEFORE_FIRST_2024_BALA_OCCURRENCE_SOURCE_READ"
        or cfg["original_source"]["archive"]!=SRC
        or cfg["original_source"]["sha256"]!=SHA
        or cfg["original_source"]["selected_equal_Event_source_primaryID_SHA256"]!=EXPECTED_SELECTED_SHA):
        raise ValueError("BALA longitudinal original community composition estimator not frozen")
    result={"schema":"structural.bala_three_decade_arthropod_composition_result.v1_314",
        "status":"ORIGINAL_SOURCE_OR_TAXON_READER_TECHNICAL_STOP",
        "original_Occurrence_rows_opened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SRC,headers={
             "User-Agent":"Structural-BALA-SevenIsland-OriginalSpeciesReplacement-v1.314"})
        with urllib.request.urlopen(req,timeout=70) as f:blob=f.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original published BALA source fingerprint mismatch")
        ev=original_event_rows(blob)
        # Strict source physical method and chosen original coreids before
        # first taxonomic field row is opened at all.
        reconstruct_selected_original_event_design(ev,cfg,receipt)
        obs=original_occurrence_rows(blob)
        result["original_Occurrence_rows_opened"]=len(obs)
        result=calculate(ev,obs,cfg,receipt)
    except Exception as error:
        result["stop_type"]=type(error).__name__
        result["stop_reason"]=str(error)[:280]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":result["status"],
      "original_Occurrence_rows_opened":result.get("original_Occurrence_rows_opened"),
      "source_29_sites":result.get("exact_source_29_longitudinal_site_count"),
      "origin_mapped_fraction":result.get("original_species_rank_origin_mapped_fraction"),
      "primary_pitfall_guilds":[{
        "guild":r["guild"],"source_site_n":r["eligible_with_both_period_taxon_detections"],
        "islands":r["islands_with_at_least_one_valid_site"],
        "mean_simpson_replacement":r["island_equal_mean_simpson_replacement_beta"],
        "mean_total_sorensen":r["island_equal_mean_sorensen_beta"],
        "mean_balanced_share":r["island_equal_mean_balanced_replacement_share"],
        "mean_absolute_richness_difference":r["island_equal_mean_absolute_net_richness_change"]
       } for r in result.get("B1_B3_main_and_method_results",[]) if r["method"]=="Pitfall solution"],
      "stop_reason":result.get("stop_reason")},sort_keys=True))
    if result["status"]=="ORIGINAL_SOURCE_OR_TAXON_READER_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":main()
