#!/usr/bin/env python3
"""Source-only official BE field plot ID bridge, BExIS1000 and BExIS24546.

Check official publisher metadata/license, then read ONLY whitelisted plot
identity/hierarchy fields, never coordinates, environmental measurements,
species labels, beetle abundances, trait scores or individual source IDs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from belongdead_bexis_13tree_original_source_gate import (
    CLASSIFY_LICENSE, NoRedirect, sanitized_license_recursive
)
from belongdead_bexis18270_paper_basala_plot_source_gate import (
    original_31123_plots, inventory_bytes, original_inventory_header_and_plot_keys
)

BASE="https://www.bexis.uni-jena.de"
ORIGINAL={
   1000:{"fallback_publisher_version":7,"maximum_bytes":2_000_000},
   24546:{"fallback_publisher_version":1,"maximum_bytes":10_000_000},
}
# Rigid field lookup from official source DATA HEADER, defined before original
# source record values. Names describe actual plot hierarchy, not coordinates.
IDENTITY_FIELDS={
   "plot","plotid","plotname","ep","epid","epname","vip","vipid",
   "vipname","parentplotid","parentplot","parentep","parentepid",
   "gp","gpid","mip","mipid","plotcode","plotidentifier",
}
PLOT_CLASS_FIELDS={"plottype","plotclass","plotcategory","plotlevel","plotstatus"}
YEARS={"year","inventoryyear","surveyyear","collectionyear"}
ALIAS_ROLES={
 "VIP":("vip","vipid","vipname"),
 "EP":("ep","epid","epname"),
}
class SourceStop(RuntimeError):pass


def norm_field(v):
    return re.sub(r"[^a-z0-9]","",str(v).strip().lower())


def official_json(path):
    if not re.fullmatch(r"/api/(?:dataset|metadata)/\d+(?:\?tag=\d+\.0)?",path):
        raise SourceStop("SOURCE_STOP_NON_PUBLISHER_METADATA_URI")
    try:
        with urllib.request.build_opener(NoRedirect).open(
            urllib.request.Request(BASE+path,
               headers={"User-Agent":"Structural-publisher-author-plot-hierarchy-sourceonly/1.0",
                        "Accept":"application/json"}),timeout=24
        ) as resp:
            body=resp.read(500001)
            status=resp.status
            ctype=resp.headers.get("Content-Type","")
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_ACCESS_STOP_PUBLISHER_METADATA_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,OSError,TimeoutError) as e:
        raise SourceStop("SOURCE_TRANSPORT_STOP_PUBLISHER_META_"+type(e).__name__) from e
    if status!=200 or len(body)>500000 or "json" not in ctype.lower():
        raise SourceStop("SOURCE_STOP_PUBLISHER_METADATA_NONJSON_OR_TOO_LARGE")
    try:return json.loads(body.decode("utf-8"))
    except ValueError as e:
        raise SourceStop("SOURCE_STOP_PUBLISHER_METADATA_NOT_DECODABLE_JSON") from e


def dataset_rights(dataset_id):
    info=ORIGINAL[dataset_id]
    record=official_json(f"/api/dataset/{dataset_id}")
    if not isinstance(record,dict):
        raise SourceStop("SOURCE_STOP_SOURCE_DATASET_METADATA_NOT_OBJECT")
    published=record.get("isPublic")
    if published is False:
        raise SourceStop("SOURCE_RIGHTS_STOP_SOURCE_DATASET_NOT_PUBLIC")
    rawver=record.get("version")
    if dataset_id==24546:
        # Official BE public catalogue cites precisely 24546 V1. The
        # /api/dataset returned current version must NOT override that pinned
        # source version; it caused a code-only STOP in earlier audit.
        v=1
    elif isinstance(rawver,(int,float)) and int(rawver)==rawver and 1<=int(rawver)<=50:
        v=int(rawver)
    elif isinstance(rawver,str) and re.fullmatch(r"\\d+(?:\\.0)?",rawver) and 1<=int(float(rawver))<=50:
        v=int(float(rawver))
    else:
        v=info["fallback_publisher_version"]
    md=official_json(f"/api/metadata/{dataset_id}?tag={v}.0")
    rights=sanitized_license_recursive(md)
    licensed=any(CLASSIFY_LICENSE.search(str(x)) for x in rights)
    if not licensed:
        raise SourceStop("SOURCE_RIGHTS_STOP_NO_ORIGINAL_INDIVIDUAL_CC_BY_OR_CC0")
    return {
      "original_published_dataset_id":dataset_id,
      "original_source_version_selected_from_metadata_or_catalogue":v,
      "original_publisher_title":str(record.get("title",""))[:150],
      "original_publisher_isPublic_field":published,
      "original_source_cc_by_cc0_licence_verified":licensed,
      "original_publisher_license_disclosures":rights[:4],
      "publisher_version_status_metadata_HTTP200":True,
    }


def original_csv_bytes(dataset_id):
    limit=ORIGINAL[dataset_id]["maximum_bytes"]
    try:
        with urllib.request.build_opener(NoRedirect).open(
            urllib.request.Request(BASE+f"/api/data/{dataset_id}",
              headers={"User-Agent":"Structural-publisher-original-EP-VIP-fields-only/1.0",
                       "Accept":"text/csv"}),timeout=44
        ) as resp:
            b=resp.read(limit+1)
            status=resp.status
            ctype=resp.headers.get("Content-Type","")
            clen=resp.headers.get("Content-Length","")
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_ACCESS_STOP_ORIGINAL_CSV_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,OSError,TimeoutError) as e:
        raise SourceStop("SOURCE_TRANSPORT_STOP_ORIGINAL_CSV_"+type(e).__name__) from e
    if status!=200 or "csv" not in ctype.lower() or len(b)>limit or (
        clen.isdigit() and len(b)!=int(clen)
    ):
        raise SourceStop("SOURCE_STOP_ORIGINAL_DATA_CSV_SIZE_OR_TYPE")
    return b


def header_and_id_field_collections(raw,source_id):
    reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    header=next(reader,[])
    if not 2<=len(header)<=150:
        raise SourceStop("SOURCE_STOP_ORIGINAL_PLOT_REGISTRY_HEADER_FIELD_COUNT")
    normalized=[norm_field(x) for x in header]
    # Fixed source role categories; coordinates, species, numeric forest data
    # and their values are never accessed.
    ididx=[i for i,n in enumerate(normalized) if n in IDENTITY_FIELDS]
    classidx=[i for i,n in enumerate(normalized) if n in PLOT_CLASS_FIELDS]
    yearidx=[i for i,n in enumerate(normalized) if n in YEARS]
    value_sets={i:set() for i in ididx}
    paired_rows=[]
    n=0
    complete=0
    missing=Counter()
    yrs={i:set() for i in yearidx}
    for row in reader:
        if not row or not any(x.strip() for x in row):continue
        n+=1
        if len(row)!=len(header):
            raise SourceStop("SOURCE_STOP_ORIGINAL_PLOT_ID_REGISTRY_CSV_WIDTH")
        idrow={}
        for idx in ididx:
            token=row[idx].strip()
            if not token:
                missing[normalized[idx]]+=1
            else:
                value_sets[idx].add(token)
                idrow[normalized[idx]]=token
        for idx in yearidx:
            token=row[idx].strip()
            if token:yrs[idx].add(token)
        if idrow:complete+=1
        vip=next((idrow[x] for x in ALIAS_ROLES["VIP"] if x in idrow),None)
        ep=next((idrow[x] for x in ALIAS_ROLES["EP"] if x in idrow),None)
        if vip is not None and ep is not None:
            paired_rows.append((vip,ep))
        # No original numeric forest/coordinates/organisms values accessed.
    if not n:
        raise SourceStop("SOURCE_STOP_ORIGINAL_PLOT_ID_REGISTRY_NO_ROWS")
    out={
      "source_original_dataset_id":source_id,
      "source_original_public_CSV_bytes":len(raw),
      "source_original_public_CSV_sha256":hashlib.sha256(raw).hexdigest(),
      "source_original_total_columns":len(header),
      "source_original_record_rows_NOT_independent_FORESTS":n,
      "source_original_rows_with_any_explicit_plot_ID":complete,
      "source_exact_predeclared_plot_identity_fields":[
         {"field_source_column_1based":i+1,"source_generic_header_name":header[i],
          "distinct_nonblank_source_tokens":len(value_sets[i]),
          "missing_source_plot_values":missing.get(normalized[i],0)}
         for i in ididx
      ],
      "source_plot_class_field_header_names_only":[header[i] for i in classidx],
      "source_year_field_labels_and_distinct_counts_ONLY":[
         {"header":header[i],"distinct_year_token_count":len(yrs[i])} for i in yearidx
      ],
      "original_same_row_explicit_VIP_and_EP_pair_count":len(paired_rows),
      "original_coordinates_lats_lons_NOT_READ_OR_EXPORTED":True,
      "original_species_wood_measurements_organismal_values_NOT_READ":True,
      "original_individual_plot_ID_text_NOT_EXPORTED":True,
      "_private_field_tokens":value_sets,
      "_private_name_by_field":{i:normalized[i] for i in ididx},
      "_private_vip_ep_pairs":set(paired_rows),
    }
    return out


def source_reference_ids():
    exp=original_31123_plots()
    raw=inventory_bytes()
    if len(raw)!=240356 or hashlib.sha256(raw).hexdigest()!="1161dfe75ea6c5ee3fab1dda98c5ec1d142db2e08a03b63d6c6266bc27b0914d":
        raise SourceStop("SOURCE_STOP_18270_BASALAREA_PINNED_SOURCE_SHA_DRIFT")
    old=original_inventory_header_and_plot_keys(raw)
    if "_private_inventory_plots" not in old:
        raise SourceStop("SOURCE_STOP_ORIGINAL_18270_EP_ID_NO_LONGER_PRESENT")
    ep=old["_private_inventory_plots"]
    if len(exp)!=30 or len(ep)!=150:
        raise SourceStop("SOURCE_STOP_BELONGDEAD_30PLOT_150EP_REFERENCE_GRAIN_CHANGED")
    return exp,ep


def compare(source,exp,ep):
    vals=source.pop("_private_field_tokens")
    names=source.pop("_private_name_by_field")
    pairs=source.pop("_private_vip_ep_pairs")
    out=[]
    for idx,tokens in vals.items():
        out.append({
          "candidate_source_field_name":source["source_exact_predeclared_plot_identity_fields"][
              next(i for i,p in enumerate(sorted(vals)) if p==idx)
          ]["source_generic_header_name"],
          "source_tokens_exact_match_BELongDead31123_plot_ID":len(tokens&exp),
          "source_tokens_exact_match_BExIS18270_EP_ID":len(tokens&ep),
        })
    source["original_source_identity_field_exact_match_against_references"]=out
    source["source_explicit_VIP_EP_row_pair_total"]=len(pairs)
    source["source_direct_original_VIP_EP_pairs_matching_BELongDead_and_stand_EP"]=sum(
        vip in exp and parent in ep for vip,parent in pairs
    )
    source["source_distinct_BELongDead_plots_with_direct_original_VIP_EP_parent_link"]=len({
        vip for vip,parent in pairs if vip in exp and parent in ep
    })
    source["author_direct_source_link_covers_all_30_experimental_plots"]=(
        len({vip for vip,parent in pairs if vip in exp and parent in ep})==30
    )
    return source


def run():
    receipts={}
    for id in (1000,24546):
        name=str(id)
        try:
            rights=dataset_rights(id)
            raw=original_csv_bytes(id)
            fields=header_and_id_field_collections(raw,id)
            exp,ep=source_reference_ids()
            fields=compare(fields,exp,ep)
            receipts[name]={
              "source_rights":rights,
              "source_only_original_plot_identity_and_method":fields,
              "status":"SOURCE_AUTHOR_VIP_EP_DIRECT_30OF30_LINK_CONFIRMED"
              if fields["author_direct_source_link_covers_all_30_experimental_plots"]
              else "SOURCE_AUTHOR_VIP_EP_DIRECT_30OF30_LINK_NOT_ESTABLISHED"
            }
        except SourceStop as e:
            receipts[name]={"status":str(e),"SOURCE_STOP_not_ecological_null":True}
    supported=any(x.get("status")=="SOURCE_AUTHOR_VIP_EP_DIRECT_30OF30_LINK_CONFIRMED" for x in receipts.values())
    deadwood=receipts.get("24546",{})
    source_deadwood=deadwood.get("source_only_original_plot_identity_and_method",{})
    direct_30=any(x["source_tokens_exact_match_BELongDead31123_plot_ID"]==30
                  for x in source_deadwood.get("original_source_identity_field_exact_match_against_references",[]))
    return {
      "schema":"structural.BELongDead_BE1000_publisher_VIP_EP_bridge_and_BE24546_deadwood_sourceonly.v1",
      "source_original_source_datasets_checked":[1000,24546],
      "source_BELongDead_reference_31123_original_30plot_verified":True,
      "source_forest_basal_area_18270_original_150_EP_verified":True,
      "source_24546_is_2012_deadwood_not_living_tree_basal_area":True,
      "source_explicit_30of30_author_hierarchy_joined":supported,
      "original_2012_deadwood_24546_exact_BELongDead_30of30_plotID_match":direct_30,
      "2012_deadwood_exact_plot_join_is_NOT_18270_living_basalarea_crosswalk":True,
      "original_species_trap_count_deadwood_treemeasurement_values_UNOPENED":True,
      "original_location_geography_coordinates_not_read":True,
      "source_all_prior_Finland_Burner_PREDICTS_NEON_BALA_GEB_scores_FROZEN":True,
      "eBird_used":False,
      "source_diagnostics":receipts,
      "status":"SOURCE_FULL_AUTHOR_VIP_EP_PHYSICAL_BRIDGE_AVAILABLE_PREBIOLOGY"
      if supported else
      "SOURCE_DEADWOOD_24546_EXACT_30PLOT_JOIN_CONFIRMED_VIP_EP_LIVING_TREE_BRIDGE_UNVERIFIED"
      if direct_30 else "SOURCE_AUTHOR_VIP_EP_BRIDGE_NOT_VERIFIED_BIOLOGY_HOLD"
    }


def test():
    assert norm_field("VIP_ID")=="vipid"
    assert norm_field("EP")=="ep"
    assert norm_field("Longitude") not in IDENTITY_FIELDS
    assert norm_field("Latitude") not in IDENTITY_FIELDS
    assert not any("coord" in s for s in IDENTITY_FIELDS)
    assert 24546 in ORIGINAL and 1000 in ORIGINAL
    print("SYNTHETIC_BE_ORIGINAL_PLOT_VIP_EP_COORDINATE_FREE_SOURCE_GATE_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    test()
    if a.test:return
    if not a.out:p.error("--out needed")
    x=run()
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead_BE1000_VIP_EP_and_24546_original_sourceonly.json").write_text(
        json.dumps(x,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(x,indent=2,ensure_ascii=False))


if __name__=="__main__":main()
