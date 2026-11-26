#!/usr/bin/env python3
"""Source-only BExIS24546 ambient deadwood item measurements: field quality.

Original 2012 CC BY4 source 7671 item rows/148 plots. Biological beetle
records (BExIS31123) never accessed apart from original set of 30 plot IDs,
whose data decoder accesses only the published PlotID column.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,urllib.error,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from belongdead_bexis18270_paper_basala_plot_source_gate import original_31123_plots
SHA="5a02350e4f1e364302dea20ca25281e65f2158d318d9fbcef56be2fe6d57786a"
BYTES=417351
CSV_URL="https://www.bexis.uni-jena.de/api/data/24546"
SPECIES_PAT=re.compile(r"^(?:tree[_ -]?species|wood[_ -]?species|species|species[_ -]?name|baumart|tree[_ -]?type|art|baumartcode)$",re.I)
VOLUME_PAT=re.compile(r"^(?:vol(?:ume)?(?:[_ -]?(?:m3|m³|ha|perha|per_ha))?|wood[_ -]?volume(?:[_ -]?(?:m3|perha))?|deadwood[_ -]?vol(?:ume)?(?:[_ -]?(?:m3|perha))?|totholz[_ -]?(?:volumen|menge)|v[_ -]?m3)$",re.I)
METH_PAT=re.compile(r"(?:plot|site|year|date|invent|decay|diam|length|height|stand|lying|fallen|dead|log|item|tree|wood|vol|species|art|baum|bhd|dbh|status|type|class|unit)",re.I)

class SourceStop(RuntimeError):pass

def original_csv():
    request=urllib.request.Request(CSV_URL,headers={"User-Agent":"Structural-original-BExIS24546-2012-source-only-QA/1.0",
                                                     "Accept":"text/csv"})
    try:
        with urllib.request.urlopen(request,timeout=43) as f:
            content=f.read(BYTES+1)
            code=f.status
            ctype=f.headers.get("Content-Type","")
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_ACCESS_STOP_BEXIS24546_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,OSError,TimeoutError) as e:
        raise SourceStop("SOURCE_TRANSPORT_STOP_BEXIS24546_"+type(e).__name__) from e
    if code!=200 or len(content)!=BYTES or "csv" not in ctype.lower() or hashlib.sha256(content).hexdigest()!=SHA:
        raise SourceStop("SOURCE_STOP_PRECOMMITTED_BEXIS24546_BYTE_OR_SHA_DRIFT")
    return content

def inspect(raw,original_30):
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=",")
    h=next(rd,[])
    if len(h)!=12 or h[1]!="plotID":
        raise SourceStop("SOURCE_STOP_ORIGINAL_12COLUMNS_AND_PLOTID_COLUMN2_CHANGED")
    # Publisher original schema names exposed ONLY when field names themselves
    # are safe method descriptors. Never output actual taxon/plot data strings.
    safe=[]
    for idx,v in enumerate(h):
        if len(v)<=60 and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_ .()/+-]{0,59}",v):
            safe.append({"original_column_position_1based":idx+1,
                         "original_source_method_header":v,
                         "source_method_header_candidate":bool(METH_PAT.search(v))})
    sp=[i for i,v in enumerate(h) if SPECIES_PAT.fullmatch(v.strip())]
    vol=[i for i,v in enumerate(h) if VOLUME_PAT.fullmatch(v.strip())]
    pl=set()
    per_plot=Counter()
    cats=set();cat_missing=0
    vol_total=vol_missing=vol_finite=vol_negative=vol_zero=0
    nonnumeric=0
    n=0
    source_30_rows=0
    for row in rd:
        if not row or not any(v.strip() for v in row):continue
        n+=1
        if len(row)!=12:
            raise SourceStop("SOURCE_STOP_ORIGINAL_SOURCE_ITEM_ROW_WIDTH_CHANGED")
        id=row[1].strip()
        if not id:raise SourceStop("SOURCE_STOP_ORIGINAL_INVENTORY_PLOT_ID_MISSING")
        pl.add(id);per_plot[id]+=1
        if id in original_30:
            source_30_rows+=1
            if len(sp)==1:
                v=row[sp[0]].strip()
                if v and v.lower() not in ("na","nan","null","n/a"):
                    cats.add(v)
                else:cat_missing+=1
            if len(vol)==1:
                vol_total+=1
                v=row[vol[0]].strip()
                if not v or v.lower() in ("na","nan","null","n/a"):
                    vol_missing+=1
                else:
                    try:x=float(v.replace(",","."))
                    except ValueError:nonnumeric+=1;continue
                    if not math.isfinite(x):vol_missing+=1
                    else:
                        vol_finite+=1
                        if x<0:vol_negative+=1
                        if x==0:vol_zero+=1
    if n!=7671 or len(pl)!=148 or len(original_30)!=30 or not original_30.issubset(pl):
        raise SourceStop("SOURCE_STOP_ORIGINAL_DEADWOOD_148PLOT_30MATCH_7671_ROWS_DRIFT")
    counts=[per_plot[x] for x in original_30]
    return {
      "schema":"structural.BELongDead24546_2012_deadwood_measurement_field_source_quality.v1",
      "BExIS24546_pinned_original_SHA256":SHA,
      "2012_original_deadwood_inventory_rows_not_independent_forests":n,
      "2012_original_deadwood_distinct_plot_IDs":len(pl),
      "original_BELongDead31123_full_30of30_plot_identity_matched":True,
      "original_30_experimental_plots_source_inventory_rows":source_30_rows,
      "original_rows_in_each_of_30_BELongDead_plots_min":min(counts),
      "original_rows_in_each_of_30_BELongDead_plots_median":sorted(counts)[len(counts)//2],
      "original_rows_in_each_of_30_BELongDead_plots_max":max(counts),
      "original_headers_only_no_original_wood_species_taxa_or_plot_names":safe,
      "original_tree_species_generic_field_exact_candidates":[h[i] for i in sp],
      "original_item_volume_generic_field_exact_candidates":[h[i] for i in vol],
      "original_tree_species_field_unambiguous":len(sp)==1,
      "original_volume_field_unambiguous":len(vol)==1,
      "original_2012_tree_species_category_count_within_30plots_only":len(cats) if len(sp)==1 else None,
      "original_2012_tree_species_missing_item_rows_within_30plots_only":cat_missing if len(sp)==1 else None,
      "original_2012_volume_measurement_validity_in_30plots_ONLY":{
         "rows_measured":vol_total,"finite":vol_finite,"missing":vol_missing,
         "non_numeric":nonnumeric,"negative":vol_negative,"zero":vol_zero,
      } if len(vol)==1 else None,
      "original_2012_measured_volume_units_NOT_assumed_without_author_codebook":True,
      "source_original_species_or_item_volume_values_never_exported":True,
      "BExIS31123_original_insect_species_abundance_or_traits_UNREAD":True,
      "source_original_2012_deadwood_not_living_source_tree_forest_basalarea":True,
      "source_original_2012_time_not_contemporaneous_to_all_2010_2017_beetle_years":True,
      "prior_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
      "eBird_used":False,
      "status":"SOURCE_ONLY_ORIGINAL_2012_DEADWOOD_FIELD_QA_COMPLETE"
    }

def synthetic():
    assert SPECIES_PAT.fullmatch("Baumart")
    assert SPECIES_PAT.fullmatch("TreeSpecies")
    assert VOLUME_PAT.fullmatch("Volume_m3")
    assert not VOLUME_PAT.fullmatch("plotID")
    assert len(SHA)==64
    print("SYNTHETIC_ORIGINAL_DEADWOOD_TREE_FIELD_VOLUME_PREBIOLOGY_QA_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out required")
    try:
        old=original_31123_plots()
        result=inspect(original_csv(),old)
    except SourceStop as ex:
        result={"schema":"structural.BELongDead24546_2012_deadwood_measurement_field_source_quality.v1",
                "status":str(ex),
                "scientific_source_STOP_not_a_beetle_effect":True,
                "previous_frozen_results_UNCHANGED":True}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead24546_2012_original_deadwood_tree_volume_sourceonly_QA.json").write_text(
         json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
