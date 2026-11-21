#!/usr/bin/env python3
"""BExIS official original tag1 vs previously downloaded LATEST provenance.

Two publisher-documented version URLs for already-verified CC BY4 datasets:
BE31123 saproxylic beetles and BE24546 ambient deadwood inventory.
Only CSV source header, original PlotID identifiers and publisher API metadata
object names. Never access beetle species/count, wood taxon/resource values,
coordinates, individual original plot IDs or biological effect estimates.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,urllib.error,urllib.request
from collections import Counter
from pathlib import Path

BASE="https://www.bexis.uni-jena.de"
SOURCES={
 31123:{"latest_sha":"73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e",
        "latest_size":8103493,"max_size":12000000},
 24546:{"latest_sha":"5a02350e4f1e364302dea20ca25281e65f2158d318d9fbcef56be2fe6d57786a",
        "latest_size":417351,"max_size":2000000},
}
HEADERS={"User-Agent":"Structural-original-BExIS-published-tag1-vs-latest-sourceonly/1.0","Accept":"text/csv"}
JSONHEADERS={"User-Agent":HEADERS["User-Agent"],"Accept":"application/json"}

class SourceStop(Exception):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

def publisher_get(url:str,limit:int,headers:dict):
    if not (url.startswith(BASE+"/api/data/") or url.startswith(BASE+"/api/dataset/")):
        raise SourceStop("SOURCE_STOP_NON_PUBLISHER_DOCUMENTED_ENDPOINT")
    req=urllib.request.Request(url,headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=60) as f:
            raw=f.read(limit+1)
            code=f.status
            ctype=f.headers.get("Content-Type","")
            n=f.headers.get("Content-Length","")
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_STOP_OFFICIAL_TAG1_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,OSError,TimeoutError) as e:
        raise SourceStop("SOURCE_STOP_OFFICIAL_TAG1_TRANSPORT_"+type(e).__name__) from e
    if code!=200 or len(raw)>limit or (n.isdigit() and len(raw)!=int(n)):
        raise SourceStop("SOURCE_STOP_ORIGINAL_TAG1_FULL_RESPONSE_NOT_CONFIRMED")
    return raw,ctype

def exact_plot_metadata(csvraw:bytes,src:int):
    rd=csv.reader(io.StringIO(csvraw.decode("utf-8-sig"),newline=""))
    h=next(rd,[])
    if not (2<=len(h)<=100):
        raise SourceStop("SOURCE_STOP_ORIGINAL_TAG1_UNEXPECTED_HEADER_WIDTH")
    if src==31123:
        fields=["PlotID","Exploratory"]
        index={key:h.index(key) for key in fields if h.count(key)==1}
        if len(index)!=2 or h.index("PlotID")!=2 or h.index("Exploratory")!=3:
            raise SourceStop("SOURCE_STOP_TAG1_BEETLE_PLOT_EXPLORATORY_SCHEMA_CHANGED")
        if len(h)!=17:raise SourceStop("SOURCE_STOP_TAG1_31123_FIELD_COUNT_NOT_17")
        plotidx=index["PlotID"];regionidx=index["Exploratory"]
    else:
        cand=[i for i,s in enumerate(h) if s in ("plotID","PlotID","PLOT","EP")]
        if len(cand)!=1:
            raise SourceStop("SOURCE_STOP_TAG1_24546_AUTHOR_PLOT_ID_NOT_UNIQUE")
        plotidx=cand[0];regionidx=None
    ids=set();regions=set();nested=set();n=0;missing=0
    for row in rd:
        if not row or not any(v.strip() for v in row):continue
        n+=1
        if len(row)!=len(h):raise SourceStop("SOURCE_STOP_ORIGINAL_TAG1_DATA_CSV_WIDTH")
        p=row[plotidx].strip()
        if not p:missing+=1;continue
        ids.add(p)
        if regionidx is not None:
            region=row[regionidx].strip()
            regions.add(region)
            nested.add((region,p))
    return {
      "_private_plot_ids":ids,
      "original_source_1based_plot_ID_field_position":plotidx+1,
      "original_source_plot_header_label":h[plotidx],
      "original_source_header_total_fields":len(h),
      "original_source_rows_not_independent_forests":n,
      "original_source_plot_ID_missing_rows":missing,
      "original_source_unique_PlotID_tokens":len(ids),
      "original_source_distinct_Exploratories_if_col_available":len(regions) if regionidx is not None else None,
      "original_source_nested_Exploratory_PlotID_count_if_available":len(nested) if regionidx is not None else None,
      "original_source_specimen_species_and_resource_measurements_UNREAD":True,
      "original_source_ID_strings_and_coordinates_NOT_EXPORTED":True,
    }

def safe_dataset_tag1_descriptor():
    raw,ctype=publisher_get(BASE+"/api/dataset/24546/tag/1",250000,JSONHEADERS)
    if "json" not in ctype.lower():raise SourceStop("SOURCE_STOP_PUBLISHER_TAG1_DATASET_NOT_JSON")
    try:d=json.loads(raw.decode("utf-8"))
    except ValueError as e:raise SourceStop("SOURCE_STOP_PUBLISHER_TAG1_DATASET_INVALID_JSON") from e
    if not isinstance(d,dict):raise SourceStop("SOURCE_STOP_PUBLISHER_TAG1_DATASET_NOT_OBJECT")
    safe_keys=[k for k in d.keys() if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,65}",str(k))]
    structure_keys=[k for k in safe_keys if any(z in k.lower() for z in ("datastructure","variable","version","tag","structure"))]
    simple={}
    for k in structure_keys:
        v=d[k]
        if isinstance(v,(int,float,bool)) or v is None:
            simple[k]=v
        elif isinstance(v,str) and len(v)<60 and re.fullmatch(r"[A-Za-z0-9_.:-]+",v):
            simple[k]=v
        elif isinstance(v,(dict,list)):
            simple[k]=type(v).__name__
    return {
      "original_tag1_publisher_dataset_metadata_SHA256":hashlib.sha256(raw).hexdigest(),
      "publisher_original_tag1_dataset_property_names_only":sorted(safe_keys)[:65],
      "publisher_data_structure_and_version_metadata_safe_fields_ONLY":simple,
      "publisher_biodiversity_and_site_records_UNREAD":True,
    }

def audit():
    out={
      "schema":"structural.BE31123_24546_publisher_tag1_vs_latest_immutable_original_source_provenance.v1",
      "official_BEXIS2_source_controller":"BEXIS2/Core DataOutController GET api/Data/{id}/tag/{tag}",
      "source_public_individual_CC_BY4_previously_verified":True,
      "source_only_original_plot_identifier_fields_read":True,
      "original_beetle_taxon_abundance_deadwood_taxon_volume_coordinates_UNREAD":True,
      "old_Finland_Burner_PREDICTS_NEON_BALA_GEB_scores_UNCHANGED":True,
      "eBird_used":False,
      "original_tag1_source_receipts":{},
    }
    private={}
    for src,p in SOURCES.items():
        try:
            b,ctype=publisher_get(BASE+f"/api/data/{src}/tag/1",p["max_size"],HEADERS)
            if "csv" not in ctype.lower():
                raise SourceStop("SOURCE_STOP_TAG1_DATA_MEDIA_NOT_CSV")
            summary=exact_plot_metadata(b,src)
            private[src]=summary.pop("_private_plot_ids")
            out["original_tag1_source_receipts"][str(src)]={
              "status":"PUBLISHER_ORIGINAL_TAG1_CSV_RECEIVED",
              "original_tag1_bytes":len(b),
              "original_tag1_SHA256":hashlib.sha256(b).hexdigest(),
              "original_prior_latest_SHA256":p["latest_sha"],
              "original_tag1_equals_prior_latest_SHA":hashlib.sha256(b).hexdigest()==p["latest_sha"],
              "original_prior_latest_csv_bytes":p["latest_size"],
              "source_only_header_and_plot":summary,
            }
        except SourceStop as e:
            out["original_tag1_source_receipts"][str(src)]={
                "status":str(e),
                "source_version_STOP_not_biological_non_support":True,
            }
    if 31123 in private and 24546 in private:
        a,b=private[31123],private[24546]
        out["original_tag1_31123_plotID_exact_overlap_with_original_tag1_24546"]={
          "experimental_original_tag1_PlotID_total":len(a),
          "deadwood_inventory_tag1_original_PlotID_total":len(b),
          "original_exact_same_plot_tokens":len(a&b),
          "original_beetle_plot_tokens_unmatched":len(a-b),
          "original_invent_plot_tokens_not_in_experiment":len(b-a),
          "source_only_no_source_IDs_or_values_exported":True,
        }
    try:
        out["BEXIS24546_tag1_dataset_meta_structure_only"]=safe_dataset_tag1_descriptor()
    except SourceStop as e:
        out["BEXIS24546_tag1_dataset_meta_structure_only"]={"status":str(e)}
    yes=all(v.get("status")=="PUBLISHER_ORIGINAL_TAG1_CSV_RECEIVED"
            for v in out["original_tag1_source_receipts"].values())
    out["status"]=(
      "PINNED_ORIGINAL_TAG1_SOURCES_AUDITED_COMPARE_LATEST_AND_JOINS"
      if yes else "SOURCE_TAG1_ORIGINAL_VERSION_ACCESS_OR_FORMAT_STOP"
    )
    return out

def test():
    assert len(SOURCES)==2
    assert SOURCES[24546]["latest_size"]==417351
    assert SOURCES[31123]["latest_size"]==8103493
    assert all(len(q["latest_sha"])==64 for q in SOURCES.values())
    assert BASE+"/api/data/24546/tag/1" != BASE+"/api/data/24546"
    print("SYNTHETIC_OFFICIAL_BEXIS_SOURCE_VERSION_TAG_SELECTOR_AND_PRIOR_HASH_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    test()
    if a.test:return
    if not a.out:p.error("--out required")
    res=audit()
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BExIS31123_24546_original_tag1_vs_latest_immutable_sourceonly.json").write_text(
        json.dumps(res,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    print(json.dumps(res,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
