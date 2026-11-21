#!/usr/bin/env python3
"""Official BExIS source-only 13-host BELongDead dataset rights/access gate.

No raw beetle occurrence, log identity, forest plot, trap, tree measurement,
trait or abundance row is requested. Only published /api/dataset and
/api/metadata endpoints for exactly four known published dataset IDs.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOST="www.bexis.uni-jena.de"
ROOT="https://"+HOST
IDENTITIES={
    "long_deadwood_full_2010_2017":31123,
    "long_deadwood_complete_logs_subset_2010_2017":31124,
    "separate_43plot_2008_beetles":30981,
    "separate_43plot_2012_2017_wood":30979,
}
UA="Structural-research-original-BExIS2-source-metadata-only/1.0"
ALLOWED={"title","name","version","tag","doi","published","isPublic","public",
         "description","publicationdate","created","modified","license","accessrights",
         "licence","licensename","licensetype","rights","datasetid","id","status"}
CLASSIFY_LICENSE=re.compile(r"(?i)(cc[- ]?by[- ]?4\.0|creative commons attribution 4\.0|cc[- ]?0[- ]?1\.0|public domain)")
RIGHTS_FIELDS={"license","licence","licensename","licensetype","rights"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sanitized_license_recursive(obj,depth=0):
    """Inspect only public metadata field-value strings associated with rights."""
    if depth>5:return []
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            label=str(k).lower()
            if any(word in label for word in ("license","licence","copyright","rights")):
                if isinstance(v,str):
                    out.append(v[:200])
                elif isinstance(v,dict):
                    out.extend(sanitized_license_recursive(v,depth+1))
                    for vv in v.values():
                        if isinstance(vv,str) and CLASSIFY_LICENSE.search(vv):
                            out.append(vv[:200])
            elif isinstance(v,(dict,list)):
                out.extend(sanitized_license_recursive(v,depth+1))
    elif isinstance(obj,list):
        for v in obj[:50]:
            out.extend(sanitized_license_recursive(v,depth+1))
    return list(dict.fromkeys(out))[:8]


def metadata_get(path):
    if not re.fullmatch(r"/api/(dataset|metadata)/\d+(?:\?tag=1\.0)?",path):
        raise ValueError("SOURCE_STOP_ORIGINAL_DOCUMENTED_BEXIS_API_PATH_NOT_ALLOWED")
    url=ROOT+path
    req=urllib.request.Request(url,headers={
        "User-Agent":UA,
        "Accept":"application/json, application/xml;q=0.8,text/plain;q=0.5",
    })
    opener=urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req,timeout=18) as response:
            code=response.status
            ctype=response.headers.get("Content-Type","")
            raw=response.read(180001)
        if len(raw)>180000:
            return {"status":"SOURCE_STOP_DOCUMENTED_METADATA_GT180K",
                    "http_status":code}
        body=raw.decode("utf-8","replace")
        record={
            "status":"PUBLISHED_ORIGINAL_ENDPOINT_REACHABLE",
            "http_status":code,
            "content_type_category":(
                "json" if "json" in ctype.lower() else
                "xml" if "xml" in ctype.lower() else
                "html" if "html" in ctype.lower() else "other"),
            "body_byte_count":len(raw),
            "no_original_species_or_log_source_rows_requested":True,
        }
        if "json" in ctype.lower():
            try:
                data=json.loads(body)
            except ValueError:
                record["status"]="SOURCE_STOP_ORIGINAL_ENDPOINT_INVALID_JSON"
                return record
            records=data if isinstance(data,list) else [data]
            record["top_level_original_metadata_data_type"]=type(data).__name__
            if isinstance(data,dict):
                record["top_level_public_metadata_field_names"]=[
                    str(k) for k in data.keys()
                    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,45}",str(k))
                ][:40]
                # Do not export author source site labels or any biological data.
                for field in ("title","name","version","tag","doi","license","licence","publicationDate","accessRights"):
                    if field in data and isinstance(data[field],(str,int,float,bool)):
                        value=data[field]
                        if field.lower() in ("title","name","doi","license","licence","accessrights"):
                            record["original_public_"+field]=str(value)[:180]
                record["original_publisher_rights_disclosures"]=sanitized_license_recursive(data)
        elif "html" in ctype.lower():
            record["html_likely_login_portal"]=bool(re.search(
                r"(?i)name\s*=\s*['\"]password['\"]|sign\s*in|login",body))
            record["status"]="SOURCE_STOP_HTML_NOT_ORIGINAL_JSON_METADATA"
        elif "xml" in ctype.lower():
            # No XML payload exported, which may contain original metadata/sample codes.
            record["status"]="SOURCE_XML_METADATA_PRESENT_UNPARSED_LICENSE_NOT_VERIFIED"
        return record
    except urllib.error.HTTPError as exc:
        redirect=exc.headers.get("Location","") if exc.headers else ""
        p=urllib.parse.urlparse(redirect)
        return {
           "status":"SOURCE_ACCESS_HTTP_STOP" if exc.code in (401,403) else
                    "SOURCE_REDIRECT_OR_HTTP_STOP",
           "http_status":exc.code,
           "redirect_target_category":(
                "same_original_BExIS_host" if p.hostname==HOST else
                "other_host" if p.hostname else "none"),
        }
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return {"status":"SOURCE_TRANSPORT_STOP",
                "exception_class":type(exc).__name__}


def analyze():
    result={
        "schema":"structural.BELongDead_BExIS_13trees_30plots_4originalids_api_metadata_only.v1",
        "original_study_BELongDead_project":"Biodiversity Exploratories",
        "original_source_BE_public_project_catalogue":"https://www.biodiversity-exploratories.de/en/projects/core-project-7-land-use-above-ground-arthropod-diversity-and-arthropod-affected-processes/",
        "official_original_source_host":HOST,
        "reported_study_plots_from_published_design_NOT_INDEPENDENT_STUDIES":30,
        "reported_host_tree_log_taxa_from_original_design":13,
        "reported_original_exploratory_regions":3,
        "author_years_of_31123_and_31124":list(range(2010,2018)),
        "31124_is_subset_of_31123_not_new_independent_study":True,
        "30981_vs_30979_source_years_2008_vs_2012_2017_NOT_MATCHED":True,
        "original_organism_occurrence_or_wood_measurement_values_NOT_REQUESTED":True,
        "all_Finland_Burner_PREDICTS_NEON_BALA_GEB_frozen":True,
        "eBird_used":False,
        "original_dataset_endpoint_receipts":{},
    }
    for name,id in IDENTITIES.items():
        r1=metadata_get(f"/api/dataset/{id}")
        r2=metadata_get(f"/api/metadata/{id}?tag=1.0")
        result["original_dataset_endpoint_receipts"][name]={
            "original_catalogue_dataset_id":id,
            "dataset_endpoint":r1,
            "metadata_endpoint":r2,
        }
    rights=[]
    for name in ("long_deadwood_full_2010_2017","long_deadwood_complete_logs_subset_2010_2017"):
        r=result["original_dataset_endpoint_receipts"][name]
        for key in ("dataset_endpoint","metadata_endpoint"):
            x=r[key]
            rights.extend(x.get("original_publisher_rights_disclosures",[]))
            for field in ("original_public_license","original_public_licence","original_public_accessRights"):
                if field in x:rights.append(x[field])
    result["source_record_license_explicitly_recognized_CC_BY_or_CC0"]=any(
        CLASSIFY_LICENSE.search(v) for v in rights
    )
    metacheck=all(any(
        result["original_dataset_endpoint_receipts"][nm][field]["status"]=="PUBLISHED_ORIGINAL_ENDPOINT_REACHABLE"
        for field in ("dataset_endpoint","metadata_endpoint"))
        for nm in ("long_deadwood_full_2010_2017","long_deadwood_complete_logs_subset_2010_2017")
    )
    result["status"]=(
        "OFFICIAL_ORIGINAL_DATASET_METADATA_AND_LICENSE_VERIFIED"
        if metacheck and result["source_record_license_explicitly_recognized_CC_BY_or_CC0"]
        else "OFFICIAL_DATASET_PUBLIC_METADATA_BUT_LICENSE_NOT_VERIFIED"
        if metacheck
        else "SOURCE_TRANSPORT_OR_ACCESS_STOP_NO_BIOLOGICAL_VALUES"
    )
    result["no_original_BExIS_data_table_or_capture_rows_requested"]=True
    return result


def synthetic():
    assert CLASSIFY_LICENSE.search("CC-BY-4.0")
    assert not CLASSIFY_LICENSE.search("All rights reserved")
    try:
        metadata_get("/api/data/31123")
        raise AssertionError("unapproved original data endpoint allowed")
    except ValueError:
        pass
    assert len(IDENTITIES)==4
    print("SYNTHETIC_OFFICIAL_BEXIS_API_METADATA_ONLY_SOURCE_LICENSE_STOP_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out required")
    out=analyze()
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead_BExIS_13tree_30plot_original_dataset_API_sourceonly.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8"
    )
    print(json.dumps(out,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
