#!/usr/bin/env python3
"""Original BELongDead 31123 BExIS publisher metadata documentation lexical gate.

No original /api/data request or beetle/wood measurements. Only public BExIS
dataset and metadata annotations; returns word-presence counters, not text.
This CANNOT itself resolve 15 ID aliases or experimental zero-capture effort.
"""
from __future__ import annotations

import argparse,hashlib,json,re,urllib.error,urllib.request
from collections import Counter
from pathlib import Path
from belongdead_bexis_13tree_original_source_gate import NoRedirect

ORIGINAL_URLS={
    "original_published_dataset":"https://www.bexis.uni-jena.de/api/dataset/31123",
    "original_author_version_metadata":"https://www.bexis.uni-jena.de/api/metadata/31123?tag=1.0",
}
METHOD_TERMS={
    "TrapID":r"\btrap\s*[_-]?\s*id\b",
    "Traptype":r"\btrap\s*[_-]?\s*type\b",
    "PlotID":r"\bplot\s*[_-]?\s*id\b",
    "TreeID":r"\btree\s*[_-]?\s*id\b",
    "TreeSpecies":r"\btree\s*[_-]?\s*species\b",
    "CollectionYear":r"\bcollection\s*[_-]?\s*year\b",
    "explicit_sampling_effort_text":r"\b(?:sampling effort|capture effort|sampling duration|sampling period|trap effort|trap deployment|number of traps)\b",
    "zero_capture_method_text":r"\b(?:zero captures?|no beetles? captured|trap with no beetles?|empty traps?)\b",
    "repeat_method_text":r"\b(?:trap relocation|resampling|re[- ]?sampling|repeated trap|replacement trap)\b",
    "alias_mapping_method_text":r"\b(?:alias(?:es)?|identifier mapping|trap[- ]?id correction|corrected trap|identifier correction)\b",
}
class SourceStop(Exception):pass

def fetch_meta(url):
    req=urllib.request.Request(url,headers={
        "User-Agent":"Structural-BExIS31123-author-trap-effort-metadata-only/1.0",
        "Accept":"application/json"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=25) as h:
            b=h.read(160001)
            status=h.status
            ctype=h.headers.get("Content-Type","")
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEXIS_METADATA_HTTP_"+str(ex.code)) from ex
    except (urllib.error.URLError,OSError,TimeoutError) as ex:
        raise SourceStop("SOURCE_STOP_BEXIS_METADATA_TRANSPORT_"+type(ex).__name__) from ex
    if status!=200 or len(b)>160000 or "json" not in ctype.lower():
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEXIS_METADATA_NOT_PUBLIC_JSON")
    try:parsed=json.loads(b.decode("utf-8"))
    except (ValueError,UnicodeError) as ex:
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEXIS_METADATA_JSON_PARSE") from ex
    return parsed,len(b),hashlib.sha256(b).hexdigest()

def all_metadata_strings(node,depth=0):
    if depth>24:return
    if isinstance(node,str):
        if len(node)<8000:
            yield node
    elif isinstance(node,dict):
        for k,v in node.items():
            if isinstance(k,str) and len(k)<100:
                yield k
            yield from all_metadata_strings(v,depth+1)
    elif isinstance(node,list):
        for x in node[:1500]:
            yield from all_metadata_strings(x,depth+1)

def scan():
    out={
       "schema":"structural.BELongDead31123_original_public_author_trap_effort_codebook_words_only.v1",
       "original_BExIS_dataset_ID":31123,
       "original_licensed_CC_BY4_confirmed_previously":True,
       "original_only_two_published_dataset_metadata_API_requests":True,
       "no_BExIS_original_species_wood_data_or_trap_rows_requested":True,
       "no_original_metadata_text_or_individual_sample_ID_exported":True,
       "prior_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_results_frozen":True,
       "eBird_used":False,
    }
    docs={}
    for name,url in ORIGINAL_URLS.items():
        data,bytesize,digest=fetch_meta(url)
        strings=list(all_metadata_strings(data))
        counts=Counter()
        for term,pattern in METHOD_TERMS.items():
            pattern=re.compile(pattern,re.I)
            counts[term]=sum(bool(pattern.search(text)) for text in strings)
        docs[name]={
          "original_source_metadata_byte_length":bytesize,
          "original_source_response_SHA256":digest,
          "original_publisher_json_string_or_key_fragments_scanned":len(strings),
          "publisher_metadata_lexical_method_term_fragment_counts":dict(counts),
          "lexical_match_NOT_a_validated_trap_occasion_or_ID_alias":True,
        }
    out["original_source_method_documentation_lexical_only"]=docs
    out["31124_15_exact_method_tuples_prior_source_mismatch_still_unresolved"]=True
    out["3546_stand_inventory_plot_link_prior_0of30_still_unresolved"]=True
    out["author_zero_capture_effort_frame_NOT_PROVED_FROM_METADATA_KEYWORDS"]=True
    out["status"]="AUTHOR_TRAP_EFFORT_AND_15ID_ALIAS_NOT_VERIFIED_NO_BIOLOGY"
    return out

def synthetic():
    b={"TrapID":"Unique identifier","Method":"zero captures and repeated trap relocation"}
    arr=list(all_metadata_strings(b))
    assert sum(bool(re.search(METHOD_TERMS["TrapID"],v,re.I)) for v in arr)==1
    assert sum(bool(re.search(METHOD_TERMS["zero_capture_method_text"],v,re.I)) for v in arr)==1
    assert len(ORIGINAL_URLS)==2
    print("SYNTHETIC_BEXIS31123_METADATA_ONLY_TRAP_CODEBOOK_LEXICAL_GATE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out required")
    try:r=scan()
    except SourceStop as ex:
        r={
          "schema":"structural.BELongDead31123_original_public_author_trap_effort_codebook_words_only.v1",
          "status":str(ex),
          "scientific_access_STOP_not_beetle_non_support":True,
          "original_beetle_population_score_not_reopened":True,
        }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead31123_publisher_metadata_trap_effort_codebook_lexical_only.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
