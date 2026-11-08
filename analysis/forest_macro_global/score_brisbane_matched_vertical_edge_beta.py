#!/usr/bin/env python3
"""Original Brisbane 10 sites x 3 edges paired canopy-vs-ground beetle beta.

The one prespecified contrast: V(site, edge 1m) - V(site, interior 256m),
where V is relative-individual-count Bray-Curtis between ground and canopy
flight-intercept traps sharing the same ORIGINAL site and edge distance.

Original Stone et al. 2018 source has 10 sites nested within ~5 forest
remnants, ONE Brisbane region; these 10 are not independent forests. All
246 source morphospecies columns had taxon records from >=2 trap locations
(source prior filtering). The source edge traps are horizontally displaced.
This is a secondary exploratory question, not a new field experiment or
a thermal migration effect. Does not export raw source species/site codes.
"""
from __future__ import annotations

import argparse,hashlib,itertools,json,math,random,re,statistics,xml.etree.ElementTree as ET,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from audit_brisbane_canopy_ground_original_xlsx import (
    SOURCE_MD5,SOURCE_DOI,OOXML,content_types,shared_text,celltext,colindex
)

SELECTED_EDGES=(1,16,256)
GROUND_EDGES=(1,4,16,64,256)
SAMPLE_COUNT=80
ORIGINAL_SITES=10
SOURCE_SPECIES_COLS=246

def original_rows(workbook):
    fp=Path(workbook)
    if not fp.is_file() or hashlib.md5(fp.read_bytes()).hexdigest()!=SOURCE_MD5:
        raise ValueError("Brisbane_source_original_publisher_MD5_changed")
    with zipfile.ZipFile(fp) as z:
        paths=dict(content_types(z))
        if "Beetle data" not in paths:raise ValueError("Brisbane_source_beetle_data_sheet_missing")
        path=paths["Beetle data"]
        if z.getinfo(path).file_size>10_000_000:
            raise ValueError("Brisbane_original_taxon_sheet_unexpected_size")
        strings=shared_text(z)
        root=ET.fromstring(z.read(path))
        result=[]
        for node in root.findall(f".//{{{OOXML}}}sheetData/{{{OOXML}}}row"):
            row={}
            for cell in node.findall(f"{{{OOXML}}}c"):
                column=re.match(r"[A-Z]+",cell.get("r",""))
                if column is None:continue
                col=colindex(column.group())
                value=celltext(cell,strings).strip()
                if value:row[col]=value
            result.append(row)
    if len(result)!=81:raise ValueError("Brisbane_original_80_Trap_rows_not_found")
    return result

def parse_number(text,*,allow_blank_zero):
    s=str(text or "").strip()
    if not s:
        if allow_blank_zero:return 0
        raise ValueError("original_source_taxon_cell_blank_unknown_not_zero")
    try:value=float(s)
    except ValueError:raise ValueError("original_source_non_numeric_taxon_cell")
    if not math.isfinite(value) or value<0 or not value.is_integer():
        raise ValueError("original_source_taxon_cells_nonnegative_integer_required")
    return int(value)

def bray_relative(a,b):
    a_sum=sum(a);b_sum=sum(b)
    if not a_sum or not b_sum:return None
    return 0.5*sum(abs(x/a_sum-y/b_sum) for x,y in zip(a,b))

def source_80_traps(rows, *, require_246_columns=True):
    if len(rows)!=81:raise ValueError("original_80_trap_source_row_count_drift")
    head=rows[0]
    headers=[head.get(i,"") for i in range(max(head)+1)]
    if headers[:5]!=["Obs","Abundance","Richness","Edge.dist","Height"]:
        raise ValueError("Brisbane_original_5_metadata_fields_changed")
    taxon_labels=headers[5:]
    if (require_246_columns and len(taxon_labels)!=SOURCE_SPECIES_COLS) or len(taxon_labels)<20:
        raise ValueError("Brisbane_source_species_column_count_drift")
    if any(not x for x in taxon_labels) or len(taxon_labels)!=len(set(taxon_labels)):
        raise ValueError("Brisbane_source_duplicate_or_blank_morphospecies_labels")
    strata={}
    original_codes=set()
    by_site=defaultdict(set)
    technical=Counter()
    per_site=defaultdict(dict)
    all_taxon_individuals=0
    original_meta_individuals=0
    original_meta_richness=0
    for raw in rows[1:]:
        code=raw.get(0,"")
        match=re.fullmatch(r"([A-Za-z]+)([0-9]+)([A-Za-z]+)([0-9]+)([A-Za-z]+)",code)
        if not match:raise ValueError("Brisbane_publisher_source_Obs_ID_cannot_parse")
        prefix,site_number,layer_token,original_edge,suffix=match.groups()
        if layer_token not in ("G","C"):
            raise ValueError("Brisbane_unknown_source_vertical_layer_token")
        layer={"G":"Ground","C":"Canopy"}[layer_token]
        if raw.get(4)!=layer:
            raise ValueError("Brisbane_original_Obs_layer_conflicts_with_Height")
        try:edge=int(float(raw.get(3,"nan")))
        except ValueError:raise ValueError("Brisbane_invalid_source_Edge_dist")
        if edge!=int(original_edge) or edge not in GROUND_EDGES:
            raise ValueError("Brisbane_original_Obs_edge_conflicts_with_Edge_dist")
        if layer=="Canopy" and edge not in SELECTED_EDGES:
            raise ValueError("Brisbane_unexpected_canopy_sample_edge_distance")
        site=(prefix,site_number)
        id_key=(site,layer,edge)
        if code in original_codes or id_key in strata:
            raise ValueError("Brisbane_duplicate_original_Obs_or_site_stratum_edge")
        original_codes.add(code)
        # Source has 246 numeric selected morphospecies columns per sampled
        # trap, including explicit zeros: blanks are NOT assumed zero.
        counts=[parse_number(raw.get(i,""),allow_blank_zero=False)
                for i in range(5,len(headers))]
        meta_abundance=parse_number(raw.get(1,""),allow_blank_zero=False)
        meta_richness=parse_number(raw.get(2,""),allow_blank_zero=False)
        selected_abundance=sum(counts)
        selected_richness=sum(n>0 for n in counts)
        technical["source_abundance_metadata_differs_selected_taxa"]+=int(
            selected_abundance!=meta_abundance)
        technical["source_richness_metadata_differs_selected_taxa"]+=int(
            selected_richness!=meta_richness)
        technical["source_nonzero_selected_taxon_cells"]+=selected_richness
        technical["source_selected_species_abundance_total"]+=selected_abundance
        technical["source_original_meta_abundance_total"]+=meta_abundance
        technical["source_original_meta_richness_total"]+=meta_richness
        technical["traps_with_zero_selected_taxa"]+=int(selected_abundance==0)
        strata[id_key]=counts
        by_site[site].add((layer,edge))
        technical[f"source_{layer}_{edge}m_trap_rows"]+=1
    expected={(layer,edge) for layer,edges in
              (("Ground",GROUND_EDGES),("Canopy",SELECTED_EDGES))
              for edge in edges}
    if len(strata)!=80 or len(by_site)!=ORIGINAL_SITES or any(v!=expected for v in by_site.values()):
        raise ValueError("Brisbane_10x8_Original_trap_design_incomplete")
    # Caller must not turn source 'site' identifiers into independent forest IDs.
    return strata,technical,len(taxon_labels)

def exact_conditional_signflip(contrast):
    if not contrast:return None
    if len(contrast)>20:raise ValueError("site_signflips_too_large")
    measured=abs(statistics.mean(contrast))
    tot=1<<len(contrast)
    extreme=0
    for mask in range(tot):
        simulated=abs(sum(v if mask>>i&1 else -v for i,v in enumerate(contrast))/len(contrast))
        if simulated>=measured-1e-12:extreme+=1
    return extreme/tot

def analyze_rows(rows, *, expect_species_246=True, boot_reps=10000):
    strata,qa,taxa=source_80_traps(rows,require_246_columns=expect_species_246)
    sites=sorted({k[0] for k in strata})
    site_out=[]
    distances=defaultdict(list)
    eligible=[]
    for i,site in enumerate(sites):
        vals={}
        for edge in SELECTED_EDGES:
            ground=strata[(site,"Ground",edge)]
            canopy=strata[(site,"Canopy",edge)]
            beta=bray_relative(ground,canopy)
            vals[edge]=beta
            if beta is not None:distances[edge].append(beta)
        # No replacement of missing trap species by ecological true zeros.
        if all(vals[e] is not None for e in SELECTED_EDGES):
            eligible.append(vals[1]-vals[256])
        site_out.append({
            "anonymous_original_site":i+1,
            "edge1_relative_species_BrayCurtis":vals[1],
            "edge16_relative_species_BrayCurtis_DESCRIPTIVE":vals[16],
            "interior256_relative_species_BrayCurtis":vals[256],
            "primary_edge_minus_interior_BrayCurtis":(
                vals[1]-vals[256] if vals[1] is not None and vals[256] is not None else None),
            "complete_3dist_ground_canopy_site":all(vals[e] is not None for e in SELECTED_EDGES)
        })
    if len(eligible)<8:
        main={"status":"STOP_FEWER_THAN_8_ELIGIBLE_STUDY_SITES",
              "site_count":len(eligible),"primary_edge_minus_interior":None,
              "site_resampling_CI":None,"conditional_exact_site_signflip_p":None}
    else:
        mean=statistics.mean(eligible)
        rng=random.Random(20261108)
        boot=sorted(statistics.mean(eligible[rng.randrange(len(eligible))] for j in eligible)
                    for n in range(boot_reps))
        main={
            "status":"EXPLORATORY_MATCHED_SITE_EDGE_DIFFERENTIATION_ESTIMATE_COMPUTED",
            "source_sites_used":len(eligible),
            "primary_edge1minus_interor256_relative_BrayCurtis_mean":mean,
            "site_bootstrap_95CI":[boot[int(.025*(boot_reps-1))],
                                  boot[int(.975*(boot_reps-1))]],
            "conditional_2sided_exact_site_signflip_p_NOT_independent_forest_replicates":
                exact_conditional_signflip(eligible),
            "sites_edge_amplification_positive":sum(x>0 for x in eligible),
            "sites_edge_homogenization_negative":sum(x<0 for x in eligible),
            "sites_edge_interor_tied":sum(x==0 for x in eligible),
            "bootstrap_replicates":boot_reps
        }
    summary={
        "schema":"structural.Brisbane_2018_original_matched_vertical_beetle_edge_beta.v1",
        "original_publisher_source_MD5":SOURCE_MD5,
        "source_DOI":SOURCE_DOI,
        "source_original_wide_taxon_code_columns":taxa,
        "source_trap_records":len(strata),
        "source_ground_flight_traps":50,
        "source_canopy_flight_traps":30,
        "source_original_10_sampling_sites_one_region":len(sites),
        "source_original_5_remnant_forest_group_membership_NOT_VERIFIED":True,
        "source_full_30_site_by_edge_ground_canopy_pair_opportunities":len(sites)*3,
        "selected_species_morphospecies_recorded_at_two_or_more_traps_by_original_source":True,
        "source_technical_quality_counts":dict(qa),
        "original_Abundance_and_Richness_metadata_not_assumed_to_be_selected_taxa":True,
        "descriptive_vertical_brays_by_edge_m":{
            str(e):{"valid_pairs":len(distances[e]),
                    "mean_relative_abundance_BrayCurtis":(
                        statistics.mean(distances[e]) if distances[e] else None)}
             for e in SELECTED_EDGES
        },
        "within_source_site_primary_effect":main,
        "site_specific_pair_diagnostics_NO_SOURCE_ID":site_out,
        "main_endpoint_prespecified_before_scoring":True,
        "mid_16m_is_secondary_descriptive_only":True,
        "independent_global_forest_regions_in_this_new_source":1,
        "source_sites_not_independent_forest_or_study_regions":True,
        "canopy_ground_traps_not_exactly_same_horizontal_coordinate":True,
        "source_study_already_reported_vertical_and_edge_beetle_differentiation":True,
        "inference_conditional_on_study_10_sites_and_5_unverified_remnant_groups":True,
        "beetle_microclimate_and_movement_NOT_observed":True,
        "raw_original_morphospecies_names_Obs_siteIDs_NOT_exported":True,
        "no_eBird_used":True
    }
    return summary

def run(source,out):
    result=analyze_rows(original_rows(source))
    folder=Path(out);folder.mkdir(parents=True,exist_ok=True)
    (folder/"Brisbane_beetle_original_paired_canopy_ground_edge_beta.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.source,a.out)
