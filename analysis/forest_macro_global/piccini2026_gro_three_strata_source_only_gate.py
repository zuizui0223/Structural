#!/usr/bin/env python3
"""Piccini 2026 / Wildermuth 2024 GRO.data metadata-only legitimate source gate.
Do not read occurrence, abundance, habitat, plot or tree-resource source values.
Each DOI gets one public DataCite GET and one official GRO Dataverse GET.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

DOIS=("10.25625/H8EMJS","10.25625/5AWJBC")
HOST="https://data.goettingen-research-online.de"
MAX_BYTES=2_000_000
HEADERS={"User-Agent":"Structural-source-provenance-readonly/1.0",
         "Accept":"application/json"}

class SourceStop(RuntimeError):
    pass

def get_public_json(url):
    """One GET. Return a safe status plus PRIVATE parsed JSON; no retries."""
    request=urllib.request.Request(url,headers=HEADERS,method="GET")
    try:
        with urllib.request.urlopen(request,timeout=24) as response:
            http=response.status
            data=response.read(MAX_BYTES+1)
    except urllib.error.HTTPError as e:
        return {"status":"HTTP_ACCESS_STOP" if e.code in (401,403)
                else "HTTP_UNAVAILABLE","http_code":e.code},None
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        return {"status":"TRANSPORT_STOP","error_class":type(e).__name__},None
    if http!=200:
        return {"status":"HTTP_UNAVAILABLE","http_code":http},None
    if len(data)>MAX_BYTES:
        return {"status":"SOURCE_JSON_OVERSIZE_STOP"},None
    try:
        value=json.loads(data.decode("utf-8"))
    except (ValueError,UnicodeError):
        return {"status":"SOURCE_JSON_INVALID_STOP"},None
    if not isinstance(value,dict):
        return {"status":"SOURCE_JSON_NOT_OBJECT_STOP"},None
    return {"status":"HTTP_200_JSON","bytes_received":len(data)},value

def datacite_only(doi,obj):
    root=obj.get("data") if isinstance(obj,dict) else None
    if not isinstance(root,dict):
        raise SourceStop("DATACITE_DATA_MISSING")
    attrs=root.get("attributes",{})
    if not isinstance(attrs,dict):
        raise SourceStop("DATACITE_ATTRIBUTES_MISSING")
    source_doi=str(root.get("id",""))
    title=attrs.get("titles",[])
    if not isinstance(title,list): title=[]
    has_title=any(bool(x.get("title")) for x in title if isinstance(x,dict))
    publisher=attrs.get("publisher")
    return {
       "published_DOI_exact_match":source_doi.casefold()==doi.casefold(),
       "publisher_metadata_present":bool(publisher),
       "title_metadata_present":has_title,
       "published_publication_year_metadata_present":isinstance(attrs.get("publicationYear"),int),
       "abstract_or_source_biology_was_NOT_read":True,
    }

def gro_only(doi,obj):
    if obj.get("status")!="OK":
        raise SourceStop("GRO_DATAVERSE_JSON_STATUS_NOT_OK")
    data=obj.get("data",{})
    if not isinstance(data,dict):
        raise SourceStop("GRO_DATA_NOT_OBJECT")
    version=data.get("latestVersion") or {}
    if not isinstance(version,dict):
        raise SourceStop("GRO_LATEST_VERSION_NOT_OBJECT")
    # Dataverse versions differ: the DOI may appear in full-form fields,
    # latestVersion.datasetPersistentId, or protocol+authority+identifier.
    # Never qualify a record without an exact native DOI match.
    candidates=[str(x) for x in (
        data.get("globalId"),data.get("persistentId"),
        version.get("datasetPersistentId")) if isinstance(x,str) and x]
    if all(isinstance(data.get(k),str) and data[k] for k in (
            "protocol","authority","identifier")):
        candidates.append(data["protocol"]+":"+data["authority"]+"/"+data["identifier"])
    doi_matches=[x.casefold() in ("doi:"+doi.casefold(),doi.casefold())
                 for x in candidates]
    files=version.get("files")
    if files is None: files=[]
    if not isinstance(files,list):
        raise SourceStop("GRO_FILES_NOT_LIST")
    formats={}
    nrestricted=0
    size_total=0
    for f in files:
        if not isinstance(f,dict):raise SourceStop("GRO_FILE_RECORD_MALFORMED")
        df=f.get("dataFile") or {}
        if not isinstance(df,dict):raise SourceStop("GRO_FILE_METADATA_MALFORMED")
        ct=str(df.get("contentType","unknown")).casefold()
        category="xlsx" if "spreadsheet" in ct or "excel" in ct else (
          "text" if ct.startswith("text/") else ("zip" if "zip" in ct else "other"))
        formats[category]=formats.get(category,0)+1
        nrestricted+=bool(f.get("restricted",False))
        size=df.get("filesize")
        if isinstance(size,int) and size>=0:
            size_total+=size
    return {
       "source_DOI_exact_match":any(doi_matches),
       "source_DOI_identity_field_present":len(candidates)>0,
       "source_DOI_identity_candidate_count":len(candidates),
       "version_state":str(version.get("versionState","UNCONFIRMED"))[:24],
       "published_version_exists":version.get("versionState")=="RELEASED",
       "metadata_file_record_count":len(files),
       "metadata_restricted_file_count":nrestricted,
       "metadata_file_format_counts":formats,
       "metadata_files_total_bytes_advertised":size_total,
       "file_content_downloaded":False,
       "file_paths_or_source_site_names_exported":False,
       "source_sampling_site_stratum_crosswalk_NOT_ESTABLISHED":True,
    }

def inspect_one(doi):
    url_dc="https://api.datacite.org/dois/"+urllib.parse.quote(doi,safe="/")
    url_gro=HOST+"/api/datasets/:persistentId/?" + urllib.parse.urlencode({"persistentId":"doi:"+doi})
    dc_status,dc_obj=get_public_json(url_dc)
    gro_status,gro_obj=get_public_json(url_gro)
    result={"doi":doi,
            "datacite_request":dc_status,
            "gro_dataverse_metadata_request":gro_status,
            "original_species_trap_wood_values_UNOPENED":True,
            "no_author_plot_IDs_or_raw_file_bytes_saved":True,
            "no_prior_Structural_biological_score_changed":True}
    if dc_obj is not None:
        try: result["bibliographic_QA"]=datacite_only(doi,dc_obj)
        except SourceStop as e:result["bibliographic_status"]=str(e)
    if gro_obj is not None:
        try:result["official_dataverse_QA"]=gro_only(doi,gro_obj)
        except SourceStop as e:result["official_dataverse_status"]=str(e)
    if gro_status["status"]=="HTTP_ACCESS_STOP":
        result["status"]="ORIGINAL_GRO_METADATA_ACCESS_STOP_NOT_BIOLOGICAL_NULL"
    elif gro_obj is None:
        result["status"]="ORIGINAL_GRO_METADATA_UNAVAILABLE_NOT_BIOLOGICAL_NULL"
    elif not all(result.get("bibliographic_QA",{}).get(k,False) for k in (
          "published_DOI_exact_match","publisher_metadata_present","title_metadata_present",
          "published_publication_year_metadata_present")):
        result["status"]="PUBLIC_DATACITE_BIBLIOGRAPHIC_CROSSCHECK_STOP"
    elif not result.get("official_dataverse_QA",{}).get("source_DOI_exact_match"):
        result["status"]="ORIGINAL_GRO_SOURCE_DOI_IDENTITY_STOP"
    elif not result["official_dataverse_QA"]["published_version_exists"]:
        result["status"]="ORIGINAL_GRO_PUBLISHED_RELEASE_NOT_ESTABLISHED"
    elif result["official_dataverse_QA"]["metadata_file_record_count"]==0:
        result["status"]="ORIGINAL_GRO_SOURCE_FILE_METADATA_EMPTY"
    else:
        result["status"]="ORIGINAL_GRO_METADATA_QUALIFIED_FILES_NOT_DOWNLOADED"
    return result

def known_truth():
    doi=DOIS[0]
    assert datacite_only(doi,{"data":{"id":doi.lower(),"attributes":{
       "publisher":"GRO.data","titles":[{"title":"Original forest beetle data"}],
       "publicationYear":2026}}})["published_DOI_exact_match"]
    good={"status":"OK","data":{"globalId":"doi:"+doi,"latestVersion":{
       "versionState":"RELEASED","files":[
       {"restricted":False,"dataFile":{"contentType":"text/tab-separated-values","filesize":2100}},
       {"restricted":True,"dataFile":{"contentType":"application/zip","filesize":3000}},
       ]}}}
    k=gro_only(doi,good)
    assert k["source_DOI_exact_match"] and k["metadata_file_record_count"]==2
    assert k["metadata_restricted_file_count"]==1
    assert k["metadata_files_total_bytes_advertised"]==5100
    assert k["file_content_downloaded"] is False
    assert gro_only(doi,{"status":"OK","data":{
       "protocol":"doi","authority":"10.25625","identifier":"H8EMJS",
       "latestVersion":{"versionState":"RELEASED","files":[]}}})["source_DOI_exact_match"]
    assert gro_only(doi,{"status":"OK","data":{
       "latestVersion":{"datasetPersistentId":"doi:10.25625/H8EMJS",
       "versionState":"RELEASED","files":[]}}})["source_DOI_exact_match"]
    assert not gro_only(doi,{"status":"OK","data":{
       "protocol":"doi","authority":"10.25625","identifier":"WRONG",
       "latestVersion":{"versionState":"RELEASED","files":[]}}})["source_DOI_exact_match"]
    assert not gro_only(doi,{"status":"OK","data":{"globalId":"doi:BAD",
        "latestVersion":{"versionState":"RELEASED","files":[]}}})["source_DOI_exact_match"]
    assert all(d.count("/")==1 for d in DOIS)
    print("SYNTHETIC_DATACITE_GRO_METADATA_ONLY_POSITIVE_MISMATCH_RESTRICTED_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:ap.error("--out required")
    results=[inspect_one(d) for d in DOIS]
    summary={
      "schema":"structural.Piccini2026_three_stratum_gro_original_source_metadata_gate.v1",
      "prebiology_protocol":"docs/FOREST_BEETLE_PICCINI2026_THREESTRATA_SOURCE_ONLY_PRESPEC_20261116.md",
      "source_publication_DOI":"10.1111/1365-2664.70472",
      "source_original_DOIs":list(DOIS),
      "source_results":results,
      "NO_original_species_or_forest_numerical_biology_opened":True,
      "NO_40_nominal_stands_claimed_as_independent_sites":True,
      "sources_not_counted_as_independent_field_replications":True,
      "Thai_Finland_PREDICTS_NEON_BALA_GEB_original_scorers_SEALED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Piccini2026_GRO_source_metadata_only.json").write_text(
       json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
