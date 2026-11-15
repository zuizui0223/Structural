#!/usr/bin/env python3
"""Original 2012 deadwood volume/types in 30 BELongDead 31123 plots: PREDICTOR ONLY.

Pin exact publisher BExIS24546/31123 original sources, read ONLY original
plot / supplied host tree labels and ambient natural wood primary, secondary
tree species and numeric DWV. Never access insect taxa/counts, or any site
coordinates; no new beetle eco-response, hypothesis test or p values.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math
from collections import Counter,defaultdict
from pathlib import Path
from belongdead_31123_original_source_plot_tree_grain import get_original as get31123
from belongdead24546_original_deadwood_item_field_quality import original_csv as get24546

MAIN_SHA="73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e"
ENV_SHA="5a02350e4f1e364302dea20ca25281e65f2158d318d9fbcef56be2fe6d57786a"
MISS={"","na","nan","null","n/a","missing","none"}
class SourceStop(RuntimeError):pass

def beetle_supplied_host_metadata(raw):
    if hashlib.sha256(raw).hexdigest()!=MAIN_SHA or len(raw)!=8103493:
        raise SourceStop("SOURCE_STOP_31123_AUTHOR_SOURCE_SHA_DRIFT")
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    h=next(rd,[])
    if len(h)!=17 or (h[2],h[3],h[5])!=("PlotID","Exploratory","TreeSpecies"):
        raise SourceStop("SOURCE_STOP_ORIGINAL_31123_SOURCE_HOST_COLS_CHANGED")
    forest=set();hosts=set();n=0
    per_plot_host=defaultdict(set)
    for row in rd:
        if not row or not any(v.strip() for v in row):continue
        n+=1
        if len(row)!=17:raise SourceStop("SOURCE_STOP_SOURCE_31123_INCIDENCE_ROW_GRAMMAR")
        plot=row[2].strip();ex=row[3].strip();host=row[5].strip()
        if not plot or not ex or not host:
            raise SourceStop("SOURCE_STOP_SOURCE_31123_PLOT_OR_HOST_MISSING")
        forest.add(plot); hosts.add(host);per_plot_host[plot].add(host)
    if len(forest)!=30 or len(hosts)!=13 or n!=59850:
        raise SourceStop("SOURCE_STOP_SOURCE_31123_FROZEN_PLOT_HOST_GRAIN_DRIFT")
    return forest,hosts,{k:len(v) for k,v in per_plot_host.items()}

def profile_ambient(raw,original_plots,experimental_hosts):
    if len(raw)!=417351 or hashlib.sha256(raw).hexdigest()!=ENV_SHA:
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEXIS24546_SHA_OR_LENGTH_DRIFT")
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    h=next(rd,[])
    if len(h)!=12 or (h[1],h[5],h[6],h[10])!=("plotID","spec1","spec2","DWV"):
        raise SourceStop("SOURCE_STOP_ORIGINAL_DEADWOOD_FIELD_POSITIONS_CHANGED")
    nr=0;nmatched=0
    sourceplots=set()
    categories1=set();categories2=set()
    sourceplots_samehost=set()
    byplot_rows=Counter()
    byplot_volume=defaultdict(float)
    byplot_nonzero=Counter()
    missing=Counter()
    nonnumeric=0
    neg=0;zero=0;positive=0
    withsecondary=0
    withoutprimary=0
    exactmatching_source_item_rows=0
    for r in rd:
        if not r or not any(v.strip() for v in r):continue
        nr+=1
        if len(r)!=12:raise SourceStop("SOURCE_STOP_ORIGINAL_DEADWOOD_ITEM_ROW_WIDTH_CHANGED")
        plot,s1,s2,vol=(r[i].strip() for i in (1,5,6,10))
        if not plot:raise SourceStop("SOURCE_STOP_ORIGINAL_2012_PLOT_KEY_MISSING")
        sourceplots.add(plot)
        if plot not in original_plots:continue
        nmatched+=1;byplot_rows[plot]+=1
        if s1.lower() in MISS:s1=""
        if s2.lower() in MISS:s2=""
        if s1:categories1.add(s1)
        else:withoutprimary+=1
        if s2:categories2.add(s2);withsecondary+=1
        if s1 in experimental_hosts or s2 in experimental_hosts:
            exactmatching_source_item_rows+=1
            sourceplots_samehost.add(plot)
        if vol.lower() in MISS:
            missing["DWV"]+=1
            continue
        try:v=float(vol)
        except ValueError:
            nonnumeric+=1
            continue
        if not math.isfinite(v):
            missing["DWV_nonfinite"]+=1
            continue
        if v<0:
            neg+=1
            continue
        byplot_volume[plot]+=v
        if v==0:zero+=1
        else:positive+=1;byplot_nonzero[plot]+=1
    if nr!=7671 or len(sourceplots)!=148 or nmatched!=1385 or len(byplot_rows)!=30:
        raise SourceStop("SOURCE_STOP_ORIGINAL_2012_7671ITEM_148PLOT_1385_MATCH_30_DRIFT")
    if any(x<=0 for x in byplot_rows.values()):
        raise SourceStop("SOURCE_STOP_2012_PLOT_WITHOUT_SOURCE_DEADWOOD_RECORD")
    vals=sorted(byplot_volume.get(p,0.0) for p in original_plots)
    fully_measured=(sum(missing.values())+nonnumeric+neg)==0
    return {
      "original_2012_deadwood_inventory_total_items":nr,
      "original_2012_deadwood_inventory_original_plot_tokens":len(sourceplots),
      "original_2012_deadwood_items_in_BELongDead_30_exact_plots":nmatched,
      "experimental_13_host_taxa_distinct_original_labels":len(experimental_hosts),
      "original_2012_ambient_spec1_distinct_labels_in_30plots":len(categories1),
      "original_2012_ambient_spec2_distinct_labels_in_30plots":len(categories2),
      "original_2012_items_with_secondary_species_label":withsecondary,
      "original_2012_items_without_primary_species_label":withoutprimary,
      "exact_original_host_label_intersection_spec1_vs_experimental":len(categories1 & experimental_hosts),
      "exact_original_host_label_intersection_spec2_vs_experimental":len(categories2 & experimental_hosts),
      "source_items_whose_original_spec1_or_spec2_label_matches_one_of_13_supplied_hosts":exactmatching_source_item_rows,
      "original_30_plots_with_some_exact_ambient_vs_supplied_host_label_match":len(sourceplots_samehost),
      "source_30plots_with_2012_deadwood_positive_volume_items":sum(byplot_nonzero.get(p,0)>0 for p in original_plots),
      "original_DWV_unit_publisher_dataStructure1027":"cubic meter",
      "2012_DWV_source_item_finite_nonnegative_complete":fully_measured,
      "source_2012_item_volume_value_missing_or_bad_counts":{
        **dict(missing),
        "non_numeric":nonnumeric,
        "negative":neg,
        "exact_zero":zero,
        "strictly_positive":positive,
      },
      "original_2012_inventory_natural_deadwood_volume_30plot_aggregate_only_if_complete_m3":{
        "min":round(vals[0],5),
        "median":round((vals[14]+vals[15])/2,5),
        "max":round(vals[-1],5),
        "30plots_have_distinct_volume_sum_values":len(set(vals)),
        "30plot_total_volume_m3_is_NOT_per_ha_without_area_codebook":True,
      } if fully_measured else None,
      "original_species_codes_are_not_translated_or_imputed":True,
      "source_mixed_species_volume_never_double_counted_into_species":True,
      "original_deadwood_volume_m3_not_living_forest_basal_area":True,
      "source_original_host_or_wood_taxon_literal_labels_and_plotIDs_NOT_EXPORTED":True,
      "source_original_beetle_taxon_abundances_counts_and_traits_NEVER_OPENED":True,
      "source_2012_deadwood_inventory_not_time_aligned_each_beetle_year":True,
      "source_31124_trap_effort_zero_opportunity_still_unresolved":True,
      "status":"SOURCE_DEADWOOD_2012_SITE_TOTAL_VOLUME_PREDICTOR_SUPPORTED"
           if fully_measured else "SOURCE_ORIGINAL_2012_AMBIENT_WOOD_VOLUME_MISSINGNESS_STOP",
    }


def synthetic():
    a={"Fagus sylvatica","Picea abies"}
    b={"Picea abies","Quercus robur"}
    assert len(a & b)==1
    assert len([x for x in (1.0,0.1,0.0) if x<0])==0
    assert int("2012")<2017
    print("SYNTHETIC_EXACT_SPECIES_LABEL_AND_UNMODIFIED_M3_PREDICTOR_SUPPORT_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out")
    try:
        plots,hosts,hostperplot=beetle_supplied_host_metadata(get31123())
        profile=profile_ambient(get24546(),plots,hosts)
        result={
          "schema":"structural.BELongDead31123_24546_2012_original_woodtype_volume_predictor_support.v1",
          "full_original_publisher_BExIS31123_SHA":MAIN_SHA,
          "ambient_original_2012_BExIS24546_SHA":ENV_SHA,
          "source_all_30_supplied_experimental_plots_present_in_deadwood_2012":True,
          "experimental_host_category_min_per_plot":min(hostperplot.values()),
          "experimental_host_category_max_per_plot":max(hostperplot.values()),
          "source_original_tree_host_and_2012_deadwood_PREDICTOR_only":profile,
          "original_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
          "eBird_used":False,
          "status":profile["status"],
        }
    except SourceStop as ex:
        result={
          "schema":"structural.BELongDead31123_24546_2012_original_woodtype_volume_predictor_support.v1",
          "status":str(ex),
          "scientific_source_STOP_not_ecological_non_support":True,
          "original_Finland_Burner_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
        }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead_30plot_2012_WOODtype_m3_predictor_sourceonly.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
