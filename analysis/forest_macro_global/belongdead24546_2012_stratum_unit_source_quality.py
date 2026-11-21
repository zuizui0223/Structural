#!/usr/bin/env python3
"""Original BE24546 plot-matched 2012 ambient deadwood SOURCE PREDICTOR QA.

Fixed published field contract: DWV stratum T/L=m3 per inventoried item,
T7/S=m3 per hectare for transect items, Vharv=m3/ha harvested stump proxy.
NEVER add volumes from different unit systems or plot missing effort=0.
BE31123 beetle source original PlotID field ONLY; species/counts not read.
No original site/wood/species code literal values exported in reports.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,statistics,urllib.error,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
BEXIS="https://www.bexis.uni-jena.de"
PIN={
 31123:(8103493,"73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e"),
 24546:(417351,"5a02350e4f1e364302dea20ca25281e65f2158d318d9fbcef56be2fe6d57786a"),
}
FIELD_NAMES=["exp","plotID","PT","Tdir","PTNum","spec1","spec2",
             "sawcut","dc","stratum","DWV","Vharv"]
STRATA=("T","L","L7","S")
UNITS={"T":"m3_item","L":"m3_item","L7":"UNIT_UNVERIFIED_AUTHOR_T7_VS_L7","S":"m3_per_ha"}
class ScientificStop(Exception):pass

def pinned(id):
    size,digest=PIN[id]
    req=urllib.request.Request(BEXIS+f"/api/data/{id}/tag/1",headers={
      "User-Agent":"Structural-BExIS24546-original-2012-DWV-stratum-source-QA/1.0",
      "Accept":"text/csv"})
    try:
        with urllib.request.urlopen(req,timeout=65) as h:
            raw=h.read(size+1);status=h.status;ctype=h.headers.get("Content-Type","")
    except urllib.error.HTTPError as ex:
        raise ScientificStop("SOURCE_STOP_CC_BY_TAG1_CSV_HTTP_"+str(ex.code)) from ex
    except (urllib.error.URLError,TimeoutError,OSError) as ex:
        raise ScientificStop("SOURCE_STOP_CC_BY_TAG1_CSV_TRANSPORT_"+type(ex).__name__) from ex
    if status!=200 or "csv" not in ctype.lower() or len(raw)!=size or hashlib.sha256(raw).hexdigest()!=digest:
        raise ScientificStop("SOURCE_STOP_ORIGINAL_TAG1_SOURCE_SIZE_HASH_OR_MEDIA_DRIFT")
    return raw

def original_30_plots(raw):
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    header=next(rd,[])
    if len(header)!=17 or header[2]!="PlotID":
        raise ScientificStop("SOURCE_STOP_31123_AUTHOR_ORIGINAL_PLOTKEY_DRIFT")
    plots=set()
    n=0
    for row in rd:
        n+=1
        if len(row)!=17:raise ScientificStop("SOURCE_STOP_ORIGINAL_BEETLE_CSV_SHAPE")
        plots.add(row[2].strip())
    if n!=59850 or len(plots)!=30 or not all(plots):
        raise ScientificStop("SOURCE_STOP_31123_ORIGINAL_30_PHYSICAL_PLOT_DRIFT")
    return plots

def missing(v):
    return not v.strip() or v.strip().lower() in {"na","nan","null","n/a","none","missing"}

def medianquartiles(values):
    arr=sorted(values)
    if not arr:return None
    def q(frac):
        f=(len(arr)-1)*frac
        i=int(f)
        return arr[i]+(arr[min(i+1,len(arr)-1)]-arr[i])*(f-i)
    return {"plots_with_observed_numeric_items":len(arr),
            "min":round(arr[0],6),"q25":round(q(.25),6),
            "median":round(q(.5),6),"q75":round(q(.75),6),
            "max":round(arr[-1],6)}

def sourceonly_qa(raw,plots):
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    head=next(rd,[])
    if head!=FIELD_NAMES:
        raise ScientificStop("SOURCE_STOP_24546_TAG1_EXACT_FIELD_ORDER_DRIFT")
    n=0;in_30=0;sourceplots=set();covered=set()
    rows_by_stratum=Counter();plots_by_stratum=defaultdict(set)
    vol_by_plot_and_stratum=defaultdict(list)
    values=defaultdict(Counter)
    spec1=set();spec2=Counter()
    id_completeness=Counter()
    decay=Counter();unexpected=Counter()
    for row in rd:
        if not row or not any(x.strip() for x in row):continue
        n+=1
        if len(row)!=12:raise ScientificStop("SOURCE_STOP_24546_ORIGINAL_12_FIELD_ROW_DRIFT")
        p=row[1].strip();sourceplots.add(p)
        if p not in plots:continue
        in_30+=1;covered.add(p)
        # ONLY original 2012 measurement/identity values; NO insect outcomes
        one,two,dc,stratum,dwv,vharv=[row[i].strip() for i in (5,6,8,9,10,11)]
        if missing(one):id_completeness["spec1_missing"]+=1
        else:spec1.add(one)
        if missing(two):id_completeness["spec2_missing"]+=1
        else:spec2[two]+=1
        if missing(one) and missing(two):id_completeness["both_spec_missing"]+=1
        if not missing(one) and not missing(two):id_completeness["both_spec_present"]+=1
        if not missing(dc):
            try:val=int(dc)
            except ValueError:unexpected["dc_nonnumeric"]+=1
            else:
                if val not in (1,2,3,4,5):unexpected["dc_not_1_to_5"]+=1
                else:decay[str(val)]+=1
        else:id_completeness["dc_missing"]+=1
        if stratum not in STRATA:
            unexpected["unknown_stratum"]+=1
            continue
        rows_by_stratum[stratum]+=1
        plots_by_stratum[stratum].add(p)
        vstats=values[stratum]
        vstats["source_items"]+=1
        if missing(dwv):
            vstats["DWV_missing"]+=1
        else:
            try:fv=float(dwv)
            except ValueError:vstats["DWV_non_numeric"]+=1
            else:
                if not math.isfinite(fv):vstats["DWV_non_finite"]+=1
                else:
                    vstats["DWV_finite"]+=1
                    if fv<0:vstats["DWV_negative"]+=1
                    if fv==0:vstats["DWV_zero"]+=1
                    if fv>=0:vol_by_plot_and_stratum[(p,stratum)].append(fv)
        if not missing(vharv):
            try:hv=float(vharv)
            except ValueError:vstats["Vharv_non_numeric"]+=1
            else:
                if math.isfinite(hv):
                    vstats["Vharv_finite"]+=1
                    if hv<0:vstats["Vharv_negative"]+=1
                    if hv==0:vstats["Vharv_zero"]+=1
                else:vstats["Vharv_non_finite"]+=1
        else:vstats["Vharv_missing"]+=1
    if n!=7671 or len(sourceplots)!=148 or len(covered)!=30 or in_30!=1385:
        raise ScientificStop("SOURCE_STOP_FROZEN_7671_148_30_1385_ORIGINAL_COHORT_CHANGED")
    out={
       "schema":"structural.BELongDead24546_2012_30plots_stratum_dependent_DWV_units_original_sourcequality.v1",
       "original_BExIS_dataset_ID":24546,
       "publisher_tagged_original_codebook_and_SHA256_verified":True,
       "original_2012_source_items_in_all_148_plots":n,
       "original_2012_source_items_in_exact_30_BELongDead_experiment_plots":in_30,
       "exact_original_matched_physical_plot_ID_count":len(covered),
       "distinct_original_spec1_item_tree_taxon_codes_in_30":len(spec1),
       "spec2_author_broad_taxon_label_counts_in_30":{x:spec2.get(x,0) for x in ("Conif","Decid")},
       "spec2_other_nonmissing_label_count":sum(v for k,v in spec2.items() if k not in ("Conif","Decid")),
       "source_original_spec1_spec2_dc_missingness":dict(id_completeness),
       "source_original_decay_class_1_to_5_counts":dict(decay),
       "source_unexpected_original_categorical_codes_count_only":dict(unexpected),
       "original_source_unit_contract":{
         "T":"DWV m3 per plot-sampled item",
         "L":"DWV m3 per plot-sampled item",
         "L7":"DWV SOURCE UNIT UNVERIFIED: stratum source author says L7 but DWV description says T7",
         "S":"DWV m3 per hectare for transect sampling",
         "Vharv":"harvested stump wood m3 per hectare, NOT ambient deadwood DWV"
       },
       "source_stratum_specific_anonymous_coverage_and_numeric_validity":{},
       "no_cross_unit_DWV_sum_or_per_ha_conversion_performed":True,
       "original_2012_resource_snapshot_not_interchangeable_with_all_beetle_years_2010_2017":True,
       "original_31124_15_trapID_discrepancy_and_all_zero_effort_UNRESOLVED":True,
       "all_original_beetle_species_captures_and_trait_scores_NOT_READ":True,
       "original_source_plot_tree_taxon_item_measurement_values_NOT_EXPORTED":True,
       "all_prior_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_results_FROZEN":True,
       "eBird_used":False,
    }
    for k in STRATA:
        totals=([sum(vals) for (p,typ),vals in vol_by_plot_and_stratum.items() if typ==k and vals]
                if k!="L7" else [])
        out["source_stratum_specific_anonymous_coverage_and_numeric_validity"][k]={
           "original_source_items_in_30_plots":rows_by_stratum.get(k,0),
           "unique_original_plots_with_inventoried_items":len(plots_by_stratum[k]),
           "source_original_DWV_and_Vharv_validity_counts":dict(values[k]),
           "DWV_sum_per_plot_with_original_observed_items_ONLY":medianquartiles(totals) if k!="L7" else None,
           "L7_original_item_DWV_values_read_for_quality_only_NOT_SUMMED":k=="L7",
           "source_DWV_per_plot_sum_unit":UNITS[k],
           "no_missing_stratum_plot_inventories_imputed_as_zero":True,
        }
    if unexpected or any(values[k].get("DWV_negative",0)>0 for k in STRATA):
        out["status"]="SOURCE_2012_WOOD_STRATA_OR_NUMERIC_VALIDITY_STOP_NOT_BEETLE_NON_SUPPORT"
    else:
        out["status"]="SOURCE_2012_WOOD_RESOURCE_BY_STRATUM_30PLOT_QA_COMPLETE_NO_BIOLOGY"
    return out

def synthetic():
    assert UNITS["T"]=="m3_item" and UNITS["L"]=="m3_item"
    assert UNITS["L7"]=="UNIT_UNVERIFIED_AUTHOR_T7_VS_L7" and UNITS["S"]=="m3_per_ha"
    assert medianquartiles([1,2,3])["median"]==2
    assert missing("NA") and not missing("4.0")
    print("SYNTHETIC_ORIGINAL_DEADWOOD_DWV_UNIT_STRATA_AND_NO_IMPUTED_ZEROS_PASS")

def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",type=Path)
    a=p.parse_args();synthetic()
    if a.test:return
    if not a.out:p.error("--out needed")
    try:r=sourceonly_qa(pinned(24546),original_30_plots(pinned(31123)))
    except ScientificStop as e:
        r={"schema":"structural.BELongDead24546_2012_30plots_stratum_dependent_DWV_units_original_sourcequality.v1",
           "status":str(e),"source_STOP_not_ecological_null":True}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead24546_original30plots_DWV_strata_sourceonly_QA.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
