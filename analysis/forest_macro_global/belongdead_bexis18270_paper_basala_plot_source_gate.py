#!/usr/bin/env python3
"""Original BELongDead31123 plots × original publisher-cited BExIS18270
forest basal-area/conifer-share source: RIGHTS + EXACT author plot IDs ONLY.

The license was not assumed. Original 18270 numeric stand-tree/host resource
measurements and 31123 beetle taxon/capture values are never inspected.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,urllib.error,urllib.request
from collections import Counter
from pathlib import Path
from belongdead_bexis_13tree_original_source_gate import (
    metadata_get, CLASSIFY_LICENSE, NoRedirect,
)
from belongdead_31123_original_source_plot_tree_grain import get_original as get31123

ID=18270
ENDPOINT="https://www.bexis.uni-jena.de/api/data/18270"
MAX_LEN=5000000
OLD_SHA="73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e"
PLOT_NAMES={"PlotID","PLOT","plot","VIP","EP","EPID"}
META_YEAR_NAMES={"Year","InventoryYear","SurveyYear","ForestYear"}
GENERIC_RX={
    "stand_tree_composition_header":re.compile(r"(?:tree|species|art|baum|spruce|beech|pine|birch|fir|conif|decidu)",re.I),
    "basal_area_header":re.compile(r"(?:basal|grundflaech|g[fg]_|bhd|dbh|diam|kronen)",re.I),
    "quantity_or_share_header":re.compile(r"(?:volum|anteil|proportion|percent|share|stock|biomass|ba[_-]|m2|ha)",re.I),
    "source_time_header":re.compile(r"(?:year|datum|date|inventory|survey|aufnahm)",re.I),
}
class SourceStop(RuntimeError):pass

def get_licensed_metadata():
    ds=metadata_get("/api/dataset/18270")
    meta=metadata_get("/api/metadata/18270?tag=1.0")
    rights=meta.get("original_publisher_rights_disclosures",[])
    if "original_public_license" in ds:rights.append(ds["original_public_license"])
    admissible=any(CLASSIFY_LICENSE.search(str(v)) for v in rights)
    if ds["status"]!="PUBLISHED_ORIGINAL_ENDPOINT_REACHABLE" or meta["status"]!="PUBLISHED_ORIGINAL_ENDPOINT_REACHABLE":
        raise SourceStop("SOURCE_STOP_ORIGINAL_18270_PUBLISHER_DATASET_METADATA_UNAVAILABLE")
    if not admissible:
        raise SourceStop("SOURCE_RIGHTS_STOP_ORIGINAL_18270_NO_EXPLICIT_CC_BY_OR_CC0_LICENSE")
    return {
      "original_source_dataset_ID":ID,
      "original_source_title":ds.get("original_public_title"),
      "original_dataset_API_status":ds["status"],
      "original_version1_metadata_API_status":meta["status"],
      "original_license_explicitly_CC_BY4_OR_CC0":True,
      "original_source_public_rights_disclosures_only":rights[:4],
    }

def inventory_bytes():
    req=urllib.request.Request(ENDPOINT,headers={
        "User-Agent":"Structural-original-paper-BExIS18270-plot-sourceonly/1.0",
        "Accept":"text/csv"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=45) as h:
            raw=h.read(MAX_LEN+1)
            status=h.status
            ctype=h.headers.get("Content-Type","")
            hdr_len=h.headers.get("Content-Length","")
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_ACCESS_STOP_ORIGINAL_BEXIS18270_HTTP_"+str(ex.code)) from ex
    except (urllib.error.URLError,OSError,TimeoutError) as ex:
        raise SourceStop("SOURCE_TRANSPORT_STOP_ORIGINAL_BEXIS18270_"+type(ex).__name__) from ex
    if status!=200 or len(raw)>MAX_LEN or "csv" not in ctype.lower():
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEXIS18270_DATA_RESPONSE_OR_CAP")
    if hdr_len.isdigit() and len(raw)!=int(hdr_len):
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEXIS18270_TRUNCATED_PAYLOAD")
    return raw

def original_31123_plots():
    raw=get31123()
    if len(raw)!=8103493 or hashlib.sha256(raw).hexdigest()!=OLD_SHA:
        raise SourceStop("SOURCE_STOP_PREVIOUS_31123_FROZEN_SOURCE_CHANGED")
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=",")
    h=next(rd,[])
    if len(h)!=17 or h[2]!="PlotID" or h[3]!="Exploratory":
        raise SourceStop("SOURCE_STOP_FROZEN_31123_PLOT_SCHEMA_CHANGED")
    ids=set()
    for row in rd:
        if not row:continue
        if len(row)!=17:raise SourceStop("SOURCE_STOP_FROZEN_31123_LONG_ROW_SHAPE")
        ids.add(row[2].strip()) # source PlotID ONLY
    if len(ids)!=30 or not all(ids):
        raise SourceStop("SOURCE_STOP_FROZEN_31123_ORIGINAL_30PLOT_DRIFT")
    return ids

def original_inventory_header_and_plot_keys(raw:bytes):
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=",")
    h=next(rd,[])
    if len(h)<3 or len(h)>100:
        raise SourceStop("SOURCE_STOP_ORIGINAL_18270_HEADER_FIELD_NUMBER_INVALID")
    candidates=[i for i,x in enumerate(h) if x in PLOT_NAMES]
    if len(candidates)!=1:
        return {
          "original_header_total_fields":len(h),
          "original_publisher_exact_plot_key_header_candidates":len(candidates),
          "original_source_author_PlotID_key_NOT_UNIQUELY_IDENTIFIABLE":True,
          "original_source_stand_numeric_tree_data_UNOPENED":True,
          "status":"SOURCE_STOP_ORIGINAL_STAND_PLOT_ID_NOT_UNIQUE_OR_ABSENT"
        }
    idx=candidates[0]
    sourceplots=set()
    missing=0
    n=0
    yearindex=[i for i,x in enumerate(h) if x in META_YEAR_NAMES]
    if len(yearindex)>1:raise SourceStop("SOURCE_STOP_MULTIPLE_UNRESOLVED_AUTHOR_INVENTORY_YEARS")
    yearlabels=Counter()
    for row in rd:
        if not row or not any(x.strip() for x in row):continue
        n+=1
        if len(row)!=len(h):raise SourceStop("SOURCE_STOP_ORIGINAL_18270_LONG_ROW_WIDTH")
        plot=row[idx].strip()
        if not plot:missing+=1
        else:sourceplots.add(plot)
        if yearindex:yearlabels[row[yearindex[0]].strip()]+=1
    return {
       "_private_inventory_plots":sourceplots,
       "original_header_total_fields":len(h),
       "publisher_author_original_plot_ID_header_label_ONLY":h[idx],
       "original_plot_ID_header_column_1based":idx+1,
       "source_original_total_stand_rows":n,
       "source_rows_with_blank_PlotID":missing,
       "source_original_distinct_author_plot_IDs":len(sourceplots),
       "source_original_plot_ID_no_substring_or_alias_transform":True,
       "source_original_explicit_time_field":h[yearindex[0]] if yearindex else None,
       "source_original_distinct_time_labels":len(yearlabels),
       "original_header_candidate_field_count_categories":{
           key:sum(bool(rx.search(x)) for x in h) for key,rx in GENERIC_RX.items()
       },
       "original_source_forest_species_names_wide_headers_NOT_REEXPORTED":True,
       "original_source_stand_numeric_tree_data_UNOPENED":True,
       "status":"ORIGINAL_STAND_PLOT_META_FIELD_FOUND_NO_NUMERIC_RESOURCES_READ",
    }

def run():
    header=get_licensed_metadata()
    stand_raw=inventory_bytes()
    inv=original_inventory_header_and_plot_keys(stand_raw)
    exp=original_31123_plots()
    if "_private_inventory_plots" in inv:
        keys=inv.pop("_private_inventory_plots")
        inv["experiment_31123_original_plot_IDs_exactly_in_stand_18270"]=len(exp&keys)
        inv["original_31123_PlotID_tokens_unmatched"]=len(exp-keys)
        inv["18270_stand_original_plot_IDs_not_in_31123"]=len(keys-exp)
        inv["all_30_BELongDead_experimental_plots_present_in_stand_18270"]=len(exp-keys)==0
        inv["status"]=(
          "SOURCE_EXACT_ALL_30_BELONGDEAD_PLOTS_PRESENT_18270_STAND_FIELDMETHOD_GATE_NEXT"
          if len(exp-keys)==0 else
          "SOURCE_STAND_18270_PLOT_CROSSWALK_PARTIAL_OR_ZERO_HOLD"
        )
    return {
       "schema":"structural.BELongDead31123_publishercited_18270_stand_basal_area_30plot_exact_join_sourceonly.v1",
       "original_publisher_stand_metadata":header,
       "original_inventory_18270_source_byte_length":len(stand_raw),
       "original_inventory_18270_SHA256_receipt":hashlib.sha256(stand_raw).hexdigest(),
       "original_method_only_inventory_and_31123_plot_IDs":inv,
       "prior_3546_stand_inventory_0of30_HOLD_preserved":True,
       "prior_31124_15_new_TrapID_source_method_STOP_preserved":True,
       "no_original_beetle_species_data_or_original_stand_measurement_values_SCORED":True,
       "no_source_original_PlotID_tree_taxon_raw_site_IDs_reexported":True,
       "original_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_effects_UNCHANGED":True,
       "eBird_used":False,
       "status":inv["status"],
    }

def synthetic():
    assert len(PLOT_NAMES)==6
    assert "PlotID" in PLOT_NAMES
    assert bool(GENERIC_RX["basal_area_header"].search("BasalArea_m2ha"))
    assert not bool(GENERIC_RX["basal_area_header"].search("PLOT"))
    print("SYNTHETIC_AUTHOR_CITED_BEXIS18270_STAND_PLOT_SOURCE_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if not args.out:p.error("--out")
    try:q=run()
    except SourceStop as err:
        q={"schema":"structural.BELongDead31123_publishercited_18270_stand_basal_area_30plot_exact_join_sourceonly.v1",
            "status":str(err),
            "source_rights_or_ID_STOP_not_beetle_ecological_null":True,
            "no_new_source_wood_species_interaction_effect_scored":True}
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"BELongDead31123_18270_authorcited_forest_basal_area_plot_ID_sourceonly.json").write_text(
        json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps(q,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
