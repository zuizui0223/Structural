#!/usr/bin/env python3
"""BELongDead source-pool hostwood validation: BExIS 3546 inventory SOURCE ONLY.

One original version-5 stand inventory metadata and rights check, then one
bounded official CSV first-header fetch if CC BY4 source public/authorized.
No original beetle or inventory plot/year/stem resource measurements parsed.
"""
from __future__ import annotations
import argparse,csv,json,re,urllib.error,urllib.request,urllib.parse
from pathlib import Path

from belongdead_bexis_13tree_original_source_gate import (
    metadata_get, CLASSIFY_LICENSE, NoRedirect, sanitized_license_recursive
)

ORIGINAL_ID=3546
DATA_ENDPOINT="https://www.bexis.uni-jena.de/api/data/3546"
MAX_READ=65536
KNOWN={
 "plot","plotid","plot_id","forest","forestid","forest_id","vip",
 "vipid","site","siteid","site_id","stand","standid","stand_id",
 "exploratory","region","regionid","region_id","inventory",
 "inventoryyear","surveyyear","samplingyear","collectionyear","year",
 "date","treename","tree","treeid","tree_id","treespecies",
 "tree_species","woodspecies","species","speciename","speciesname",
 "treegenus","genus","basalarea","basal_area","volume","woodvolume",
 "livewood","deadwood","canopy","dbh","diameter","treecount",
 "stock","volumeperha","biomass","abundance","proportion","percent",
 "age","standage","area","landuse","management","samplingdate",
 "foresttype","standtype","exposure","sample"
}

def first_csv_header(raw,contenttype):
    if b"\n" not in raw:
        return {"status":"SOURCE_HEADER_STOP_FIRST_LINE_NOT_COMPLETE"}
    first=raw.split(b"\n",1)[0].rstrip(b"\r")
    if len(first)>32768:
        return {"status":"SOURCE_HEADER_STOP_TOO_LONG"}
    try:
        line=first.decode("utf-8-sig")
    except UnicodeError:
        return {"status":"SOURCE_HEADER_STOP_ENCODING"}
    delim=max((",","\t",";"),key=line.count)
    if not line.count(delim):
        return {"status":"SOURCE_HEADER_STOP_DELIMITER_MISSING"}
    cols=next(csv.reader([line],delimiter=delim),[])
    safe=[]
    for i,label in enumerate(cols):
        label=str(label).strip()
        normalized=re.sub(r"[^a-z0-9]","",label.lower())
        if normalized in KNOWN and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_ .-]{0,60}",label):
            safe.append({"field_source_column_1based":i+1,"original_generic_header_only":label})
    return {
       "status":"ORIGINAL_FOREST_INVENTORY_HEADER_RECEIVED_NO_VALUES",
       "original_header_total_columns":len(cols),
       "original_generic_plot_tree_volume_time_fields_only":safe,
       "original_source_delimiter_category":{",":"comma","\t":"tab",";":"semicolon"}[delim],
       "species_specific_wide_column_names_NOT_EXPORTED":True,
       "original_inventory_tree_or_plot_values_UNREAD":True,
    }

def source_first_header():
    request=urllib.request.Request(DATA_ENDPOINT,headers={
        "User-Agent":"Structural-original-BEXIS3546-inventory-header-sourceonly-2026/1.0",
        "Accept":"text/csv,application/json;q=0.8,*/*;q=0.5",
        "Range":"bytes=0-65535"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request,timeout=40) as f:
            raw=f.read(MAX_READ)
            ctype=f.headers.get("Content-Type","")
            clen=f.headers.get("Content-Length","")
            status=f.status
            contRange=f.headers.get("Content-Range","")
        out={
           "original_source_endpoint_HTTP_status":status,
           "publisher_content_type_class":(
                "csv" if "csv" in ctype.lower() else
                "json" if "json" in ctype.lower() else
                "html" if "html" in ctype.lower() else
                "other"),
           "server_original_total_content_length_if_provided":int(clen) if clen.isdigit() else None,
           "publisher_byte_range_respected":bool(contRange),
           "first_only_bytes_received_then_stream_closed":len(raw),
           "no_original_forest_inventory_measurement_values_decoded":True,
        }
        if status not in (200,206):
            out["status"]="SOURCE_DATA_STOP_NON200"
        elif out["publisher_content_type_class"]=="csv":
            out["source_inventory_first_header"]=first_csv_header(raw,ctype)
            out["status"]=out["source_inventory_first_header"]["status"]
        else:
            out["status"]="SOURCE_DATA_CONTENT_SCHEMA_NOT_CSV_DO_NOT_PARSE_VALUES"
        return out
    except urllib.error.HTTPError as e:
        return {"status":"SOURCE_ACCESS_STOP_HTTP","http_status":e.code}
    except (urllib.error.URLError,OSError,TimeoutError) as e:
        return {"status":"SOURCE_TRANSPORT_STOP","error_class":type(e).__name__}

def original_version5_metadata():
    """One exact publisher-prescribed BExIS /api/metadata/3546?tag=5.0."""
    req=urllib.request.Request(
        "https://www.bexis.uni-jena.de/api/metadata/3546?tag=5.0",
        headers={"User-Agent":"Structural-BExIS-3546-original-metadata-v5/1.0",
                 "Accept":"application/json"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=25) as resp:
            raw=resp.read(350001)
            status=resp.status
            ctype=resp.headers.get("Content-Type","")
        if status!=200 or len(raw)>350000 or "json" not in ctype.lower():
            return {"status":"SOURCE_STOP_PUBLISHED_VERSION5_METADATA_NOT_JSON_OR_TOO_LARGE"}
        doc=json.loads(raw.decode("utf-8"))
        return {"status":"PUBLISHED_ORIGINAL_ENDPOINT_REACHABLE",
                "http_status":200,
                "original_publisher_rights_disclosures":sanitized_license_recursive(doc),
                "original_source_metadata_bytes":len(raw)}
    except urllib.error.HTTPError as exc:
        return {"status":"SOURCE_ACCESS_STOP_HTTP","http_status":exc.code}
    except (urllib.error.URLError,OSError,TimeoutError,ValueError) as exc:
        return {"status":"SOURCE_TRANSPORT_OR_PARSE_STOP",
                "error_class":type(exc).__name__}


def run():
    ds=metadata_get("/api/dataset/3546")
    meta=original_version5_metadata()
    original_license=meta.get("original_publisher_rights_disclosures",[])
    if "original_public_license" in ds:original_license.append(ds["original_public_license"])
    verified=any(CLASSIFY_LICENSE.search(v) for v in original_license)
    official_api_reachable=ds["status"]=="PUBLISHED_ORIGINAL_ENDPOINT_REACHABLE" and meta["status"]=="PUBLISHED_ORIGINAL_ENDPOINT_REACHABLE"
    # True public metadata does not itself assert data open. Check original
    # dataset source GET separately only after individual source license verified.
    item={
      "schema":"structural.BELongDead_original_BExIS3546_stand_inventory_host_source_pool_sourceonly.v1",
      "original_inventory_dataset_ID":ORIGINAL_ID,
      "publisher_dataset_metadata_status":ds["status"],
      "publisher_metadata_version5_status":meta["status"],
      "source_title_from_original_publisher":ds.get("original_public_title"),
      "source_version_from_publisher":ds.get("original_public_version"),
      "source_explicit_CC_BY4_or_CC0_license_detected":verified,
      "publisher_original_individual_license_disclosure":original_license[:5],
      "BE_31123_pinned_long_tree_host_metadata_30plots_13tree_species_ALREADY_VERIFIED":True,
      "BE_31124_same_experiment_subset_not_independent_study":True,
      "BExIS_3546_forest_species_resource_source_rows_UNOPENED":True,
      "BExIS_31123_original_beetle_outcome_UNOPENED":True,
      "no_new_source_pool_or_saproxylic_effect_scored":True,
      "old_Finland_Burner_PREDICTS_NEON_BALA_GEB_scores_FROZEN":True,
      "eBird_used":False,
    }
    if not official_api_reachable:
        item["status"]="SOURCE_ACCESS_OR_VERSION_STOP_INVENTORY_ORIGINAL_METADATA"
        return item
    if not verified:
        item["status"]="SOURCE_RIGHTS_STOP_INVENTORY_NO_EXPLICIT_DATASET_LICENSE"
        return item
    item["original_data_first_header_access"]=source_first_header()
    item["status"]=item["original_data_first_header_access"]["status"]
    return item

def synthetic():
    x=first_csv_header(b"PlotID,Year,TreeSpecies,DBH,Pinus sylvestris\nP1,2018,Picea,22,0\n","text/csv")
    assert x["original_header_total_columns"]==5
    assert len(x["original_generic_plot_tree_volume_time_fields_only"])==4
    assert not any("sylvestris" in str(v) for v in x["original_generic_plot_tree_volume_time_fields_only"])
    assert CLASSIFY_LICENSE.search("CC BY 4.0")
    assert original_version5_metadata.__name__=="original_version5_metadata"
    print("SYNTHETIC_BEXIS3546_SOURCE_LICENSE_AND_TREE_INVENTORY_HEADER_PRIVACY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out")
    item=run()
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"bexis3546_original_forest_inventory_tree_species_supply_headeronly.json").write_text(
        json.dumps(item,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(item,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
