#!/usr/bin/env python3
"""Author-frozen MOVECLIM 2013 native plot data versus S1 island-loss cases.

Only retrospective plot-level habitat associations. Historical extinction risk,
migration, rescue and recolonization are NEVER inferred from these records.
"""
import argparse,csv,hashlib,io,json,math,statistics,urllib.request,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from azores_MOVECLIM_2013_source_preflight_v1_277 import inspect_moveclim
from azores2016_s1_loss_presence_crosswalk_v1_268 import canonical_binomial,normalized_locality
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
from macaronesia_extirpation_source_profile_v1_263 import download_original

MURL="https://ipt.gbif.pt/ipt/archive.do?r=plants_plots_moveclim&v=1.6"
MSHA="612dad4edc1a5fb8e9fd057167320144d8a7791a02d1245513d58fd6c8cdabc4"
SURL="https://digital.csic.es/bitstream/10261/377677/5/Extinct_species_biogeographical_variables_%26_biological_traits_Macaronesian_flora.xlsx"
SSHA="767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1"
ISLANDS={"Flores","Pico","São Miguel","Terceira"}
NATIVE={"nat","native","indigenous","end","endemic","azorean endemic",
        "azores endemic","endemic to azores","native non endemic","native non-endemic"}

def _norm(x):
    return " ".join(str(x or "").casefold().split())

def _mean(x):
    return sum(x)/len(x) if x else None

def _median(x):
    return statistics.median(x) if x else None

def audit_plot_frame(events,occurrences,losses,expected_plots=58,expected_events=232,
                     min_reference_species=5,min_affected_species=2):
    if len(events)!=expected_events:raise ValueError("Original Event count differs; cannot invent surveyed zeros")
    id_to_plot={}; plots=defaultdict(list)
    for e in events:
        k=str(e.get("coreid","")).strip()
        if not k or k in id_to_plot:raise ValueError("Duplicate/missing original Event coreid")
        island=normalized_locality(e.get("island"))
        if island is None or (expected_plots==58 and island not in ISLANDS):
            raise ValueError("Original Event island not in frozen four-island universe")
        if str(e.get("year","")).strip()!="2013" or not str(e.get("eventDate","")).startswith("2013"):
            raise ValueError("Source Event year differs from prospectively frozen 2013")
        loc=str(e.get("locationID","")).strip()
        if not loc:raise ValueError("Original author plot locationID missing; cannot infer location")
        try:elev=float(e.get("minimumElevationInMeters"))
        except (TypeError,ValueError):raise ValueError("Original plot elevation missing or nonnumeric")
        if not math.isfinite(elev):raise ValueError("Original plot elevation nonfinite")
        site=(island,loc)
        plots[site].append(elev)
        id_to_plot[k]=site
    if len(plots)!=expected_plots:
        raise ValueError(f"Original locationID makes {len(plots)} plot keys not expected {expected_plots}; stop")
    for k,vals in plots.items():
        if len(vals)!=4:raise ValueError("Source author plot has other than four Event subplots")
        if max(vals)-min(vals)>30:raise ValueError("Author plot elevation mismatch >30m")
    plot_elevation={k:statistics.median(v) for k,v in plots.items()}
    rank={}
    for island in set(k[0] for k in plots):
        group={k:v for k,v in plot_elevation.items() if k[0]==island}
        for site,elev in group.items():
            less=sum(v<elev for v in group.values())
            ties=sum(v==elev for v in group.values())
            rank[site]=(less+(ties-1)/2)/(len(group)-1) if len(group)>1 else 0.5
    loss_pairs=set()
    for l in losses:
        if (_norm(l.get("Archipelago")) not in {"azores","açores"}
            or _norm(l.get("Category"))!="well-supported"
            or _norm(l.get("Extinction category"))!="extirpation (island level)"):
            continue
        species=canonical_binomial(l.get("Species"))
        island=normalized_locality(l.get("Island"))
        if species is None or island is None:
            raise ValueError("Strict S1 taxon or loss island cannot be identified")
        loss_pairs.add((species,island))
    affected={s for s,_ in loss_pairs}
    records=Counter();origin_vocab=Counter();quantity_vocab=Counter()
    positive=defaultdict(set);ori=defaultdict(set);seen_taxa=set();observed=set()
    nonnative_unknown=0
    for o in occurrences:
        ek=str(o.get("coreid","")).strip()
        if ek not in id_to_plot:raise ValueError("Occurrence coreid lacks matching original Event")
        site=id_to_plot[ek]
        origin=_norm(o.get("establishmentMeans"))
        origin_vocab[str(o.get("establishmentMeans") or "[MISSING]")]+=1
        quantity_vocab[str(o.get("organismQuantityType") or "[MISSING]")]+=1
        if _norm(o.get("taxonRank"))!="species":
            records["excluded_non_species_rank"]+=1;nonnative_unknown+=1;continue
        name=canonical_binomial(o.get("scientificName"))
        if name is None:
            records["excluded_unresolved_name"]+=1;nonnative_unknown+=1;continue
        try:cover=float(o.get("organismQuantity"))
        except (ValueError,TypeError):
            records["excluded_missing_or_invalid_OTV"]+=1;nonnative_unknown+=1;continue
        if not math.isfinite(cover) or not (1<=cover<=9):
            records["excluded_missing_or_invalid_OTV"]+=1;nonnative_unknown+=1;continue
        token=(site[0],name)
        seen_taxa.add(token)
        ori[token].add(origin in NATIVE)
        positive[token].add(site)
        observed.add((ek,name))
        if origin not in NATIVE:nonnative_unknown+=1
    native={t:sites for t,sites in positive.items() if ori[t]=={True}}
    island_summaries={}
    same_loss={(species,island) for species,island in loss_pairs if (island,species) in seen_taxa}
    for island in sorted({k[0] for k in plots}):
        aff=[];ref=[];plots_affected=0
        for (isl,species),recorded in native.items():
            if isl!=island:continue
            item=_mean([rank[p] for p in recorded])
            if species in affected:aff.append(item);plots_affected+=len(recorded)
            else:ref.append(item)
        ok=(len(aff)>=min_affected_species and len(ref)>=min_reference_species)
        local_elev=[el for site,el in plot_elevation.items() if site[0]==island]
        island_summaries[island]={
           "sampled_10x10m_plots":len(local_elev),
           "sampled_5x5m_subplots":sum(site[0]==island for site in id_to_plot.values()),
           "native_species_positive_plots":sum(len(sites) for (isl,_),sites in native.items() if isl==island),
           "S1_loss_affected_native_species_positive_plots":plots_affected,
           "affected_native_taxa":len(aff),"reference_native_taxa":len(ref),
           "S1_affected_taxa_detected_any_status":sum(1 for isl,s in seen_taxa if isl==island and s in affected),
           "historically_lost_same_island_taxa_recorded_2013":sum(isl==island for _,isl in same_loss),
           "min_plot_elevation_m":min(local_elev),"max_plot_elevation_m":max(local_elev),
           "mean_plot_elevation_m":_mean(local_elev),
           "comparison_estimable":ok,
           "affected_mean_elevation_percentile":_mean(aff) if ok else None,
           "reference_mean_elevation_percentile":_mean(ref) if ok else None,
           "affected_median_elevation_percentile":_median(aff) if ok else None,
           "reference_median_elevation_percentile":_median(ref) if ok else None,
           "elevation_percentile_difference_affected_minus_reference":_mean(aff)-_mean(ref) if ok else None,
           "no_elevation_contrast_if_ineligible":not ok}
    raw_native_positives=sum(len(x) for x in native.values())
    return {
       "physical":{
         "event_subplots":len(events),"distinct_permanent_plots":len(plots),
         "plots_by_island":dict(sorted(Counter(s[0] for s in plots).items()))},
       "incidence":{
         "occurrence_source_rows":len(occurrences),
         "distinct_positive_subplot_taxon_records":len(observed),
         "species_island_positive_pairs":len(seen_taxa),
         "eligible_native_plot_taxon_positives":raw_native_positives,
         "nonnative_or_unknown_plot_taxon_records":nonnative_unknown,
         "exclusions":dict(records),
         "author_establishmentMeans_values":dict(sorted(origin_vocab.items())),
         "author_organismQuantityType_values":dict(sorted(quantity_vocab.items()))},
       "historical":{
         "distinct_S1_loss_taxa":len(affected),"S1_strict_taxon_island_cases":len(loss_pairs),
         "S1_loss_taxa_detected_in_2013":len({s for i,s in seen_taxa if s in affected}),
         "S1_loss_taxa_not_seen_in_2013":len(affected-{s for i,s in seen_taxa}),
         "historically_lost_taxon_island_pairs_with_2013_positive_plot":len(same_loss),
         "S1_loss_affected_native_taxa_found_in_2013":len({s for i,s in native if s in affected}),
         "plot_or_taxon_identity_names_exported":False},
       "by_island":island_summaries,
       "sampling_warning":{
         "not_independent_subplots":True,
         "plot_local_nondetection_not_island_absence":True,
         "not_historical_extinction_risk":True,
         "not_pre_loss_donor_viability":True,
         "comparison_constrained_to_intact_vegetation_gradient":True,
         "within_single_archipelago_not_cross_archipelago_replication":True,
         "native_recorded_group_requires_exact_author_origin_label":True,
         "not_population_recolonization_or_rescue":True}}

def original_event_occurrence_records(archive):
    schema=inspect_moveclim(archive)
    ev=schema["core"]
    ex=next(x for x in schema["extensions"] if x["rowtype"].endswith("/Occurrence"))
    def term_map(table):
        return {str(field["term"]).split("/")[-1]:int(field["index"])
                for field in table["fields"] if field.get("term") and field.get("index") is not None}
    def parse(z,table,needed):
        index=term_map(table)
        if not set(needed)<=set(index):
            raise ValueError("Author source missing frozen Event/Occurrence columns: "+str(sorted(set(needed)-set(index))))
        if table["encoding"].casefold() not in {"utf-8","utf8"}:
            raise ValueError("Original source archive not UTF-8")
        with z.open(table["record_path"]) as stream:
            with io.TextIOWrapper(stream,encoding="utf-8-sig",newline="") as f:
                reader=csv.reader(f,delimiter="\t")
                for _ in range(int(table["ignore_header_lines"] or 0)):next(reader,None)
                for line in reader:
                    if not line or not any(line):continue
                    if any(index[k]>=len(line) for k in needed):
                        raise ValueError("Original source has malformed short data row")
                    rec={k:line[index[k]] for k in needed}
                    rec["coreid"]=line[0]
                    yield rec
    efields=("eventID","eventDate","year","island","locationID","minimumElevationInMeters")
    ofields=("scientificName","taxonRank","establishmentMeans",
             "organismQuantity","organismQuantityType")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        return list(parse(z,ev,efields)),list(parse(z,ex,ofields))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    c=json.loads(args.contract.read_text())
    if (c.get("schema")!="structural.moveclim2013_S1_native_forest_refugia_design.v1_278"
        or c.get("status")!="FROZEN_BEFORE_2013_MOVECLIM_EVENT_AND_OCCURRENCE_VALUE_ACCESS"):
        raise ValueError("Unfrozen source design")
    m,s=c["sources"]["MOVECLIM"],c["sources"]["S1"]
    if (m["original_url"]!=MURL or m["sha256"]!=MSHA or
        s["url"]!=SURL or s["sha256"]!=SSHA):
        raise ValueError("Original source identities differ from frozen publication")
    result={"schema":"structural.moveclim2013_native_refugia_result.v1_278",
            "status":"SOURCE_STOP_NO_BIOLOGICAL_INFERENCE",
            "source_2013_SHA256":MSHA,"source_CSIC_SHA256":SSHA,
            "original_S2_S3_S4_values_opened":0,
            "original_mammal_BioTIME_RLS_holdout_rows_opened":0,
            "new_confirmatory_systems_admitted":0,
            "GEB_scientific_HOLD":True,"eBird_used":False}
    try:
        req=urllib.request.Request(MURL,headers={
            "User-Agent":"Structural-Azores-island-native-habitat-survey/1.0"})
        with urllib.request.urlopen(req,timeout=60) as r:move=r.read(15_000_001)
        if len(move)!=111299 or hashlib.sha256(move).hexdigest()!=MSHA:
            raise ValueError("Publisher exact MOVECLIM source changed")
        csic=download_original(SURL,332776,5_000_000)
        if hashlib.sha256(csic).hexdigest()!=SSHA:
            raise ValueError("Publisher S1 local loss source changed")
        ev,obs=original_event_occurrence_records(move)
        if len(ev)!=232 or len(obs)!=2539:
            raise ValueError("Original Event/Occurrence denominator mismatch")
        cases=parse_sheet_s1(csic)
        audit=audit_plot_frame(ev,obs,cases)
        if (audit["historical"]["distinct_S1_loss_taxa"]!=20 or
            audit["historical"]["S1_strict_taxon_island_cases"]!=24):
            raise ValueError("Original 20/24 Azores S1 source universe mismatched")
        result["status"]="AUTHOR_2013_NATIVE_FOREST_PLOT_DESCRIPTIVE_RESULT"
        result["original_2013_events"]=len(ev)
        result["original_2013_occurrences"]=len(obs)
        result["audit"]=audit
        result["sampling_warning"]=audit["sampling_warning"]
    except Exception as e:
        result["stop_type"]=type(e).__name__
        result["stop_reason"]=str(e)[:500]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],"events":result.get("original_2013_events"),
        "plots":result.get("audit",{}).get("physical",{}).get("distinct_permanent_plots"),
        "loss_taxa_field_detected":result.get("audit",{}).get("historical",{}).get("S1_loss_taxa_detected_in_2013"),
        "stop_reason":result.get("stop_reason")},sort_keys=True))
    if result["status"]!="AUTHOR_2013_NATIVE_FOREST_PLOT_DESCRIPTIVE_RESULT":
        raise SystemExit(2)

if __name__=="__main__":
    main()
