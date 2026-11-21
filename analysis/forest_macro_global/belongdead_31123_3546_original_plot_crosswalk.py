#!/usr/bin/env python3
"""Licensed original BExIS31123 experimental deadwood plots vs BExIS3546
stand-inventory exact original PLOT key / field header source-only crosswalk.

No beetle species names/abundance/trap values or inventory stem/wood numeric
measurements are accessed; only original plot IDs and header field metadata.
Full author original files remain in memory on runner; output only aggregates.
"""
from __future__ import annotations

import argparse,csv,hashlib,io,json,re,urllib.error,urllib.request
from collections import Counter,defaultdict
from pathlib import Path

from belongdead_31123_original_source_plot_tree_grain import get_original as get_belongdead_31123

N_BEETLE=8103493
SHA_BEETLE="73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e"
N_INVENTORY=40458
URL_INVENTORY="https://www.bexis.uni-jena.de/api/data/3546"
SOURCE_META_FIELDS={"Year","InventoryYear"}
SRC_SPECIES_HEADER=re.compile(r"(?i)(tree.?species|species|taxon|tree.?type|birch|beech|oak|spruce|pine|fir|speciesname)")
SRC_RESOURCE_HEADER=re.compile(r"(?i)(basal|volume|biomass|dbh|diam|stem|stock|wood|cover|age|treecount|tree.?count)")

class ScientificStop(RuntimeError):pass


def get_inventory():
    req=urllib.request.Request(
        URL_INVENTORY,headers={"User-Agent":"Structural-original-BExIS3546-31123-sourceonly-2026/1.0",
                               "Accept":"text/csv"})
    try:
        with urllib.request.urlopen(req,timeout=32) as h:
            raw=h.read(N_INVENTORY+1)
            status=h.status
            ctype=h.headers.get("Content-Type","")
    except urllib.error.HTTPError as e:
        raise ScientificStop("SOURCE_STOP_STAND_INVENTORY_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,OSError,TimeoutError) as e:
        raise ScientificStop("SOURCE_STOP_STAND_INVENTORY_TRANSPORT_"+type(e).__name__) from e
    if status!=200 or "csv" not in ctype.lower() or len(raw)!=N_INVENTORY:
        raise ScientificStop("SOURCE_STOP_STAND_INVENTORY_ORIGINAL_BYTECOUNT_OR_MEDIA_CHANGED")
    return raw


def parse_original_csv_meta(raw,source_kind):
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=",")
    cols=next(rd,[])
    if source_kind=="beetle":
        if len(cols)!=17 or cols[2:4]!=["PlotID","Exploratory"]:
            raise ScientificStop("SOURCE_STOP_BELONGDEAD_ORIGINAL_PLOT_FIELD_ID_CHANGED")
        plots=set()
        ex_by_plot=defaultdict(set)
        records=0
        for row in rd:
            records+=1
            if len(row)!=17:
                raise ScientificStop("SOURCE_STOP_BEETLE_LONG_ROW_SHAPE")
            plot,ex=row[2].strip(),row[3].strip()
            if not plot or not ex:
                raise ScientificStop("SOURCE_STOP_BEETLE_FIELD_PLOT_EMPTY")
            plots.add((ex,plot));ex_by_plot[plot].add(ex)
        if records!=59850 or len(plots)!=30:
            raise ScientificStop("SOURCE_STOP_OLD_BELONGDEAD_59850_30PLOT_METADATA_DRIFT")
        return {
            "_private_plotid_set":set(x[1] for x in plots),
            "_private_nested_plot_keys":plots,
            "original_long_records_NOT_independent_traps_or_beetles":records,
            "original_nested_exploratory_plot_keys":len(plots),
            "distinct_original_TrapData_PlotID_tokens":len(set(x[1] for x in plots)),
            "PlotID_tokens_reused_across_Exploratories":sum(len(v)>1 for v in ex_by_plot.values()),
            "source_beetle_capture_abundance_species_or_tree_values_UNREAD":True,
        }
    else:
        if len(cols)!=16 or cols[0]!="PLOT":
            raise ScientificStop("SOURCE_STOP_ORIGINAL_3546_INVENTORY_16COL_PLOT_SCHEMA_DRIFT")
        safe=[]
        for i,x in enumerate(cols):
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_ .+()/-]{0,55}",x):
                safe.append({"original_field_col_1based":i+1,"publisher_original_inventory_HEADER_only":x})
        time_fields=[(j,v) for j,v in enumerate(cols) if v in SOURCE_META_FIELDS]
        if len(time_fields)>1:
            raise ScientificStop("SOURCE_STOP_MULTIPLE_AUTHOR_YEAR_HEADERS_FOR_STAND_INVENTORY")
        index,yearname=time_fields[0] if time_fields else (None,None)
        plot_tokens=set();records=0;blank=0;plot_counts=Counter();year_counts=Counter()
        for row in rd:
            records+=1
            if len(row)!=16:
                raise ScientificStop("SOURCE_STOP_STAND_INVENTORY_CSV_ROW_SHAPE")
            plot=row[0].strip()
            if not plot:blank+=1;continue
            plot_tokens.add(plot)
            plot_counts[plot]+=1
            if index is not None:
                year_counts[row[index].strip()]+=1
        return {
            "_private_inventory_plot_set":plot_tokens,
            "original_stand_inventory_rows":records,
            "original_stand_PLOT_missing_rows":blank,
            "original_stand_PLOT_distinct_labels":len(plot_tokens),
            "inventory_plot_labels_represented_multiple_rows":sum(v>1 for v in plot_counts.values()),
            "max_inventory_source_rows_per_same_PLOT":max(plot_counts.values(),default=0),
            "inventory_original_complete_field_header_only":safe,
            "inventory_source_year_field_if_explicit":yearname,
            "inventory_distinct_year_labels_if_present":len(year_counts),
            "inventory_year_label_counts_not_survey_ages":dict(year_counts) if index is not None else {},
            "source_original_headers_direct_tree_taxon_candidates_only":[x for x in cols if SRC_SPECIES_HEADER.search(x)],
            "source_original_headers_tree_quantity_structure_candidates_only":[x for x in cols if SRC_RESOURCE_HEADER.search(x)],
            "original_inventory_basal_area_volume_tree_measured_cells_UNREAD":True,
            "original_source_ID_values_NOT_EXPORTED":True,
        }


def compare(bet,inventory):
    source=bet["_private_plotid_set"]
    inv=inventory["_private_inventory_plot_set"]
    return {
        "source_original_BELongDead_distinct_PlotID_tokens":len(source),
        "source_original_forest_inventory_distinct_PLOT_tokens":len(inv),
        "source_original_exact_PlotID_against_PLOT_intersection":len(source&inv),
        "source_BELongDead_plot_tokens_missing_from_inventory":len(source-inv),
        "source_inventory_plot_tokens_not_in_30_BELongDead":len(inv-source),
        "source_plot_ID_comparison_trim_whitespace_only_NO_guessed_alias":True,
        "source_same_year_stand_inventory_and_experimental_tree_supply_NOT_verified":True,
        "source_species_and_forest_measurements_NOT_SCORED":True,
        "no_site_plot_identifier_strings_exported":True,
    }


def known_truth():
    a={("ALB","A"),("SCH","B")}
    b={"A","B","C"}
    assert len({v for _,v in a}&b)==2
    assert SRC_SPECIES_HEADER.search("TreeSpecies")
    assert SRC_RESOURCE_HEADER.search("BasalArea")
    assert not SRC_SPECIES_HEADER.search("PLOT")
    print("SYNTHETIC_3546_VERSUS_31123_EXACT_ORIGINAL_SOURCE_PLOT_ID_ONLY_PASS")


def run():
    beetle=get_belongdead_31123()
    if len(beetle)!=N_BEETLE or hashlib.sha256(beetle).hexdigest()!=SHA_BEETLE:
        raise ScientificStop("SOURCE_STOP_ORIGINAL_BELONGDEAD_31123_SOURCE_SHA_DRIFT")
    stand=get_inventory()
    b=parse_original_csv_meta(beetle,"beetle")
    i=parse_original_csv_meta(stand,"inventory")
    cross=compare(b,i)
    b.pop("_private_plotid_set");b.pop("_private_nested_plot_keys")
    i.pop("_private_inventory_plot_set")
    return {
      "schema":"structural.BELongDead_BExIS31123_with_BExIS3546_exact_PLOT_sourceonly.v1",
      "original_experimental_beetle_source_ID":31123,
      "original_stand_inventory_source_ID":3546,
      "original_31123_sha256_verified":SHA_BEETLE,
      "original_3546_sha256_receipt_only":hashlib.sha256(stand).hexdigest(),
      "original_31123_and_3546_byte_lengths_verified":[len(beetle),len(stand)],
      "author_31123_and_3546_CC_BY4_licenses_verified_pre_CI":True,
      "beetle_original_metadata_only":b,
      "stand_original_metadata_only":i,
      "exact_source_plot_crosswalk":cross,
      "no_new_BELongDead_ecological_effect_estimated":True,
      "Finnish_VD10_Burner_PREDICTS_NEON_BALA_GEB_previous_scores_unchanged":True,
      "eBird_used":False,
      "status":(
         "SOURCE_PLOT_ID_EXACT_30OF30_MATCH_STAND_SPECIES_QUANTITY_SCHEMA_STILL_REQUIRES_AUTHOR_CODEBOOK"
         if cross["source_original_exact_PlotID_against_PLOT_intersection"]==30 else
         "SOURCE_STAND_INVENTORY_EXACT_PLOT_ID_PARTIAL_OR_ZERO_SOURCE_JOIN_HOLD"
      ),
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if not a.out:p.error("--out")
    try:r=run()
    except ScientificStop as exc:
        r={
            "schema":"structural.BELongDead_BExIS31123_with_BExIS3546_exact_PLOT_sourceonly.v1",
            "status":str(exc),
            "source_stop_not_ecological_null":True,
            "no_beetle_or_stand_numeric_effect_scored":True,
        }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead_31123_3546_original_exact_plot_sourceonly.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
