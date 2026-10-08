#!/usr/bin/env python3
"""Metadata-only HTTP transport inspection for the original nine Hébert Dryad CSVs.

May fetch the publisher's HTML landing page; NEVER GET, range-read or parse any
CSV or its species/island values. File probes are HTTP HEAD only.
"""
from __future__ import annotations
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib import request, parse, error
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"development/hebert_transport_preflight_contract_v1_198.json"
FROZEN=ROOT/"development/global_mammals_independent_checklist_preintake_v1_188.json"

class Stop(RuntimeError):pass

def permitted(url:str)->bool:
    p=parse.urlsplit(url)
    if p.scheme!="https" or p.username is not None or p.password is not None:return False
    h=(p.hostname or "").lower()
    return h=="datadryad.org" or h.endswith(".datadryad.org") or h=="s3.amazonaws.com" or h.endswith(".amazonaws.com")

def scrub(url:str)->str:
    p=parse.urlsplit(url)
    return parse.urlunsplit((p.scheme,p.netloc,p.path,"",""))

class DownloadAnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items=[]
        self.inside=False
        self.href=None
        self.label=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            at=dict(attrs)
            self.inside=True
            self.href=at.get("href")
            self.label=[]
    def handle_data(self,data):
        if self.inside:self.label.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.inside:
            if self.href:self.items.append((" ".join("".join(self.label).split()),self.href))
            self.inside=False;self.href=None;self.label=[]

class RedirectGuard(request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not permitted(newurl):raise Stop("redirect host not approved")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch_landing(url):
    if not permitted(url):raise Stop("unsafe landing URL")
    opener=request.build_opener(RedirectGuard())
    r=request.Request(url,headers={"User-Agent":"Structural-Hébert-transport-metadata-only-v1.198","Accept":"text/html"})
    with opener.open(r,timeout=25) as resp:
        if "html" not in resp.headers.get("Content-Type","").lower():
            raise Stop("landing response not HTML")
        data=resp.read(2_000_001)
        if len(data)>2_000_000:raise Stop("landing HTML exceeds cap")
        final=resp.url
    return data.decode("utf-8","replace"),scrub(final)

def named_links(html,landing,expected_names):
    parser=DownloadAnchorParser();parser.feed(html)
    d=defaultdict(list)
    for label,href in parser.items:
        if label in expected_names:
            url=parse.urljoin(landing,href)
            if permitted(url) and url not in d[label]:d[label].append(url)
    return dict(d)

def probe_head(url):
    if not permitted(url):return {"state":"UNSAFE_URL"}
    opener=request.build_opener(RedirectGuard())
    req=request.Request(url,method="HEAD",headers={"User-Agent":"Structural-Hébert-transport-metadata-only-v1.198","Accept":"text/csv,application/octet-stream"})
    try:
        with opener.open(req,timeout=13) as resp:
            final=resp.url
            if not permitted(final):return {"state":"UNSAFE_REDIRECT"}
            ctype=resp.headers.get("Content-Type","").split(";")[0].lower()
            length=resp.headers.get("Content-Length")
            size=int(length) if length is not None and str(length).isdigit() else None
            disp=resp.headers.get("Content-Disposition","")
            if ctype in ("text/html","application/xhtml+xml") or (size is not None and (size<12 or size>200000)):
                state="INVALID_FILE_METADATA"
            else:
                state="HEAD_OK_FILE_IDENTITY_UNVERIFIED"
            return {"state":state,"http_status":int(resp.status),"content_type":ctype,
                    "content_length":size,"content_disposition_filename_only":disp.split("filename=")[-1].strip("'\" ")[:100] if "filename=" in disp else None,
                    "final_public_url":scrub(final)}
    except (error.HTTPError,error.URLError,TimeoutError,OSError,Stop) as exc:
        return {"state":"HEAD_FAILED","error_class":type(exc).__name__,
                "http_status":getattr(exc,"code",None)}

def preflight(c,source,landing_html,landing_final,head_func=probe_head):
    if c["schema"]!="structural.hebert_transport_preflight.v1_198":raise Stop("contract drift")
    if source["source"]["doi"]!=c["dataset_doi"]:raise Stop("source DOI drift")
    original=source["files"]
    if len(original)!=9 or len({f["name"] for f in original})!=9:raise Stop("frozen file list drift")
    if not all(f["name"].lower().endswith(".csv") for f in original):raise Stop("non-CSV item")
    expected={f["name"] for f in original}
    links=named_links(landing_html,landing_final,expected)
    out=[];ok=0
    for f in original:
        name=f["name"];fid=f["id"]
        candidates=[
            c["candidate_urls"]["previous_frozen_api_template"].format(id=fid),
            c["candidate_urls"]["previous_frozen_fallback_template"].format(id=fid)
        ]+links.get(name,[])
        dedup=list(dict.fromkeys(candidates));success=False;attempts=[]
        for url in dedup:
            result=head_func(url)
            attempts.append({"route":"live_landing_exact_filename" if url in links.get(name,[]) else "frozen_old_id",
                             "url":scrub(url),**result})
            if result.get("state")=="HEAD_OK_FILE_IDENTITY_UNVERIFIED":success=True
        out.append({"file":name,"frozen_file_id":fid,"exact_visible_download_link_in_landing":bool(links.get(name)),
                    "head_candidate_success":success,"attempts":attempts})
        ok+=int(success)
    status= "HEAD_CANDIDATE_ALL_9" if ok==9 else "HEAD_PARTIAL" if ok>0 else "NO_HEAD_CANDIDATE"
    return {
       "schema":"structural.hebert_transport_preflight_result.v1_198",
       "status":status,
       "dataset_doi":c["dataset_doi"],
       "landing_page_verified":True,
       "landing_url":scrub(landing_final),
       "frozen_csv_names":sorted(expected),
       "frozen_csv_count":len(original),
       "csv_head_candidates":ok,
       "files":out,
       "CSV_body_bytes_read":0,"species_or_island_header_values_decoded":0,
       "island_species_binary_values_decoded":0,"original_mammal_heldout_values_opened":0,
       "external_ecological_score_produced":False,
       "downstream_header_projection_authorized":False,
       "eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=CONTRACT)
    ap.add_argument("--source",type=Path,default=FROZEN)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        source=json.loads(a.source.read_text())
        html,final=fetch_landing(c["landing_url"])
        if c["dataset_doi"] not in html:raise Stop("landing DOI not found")
        out=preflight(c,source,html,final)
        exitcode=0
    except (OSError,ValueError,KeyError,Stop,json.JSONDecodeError) as e:
        out={"schema":"structural.hebert_transport_preflight_result.v1_198",
             "status":"LANDING_UNAVAILABLE","reason_class":type(e).__name__,
             "CSV_body_bytes_read":0,"species_or_island_header_values_decoded":0,
             "island_species_binary_values_decoded":0,"original_mammal_heldout_values_opened":0,
             "external_ecological_score_produced":False,"downstream_header_projection_authorized":False,
             "eBird_used":False}
        exitcode=0  # terminal metadata receipt, not an ecology failure
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps(out,sort_keys=True,ensure_ascii=False))
    return exitcode
if __name__=="__main__":raise SystemExit(main())
