#!/usr/bin/env python3
"""v1.339 HEAD-only original Galapagos ant archive availability and version audit.

Pensoft original Sep 2026 URL returned HTTP404 in v1.338. Test source
publisher URLs in a fixed order WITHOUT opening any ZIP or Event/Occurrence.
Do not assume Ecuador 2026 Jun source and Pensoft 2026 Sep are byte-identical.
"""
import argparse,json,urllib.request,urllib.error
from pathlib import Path

def probe(candidates,requester=None):
    result=[]
    for candidate in candidates:
        url=candidate["url"]
        if requester is None:
            req=urllib.request.Request(url,method="HEAD",
                headers={"User-Agent":"Structural-Galapagos-DwCA-HEAD-only-v1.339"})
            handler=urllib.request.urlopen
        else:
            req=url;handler=requester
        try:
            with handler(req,timeout=22) as response:
                status=response.status
                final=response.geturl()
                headers=response.headers
                result.append({
                    "source":candidate["source"],
                    "source_dataset_UUID":candidate["dataset_uuid"],
                    "original_version_tag":candidate["version_tag"],
                    "source_original_publisher_URL":url,
                    "HTTP_HEAD_status":status,
                    "effective_host_URL":final,
                    "HTTP_content_type":headers.get("Content-Type"),
                    "HTTP_content_length":headers.get("Content-Length"),
                    "HTTP_HEAD_source_accessible":200<=status<300,
                    "response_body_bytes_read":0
                })
        except (urllib.error.URLError,TimeoutError,OSError) as e:
            result.append({
                "source":candidate["source"],
                "source_dataset_UUID":candidate["dataset_uuid"],
                "original_version_tag":candidate["version_tag"],
                "source_original_publisher_URL":url,
                "HTTP_HEAD_source_accessible":False,
                "error_type":type(e).__name__,
                "HTTP_error_status":getattr(e,"code",None),
                "response_body_bytes_read":0
            })
    return result

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--contract",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    x=a.parse_args()
    c=json.loads(x.contract.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.galapagos_ant_original_archive_transport.v1_339"
        or c.get("status")!="FIXED_ALTERNATIVE_PUBLISHER_ARCHIVE_PROBE_HEAD_ONLY_NO_SOURCE_DATA_ROWS"
        or len(c.get("candidates",[]))!=3
        or not c["firewall"]["previous_v1_338_Pensoft_original_url_failed"]):
        raise ValueError("Original publisher and no-Galapagos-source read protocol not frozen")
    rows=probe(c["candidates"])
    good=[z["source"] for z in rows if z["HTTP_HEAD_source_accessible"]]
    r={
        "schema":"structural.galapagos_ant_archive_traffic_result.v1_339",
        "status":"ORIGINAL_ARCHIVE_HEAD_AVAILABLE_VERSION_NOT_YET_ADMITTED" if good
                 else "SOURCE_ACCESS_TRANSPORT_STOP_NO_ORIGINAL_BIOLOGICAL_DATA",
        "tested_exact_original_source_registration_count":len(rows),
        "accessible_source_registration_labels":good,
        "source_publisher_endpoint_checks":rows,
        "source_archive_bodies_read":0,"original_Event_rows_read":0,
        "original_Occurrence_rows_read":0,
        "cannot_infer_byte_identical_original_versions":True,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(r,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({
        "status":r["status"],
        "endpoint_results":[{k:v.get(k) for k in ("source","HTTP_HEAD_status","HTTP_error_status","HTTP_content_length","HTTP_content_type")}
                             for v in rows],
        "original_biological_rows_opened":0
    },sort_keys=True))
if __name__=="__main__":main()
