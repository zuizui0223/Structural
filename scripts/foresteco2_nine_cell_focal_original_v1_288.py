#!/usr/bin/env python3
"""ForestEco2 v1.288: independent published-source plant composition score.

This is a separate retrospective outcome-sealed-at-design-time study with
Event-exposed 9/11/10 cells. The original v1.286 10/10/10 gate remains terminal.
Never claim causal preservation, immigration, survival or pristine confirmation.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,random,urllib.request,xml.etree.ElementTree as ET,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from foresteco2_event_only_qualification_v1_286 import (
    SOURCE,SOURCE_SHA,_read_author_event_only,_norm,_local,_term
)
from azores_MOVECLIM_introduced_pressure_v1_281 import _loss_taxa
from azores2016_s1_loss_presence_crosswalk_v1_268 import canonical_binomial,normalized_locality
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
from macaronesia_extirpation_source_profile_v1_263 import download_original

S1_SHA="767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1"
S1_URL="https://digital.csic.es/bitstream/10261/377677/5/Extinct_species_biogeographical_variables_%26_biological_traits_Macaronesian_flora.xlsx"
GROUPS=("Pico","São Miguel","Terceira")
HABITATS=("NF","EW","PF")

def original_occurrence_rows(archive):
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        occs=[e for e in root if _local(e.tag)=="extension"
              and e.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(occs)!=1:raise ValueError("Original one Occurrence role not established")
        ext=occs[0];cols={};path=None;id_col=None
        for node in ext.iter():
            tag=_local(node.tag)
            if tag=="field" and "term" in node.attrib and "index" in node.attrib:
                cols[_term(node.attrib["term"])]=int(node.attrib["index"])
            elif tag=="coreid":id_col=int(node.attrib["index"])
            elif tag=="location" and node.text:path=node.text.strip()
        required={"scientificName","taxonRank","establishmentMeans"}
        if not required.issubset(cols) or id_col is None or not path:
            raise ValueError("Source occurrence role/schema differs from frozen v1.285")
        delimiter=ext.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        if len(delimiter)!=1:raise ValueError("Unrecognized Occurrence delimiter")
        nignore=int(ext.attrib.get("ignoreHeaderLines","0"))
        if nignore<0 or nignore>2:raise ValueError("Unexpected original Occurrence header count")
        with z.open(path) as stream:
            with io.TextIOWrapper(stream,encoding="utf-8-sig",newline="") as f:
                rdr=csv.reader(f,delimiter=delimiter)
                for _ in range(nignore): next(rdr,None)
                result=[]
                for values in rdr:
                    if not values or not any(values):continue
                    if id_col>=len(values) or any(cols[n]>=len(values) for n in required):
                        raise ValueError("Invalid source Occurrence field width")
                    item={k:values[v] for k,v in cols.items() if v<len(values)}
                    item["coreid"]=values[id_col]
                    result.append(item)
                return result

def quantile(sorted_values,p):
    if not sorted_values:raise ValueError("Empty bootstrap")
    pos=(len(sorted_values)-1)*p
    low=int(pos);high=min(len(sorted_values)-1,low+1)
    return sorted_values[low]+(sorted_values[high]-sorted_values[low])*(pos-low)

def statistic(grouped):
    d={}
    totals={}
    for island in GROUPS:
        logit={}
        totals[island]={}
        for habitat in HABITATS:
            plots=grouped[(island,habitat)]
            f=sum(z[0] for z in plots);r=sum(z[1] for z in plots)
            logit[habitat]=math.log((f+0.5)/(r+0.5))
            totals[island][habitat]={"focal_native_plot_taxon_positive_cells":f,
                 "other_native_plot_taxon_positive_cells":r,
                 "introduced_plot_taxon_positive_cells":sum(z[2] for z in plots),
                 "original_plot_count":len(plots)}
        d[island]=logit["NF"]-(logit["EW"]+logit["PF"])/2
    return sum(d.values())/len(GROUPS),d,totals

def score_original(events,observations,loss_rows,protocol):
    if len(events)!=90 or len(observations)!=1150:
        raise ValueError("Original forest sample/plant response row totals fail")
    focal,loss_pairs=_loss_taxa(loss_rows)
    if len(focal)!=20 or len(loss_pairs)!=24:
        raise ValueError("Original external 20/24 historical species frame differs")
    type_by_original={"natural forest":"NF","exotic woodland":"EW","production forest":"PF"}
    island_names={"pico":"Pico","são miguel":"São Miguel","sao miguel":"São Miguel","terceira":"Terceira"}
    core_to_group={};loc_seen=set()
    site_to_core={}
    for e in events:
        id_=str(e.get("source_coreid","")).strip()
        loc=str(e.get("locationID","")).strip()
        island=island_names.get(_norm(e.get("island")))
        habitat=type_by_original.get(_norm(e.get("habitat")))
        if not id_ or not loc or not island or not habitat or id_ in core_to_group:
            raise ValueError("Nonfrozen Event join/forest code")
        if (island,loc) in loc_seen:
            raise ValueError("Duplicate original physical forest plot")
        loc_seen.add((island,loc))
        core_to_group[id_]=(island,habitat)
        site_to_core[id_]=id_
    original_n=Counter(core_to_group.values())
    if any(original_n[(island,h)]!=protocol["verified_response_independent_design"]["forest_type_counts_per_island"][h]
           for island in GROUPS for h in HABITATS):
        raise ValueError("Original response-free Event 9/11/10 frame changed")

    native=set(_norm(z) for z in protocol["classification"]["native_exact_normalized"])
    introduced=set(_norm(z) for z in protocol["classification"]["introduced_exact_normalized"])
    status=defaultdict(set)
    positive=set()
    exclude=Counter()
    species_ranks_eligible=0
    unknown_status_records=0
    for o in observations:
        key=str(o.get("coreid","")).strip()
        if key not in core_to_group:raise ValueError("Occurrence without original author Event join")
        if _norm(o.get("taxonRank"))!="species":
            exclude["non_species_rank"]+=1;continue
        name=canonical_binomial(o.get("scientificName"))
        if name is None:
            exclude["no_unique_canonical_binomial"]+=1;continue
        species_ranks_eligible+=1
        code=_norm(o.get("establishmentMeans"))
        if code in native:cls="native"
        elif code in introduced:cls="introduced"
        else:
            cls="unknown";unknown_status_records+=1
        status[(core_to_group[key][0],name)].add(cls)
        positive.add((key,name))
    if species_ranks_eligible==0:
        raise ValueError("No admissible species-rank rows")
    unknown_fraction=unknown_status_records/species_ranks_eligible
    if unknown_fraction>protocol["pilot_estimability_before_score"]["max_fraction_unclassified_original_Occurrence_rows"]:
        # Scientifically STOP rather than expanding allowed classes after seeing origin labels.
        return {"schema":"structural.foresteco2_nine_cell_original_result.v1_288",
                "status":"STOP_UNCLASSIFIED_ORIGIN_EXCEEDS_FROZEN_THRESHOLD",
                "original_occurrence_rows_opened":len(observations),
                "unknown_status_species_rank_fraction":unknown_fraction,
                "focal_prediction_scored":False,
                "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}

    focal_taxa=set();focal_islands=set();all_focal_cells=0
    grouped=defaultdict(list)
    by_core=defaultdict(lambda:[0,0,0])
    for core,name in sorted(positive):
        island,h=core_to_group[core]
        classes=status[(island,name)]
        if classes=={"native"}:
            if name in focal:
                by_core[core][0]+=1;focal_taxa.add(name);focal_islands.add(island);all_focal_cells+=1
            else:by_core[core][1]+=1
        elif classes=={"introduced"}:by_core[core][2]+=1
        else:exclude["mixed_or_unknown_species_status"]=exclude["mixed_or_unknown_species_status"]+1
    for core,g in core_to_group.items():
        grouped[g].append(tuple(by_core[core]))
    if any(len(grouped[(i,h)])!=protocol["verified_response_independent_design"]["forest_type_counts_per_island"][h]
           for i in GROUPS for h in HABITATS):
        raise ValueError("Forest groups changed after response access")

    D,d,summary=statistic(grouped)
    minimum=protocol["pilot_estimability_before_score"]
    reason=[]
    if len(focal_taxa)<minimum["min_distinct_focal_native_taxa_all"]:
        reason.append("insufficient_distinct_focal_native_taxa")
    if len(focal_islands)<minimum["min_islands_with_any_focal_native_taxon"]:
        reason.append("insufficient_focal_island_coverage")
    if all_focal_cells<minimum["min_total_focal_native_plot_taxon_positive_cells"]:
        reason.append("insufficient_focal_positive_plant_plot_cells")
    if any(summary[i][h]["other_native_plot_taxon_positive_cells"]<
           minimum["all_nine_cells_min_reference_native_plot_taxon_positives"]
           for i in GROUPS for h in HABITATS):
        reason.append("reference_native_stratum_missing")
    result={
        "schema":"structural.foresteco2_nine_cell_original_result.v1_288",
        "status":"STOP_FOCAL_ESTIMABILITY_AFTER_ONE_SHOT" if reason else "RETROSPECTIVE_INDEPENDENT_FOREST_SOURCE_DESCRIPTIVE_SCORE",
        "foresteco2_published_original_source_SHA256":protocol["source"]["archive_sha256"],
        "total_original_event_rows":len(events),
        "total_original_occurrence_rows":len(observations),
        "fixed_historical_loss_taxa":len(focal),
        "strict_historical_loss_taxon_island_pairs":len(loss_pairs),
        "focal_native_taxa_detected_count":len(focal_taxa),
        "focal_islands_detected_count":len(focal_islands),
        "focal_native_positive_plot_taxon_cells":all_focal_cells,
        "unknown_species_rank_status_fraction":unknown_fraction,
        "excluded_record_classes":dict(sorted(exclude.items())),
        "by_island_and_forest":summary,
        "pilot_estimability_reason":reason,
        "original_v1_286_gate_remains_terminal":True,
        "original_v1_287_9_11_10_cells_used":True,
        "new_confirmatory_systems":0,
        "GEB_scientific_HOLD":True,
        "eBird_used":False,
        "no_taxon_plot_island_label_pairs_or_raw_records_exported":True,
        "not_island_extinction_risk_or_causal_forest_intervention":True,
        "not_recolonization_rescue_or_viable_donor_inference":True,
    }
    if reason:
        result["focal_prediction_scored"]=False
        result["primary_D"]=None
        result["bootstrap_CI95"]=None
        return result

    B=2000;rng=random.Random(1729);sim=[]
    for _ in range(B):
        boot={}
        for k,plots in grouped.items():
            boot[k]=[plots[rng.randrange(len(plots))] for _ in range(len(plots))]
        sim.append(statistic(boot)[0])
    sim.sort()
    lo,hi=quantile(sim,.025),quantile(sim,.975)
    result["focal_prediction_scored"]=True
    result["primary_D"]=D
    result["three_island_contrasts"]=d
    result["bootstrap_CI95"]=[lo,hi]
    result["bootstrap_replicates"]=B
    result["bootstrap_seed"]=1729
    result["descriptive_positive_lower_bound_above_zero"]=D>0 and lo>0
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.foresteco2_unequal_design_focal_composition.v1_288"
        or c.get("status")!="FROZEN_AFTER_SOURCE_EVENT_ONLY_BEFORE_ANY_FORESTECO2_PLANT_OCCURRENCE_VALUES"
        or c["source"]["archive_sha256"]!=SOURCE_SHA
        or c["source"]["historical_S1_workbook_sha256"]!=S1_SHA):
        raise ValueError("Original plant frame and historical S1 contrast not frozen")
    result={"schema":"structural.foresteco2_nine_cell_original_result.v1_288",
            "status":"SOURCE_OR_BIOLOGICAL_ONE_SHOT_STOP",
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False,
            "original_occurrence_rows_opened":0,"focal_prediction_scored":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-ForestEco2-Original-90-NineCell-Focal-v1.288"})
        with urllib.request.urlopen(req,timeout=60) as remote:
            arc=remote.read(5_000_001)
        if len(arc)>5_000_000 or hashlib.sha256(arc).hexdigest()!=SOURCE_SHA:
            raise ValueError("ForestEco2 original snapshot changed")
        events=_read_author_event_only(arc)
        occ=original_occurrence_rows(arc)
        result["original_occurrence_rows_opened"]=len(occ)
        s1=download_original(S1_URL,332776,5_000_000)
        if hashlib.sha256(s1).hexdigest()!=S1_SHA:raise ValueError("S1 historical source changed")
        losses=parse_sheet_s1(s1)
        result=score_original(events,occ,losses,c)
    except Exception as error:
        result["stop_type"]=type(error).__name__
        result["stop_reason"]=str(error)[:400]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
       "original_occurrence_rows_opened":result.get("original_occurrence_rows_opened",result.get("total_original_occurrence_rows")),
       "focal_taxa_detected":result.get("focal_native_taxa_detected_count"),
       "focal_islands":result.get("focal_islands_detected_count"),
       "focal_cells":result.get("focal_native_positive_plot_taxon_cells"),
       "primary_D":result.get("primary_D"),
       "bootstrap_CI95":result.get("bootstrap_CI95"),
       "stop_reason":result.get("stop_reason")},sort_keys=True))
    # Terminal failures are legitimate STOP outcomes, not CI-successful ecology.
    if result["status"] not in ("RETROSPECTIVE_INDEPENDENT_FOREST_SOURCE_DESCRIPTIVE_SCORE",
                                "STOP_FOCAL_ESTIMABILITY_AFTER_ONE_SHOT",
                                "STOP_UNCLASSIFIED_ORIGIN_EXCEEDS_FROZEN_THRESHOLD"):
        raise SystemExit(2)

if __name__=="__main__":main()
