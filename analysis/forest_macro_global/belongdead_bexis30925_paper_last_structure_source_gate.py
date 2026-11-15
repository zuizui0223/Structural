#!/usr/bin/env python3
"""One final original author-cited BE forest source: BExIS30925 vs 31123 plots.

Only original public license+metadata, original source CSV header and exact
plot ID field; no tree/stand measurements, capture/taxon/trait values or p.
"""
from __future__ import annotations
import argparse,hashlib,json,urllib.error,urllib.request
from pathlib import Path
from belongdead_bexis_13tree_original_source_gate import metadata_get, CLASSIFY_LICENSE, NoRedirect
from belongdead_bexis18270_paper_basala_plot_source_gate import (
  original_inventory_header_and_plot_keys, original_31123_plots, SourceStop
)
DATA_URL="https://www.bexis.uni-jena.de/api/data/30925"
MAX_SIZE=5000000

def check():
    d=metadata_get("/api/dataset/30925")
    m=metadata_get("/api/metadata/30925?tag=1.0")
    if d["status"]!="PUBLISHED_ORIGINAL_ENDPOINT_REACHABLE" or m["status"]!="PUBLISHED_ORIGINAL_ENDPOINT_REACHABLE":
        raise SourceStop("SOURCE_STOP_30925_ORIGINAL_PUBLISHER_META_OR_VERSION1_UNAVAILABLE")
    rights=m.get("original_publisher_rights_disclosures",[])
    if "original_public_license" in d:rights.append(d["original_public_license"])
    if not any(CLASSIFY_LICENSE.search(str(v)) for v in rights):
        raise SourceStop("SOURCE_RIGHTS_STOP_30925_NOT_EXPLICIT_PUBLISHED_CC_BY4")
    req=urllib.request.Request(DATA_URL,headers={
      "User-Agent":"Structural-original-author-paper-BExIS30925-plotkeys/1.0",
      "Accept":"text/csv"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=50) as h:
            data=h.read(MAX_SIZE+1)
            ctype=h.headers.get("Content-Type","")
            size=h.headers.get("Content-Length","")
            status=h.status
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_ACCESS_STOP_30925_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,OSError,TimeoutError) as exc:
        raise SourceStop("SOURCE_TRANSPORT_STOP_30925_"+type(exc).__name__) from exc
    if status!=200 or "csv" not in ctype.lower() or len(data)>MAX_SIZE or (
        size.isdigit() and len(data)!=int(size)
    ):
        raise SourceStop("SOURCE_STOP_30925_ORIGINAL_CSV_CONTENT_NOT_FULLY_AVAILABLE")
    source=original_inventory_header_and_plot_keys(data)
    test=original_31123_plots()
    if "_private_inventory_plots" not in source:
        match=None
        source["original_30925_plot_key_not_uniquely_in_header"]=True
        status="SOURCE_PLOT_KEY_NOT_IDENTIFIABLE_ORIGINAL_30925_STOP"
    else:
        keys=source.pop("_private_inventory_plots")
        match=len(test&keys)
        source.update({
          "original_source_31123_exact_30_plot_IDs_in_30925":match,
          "original_31123_PlotID_missing_from_30925":len(test-keys),
          "original_30925_PlotIDs_not_in_BELongDead":len(keys-test),
          "author_full_30_experiment_plot_IDs_covered":match==30,
        })
        status="SOURCE_EXACT_ALL_30_MATCH_AUTHOR_STAND_RESOURCE_FIELDS_REQUIRE_CODEBOOK" if match==30 else "SOURCE_30925_FOREST_STAND_PLOT_CROSSWALK_PARTIAL_OR_ZERO_HOLD"
    return {
      "schema":"structural.BELongDead31123_publisher_cited_30925_forest_source_exact_plot_only.v1",
      "source_original_30925_dataset_ID":30925,
      "source_30925_publisher_title":d.get("original_public_title"),
      "source_30925_original_license_explicit_CC_BY4":True,
      "original_dataset_30925_source_version1":True,
      "source_original_csv_bytes":len(data),
      "source_original_csv_sha256":hashlib.sha256(data).hexdigest(),
      "original_source_30925_metadata_plot_and_field_headers_only":source,
      "source_previous_3546_0of30_and_18270_3of30_joins_unmodified":True,
      "source_31124_15_additional_trapID_method_HOLD_unmodified":True,
      "no_original_beetle_species_or_forest_stand_numeric_values_read_or_scored":True,
      "source_original_raw_site_PlotID_species_columns_NOT_REEXPORTED":True,
      "all_Finland_Burner_PREDICTS_NEON_BALA_GEB_prior_outcomes_UNCHANGED":True,
      "eBird_used":False,
      "status":status,
    }

def synthetic():
    assert CLASSIFY_LICENSE.search("CC BY 4.0")
    assert DATA_URL.endswith("/30925")
    assert not DATA_URL.endswith("/30924")
    print("SYNTHETIC_AUTHOR_CITED_30925_SOURCE_ONLY_FROZEN_ID_AND_LICENSE_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    synthetic()
    if a.test:return
    if not a.out:ap.error("--out")
    try:z=check()
    except SourceStop as exc:
        z={"schema":"structural.BELongDead31123_publisher_cited_30925_forest_source_exact_plot_only.v1",
           "status":str(exc),
           "source_only_stop_not_ecological_null":True,
           "original_study_BE_effects_untouched":True}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead31123_authorcited30925_stand_30plot_sourceonly.json").write_text(
       json.dumps(z,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(z,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
