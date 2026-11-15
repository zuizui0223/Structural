#!/usr/bin/env python3
"""2026 99 forest plots original author Zenodo source/metadata ONLY.

Downloads two pinned files privately, examines Rmd code as unexecuted text,
and ingests metadata-only TSV emitted by base R RData object inspector.
No original beetle/wood/tree/niche cells/coefficients read by this script.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

RECORD="17927769"
MANIFEST={
 "Decline_Data.RData":(33531,"34312f823dafa60568fa0cd92926ee37"),
 "Analysis_Cascade_Decline_Salvage.Rmd":(80911,"083c1aef2e0acb519675f52dcbbf92f7")
}
CODE_TOKENS=("load","readrds","read.csv","read_csv","plot","tree","deadwood","trem",
             "beetle","trap","guild","mortality","salvage","decline","site","glm","sem")


class SourceStop(Exception):pass


def download(root:Path):
    root.mkdir(parents=True,exist_ok=True)
    results={}
    for name,(n,dig) in MANIFEST.items():
        url=f"https://zenodo.org/records/{RECORD}/files/{name}?download=1"
        req=urllib.request.Request(url,headers={"User-Agent":"Structural-original-method-sourceonly-2026/1.0"})
        try:
            with urllib.request.urlopen(req,timeout=45) as resp:
                content=resp.read(n+1)
                status=resp.status
        except urllib.error.HTTPError as ex:
            raise SourceStop("SOURCE_ACCESS_STOP_PUBLISHED_FILE_HTTP_"+str(ex.code)) from ex
        except (urllib.error.URLError,OSError,TimeoutError) as ex:
            raise SourceStop("SOURCE_ACCESS_STOP_TRANSPORT_"+type(ex).__name__) from ex
        if status!=200 or len(content)!=n:
            raise SourceStop("SOURCE_STOP_PUBLISHED_ORIGINAL_FILE_SIZE_CHANGED")
        if hashlib.md5(content).hexdigest()!=dig:
            raise SourceStop("SOURCE_STOP_PUBLISHED_ORIGINAL_FILE_DIGEST_DRIFT")
        (root/name).write_bytes(content)
        results[name]={"original_bytes_verified":n,"original_md5_pass":True}
    return results


def method_only(rmd_text:str):
    lines=rmd_text.splitlines()
    num_chunks=sum(bool(re.match(r"^\s*```\s*\{\s*[Rr]\b",line)) for line in lines)
    # Lexical only: never run old biological code or extract its coefficients.
    count={}
    lowered=rmd_text.lower()
    for needle in CODE_TOKENS:
        count[needle.replace(".","_")]=len(re.findall(r"\b"+re.escape(needle)+r"\b",lowered))
    return {
      "published_original_author_Rmd_text_lines":len(lines),
      "original_author_R_code_chunk_markers":num_chunks,
      "source_method_token_counts_NOT_original_biological_values":count,
      "source_author_code_not_run":True,
      "source_original_Rmarkdown_text_not_redistributed":True,
    }


def safe_tsv_schema(path:Path):
    if not path.is_file():raise SourceStop("SOURCE_STOP_RDATA_OBJECT_SCHEMA_TSV_MISSING")
    rows=path.read_text(encoding="utf-8").splitlines()
    if not rows or rows[0]!="object_slot\tclass\trows\tcolumns\tgeneric_fields":
        raise SourceStop("SOURCE_STOP_ORIGINAL_RDATA_OBJECT_SCHEMA_TSV_HEADER")
    res=[]
    safe_words=re.compile(r"^[A-Za-z0-9_.,+-]{0,400}$")
    for line in rows[1:]:
        fields=line.split("\t")
        if len(fields)!=5 or not fields[0].startswith("obj"):
            raise SourceStop("SOURCE_STOP_ORIGINAL_RDATA_SCHEMA_ROW")
        slot,clazz,n,cols,names=fields
        if not all(re.fullmatch(r"(?:[0-9]+|NA)",p) for p in (n,cols)):
            raise SourceStop("SOURCE_STOP_ORIGINAL_RDATA_SCHEMA_DIMENSION")
        if not safe_words.fullmatch(clazz) or not safe_words.fullmatch(names):
            raise SourceStop("SOURCE_STOP_SCHEMA_MIGHT_CONTAIN_AUTHOR_ROW_ID")
        res.append({
          "opaque_R_original_object_slot_not_name":slot,
          "source_original_object_class":clazz,
          "original_object_rows_if_rectangular":None if n=="NA" else int(n),
          "original_object_columns_if_rectangular":None if cols=="NA" else int(cols),
          "generic_named_method_fields_ONLY":[x for x in names.split(",") if x],
        })
    return res


def test():
    x=method_only("## METHODS\n```{r}\nplot(data); load('a.RData')\n```\n")
    assert x["original_author_R_code_chunk_markers"]==1
    assert x["source_method_token_counts_NOT_original_biological_values"]["load"]==1
    assert x["source_author_code_not_run"]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f=Path(td)/"schema.tsv"
        f.write_text("object_slot\tclass\trows\tcolumns\tgeneric_fields\nobj1\tdata.frame\t99\t13\tplot,year\n")
        a=safe_tsv_schema(f)
        assert len(a)==1 and a[0]["original_object_rows_if_rectangular"]==99
    print("SYNTHETIC_OFFICIAL_ARCHIVE_METHOD_ONLY_ORIGINAL_R_OBJECT_SCHEMA_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("test","download","finalize"),required=True)
    ap.add_argument("--private",type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--tsv",type=Path)
    a=ap.parse_args()
    test()
    if a.mode=="test":return
    if a.private is None or a.out is None:ap.error("--private --out required")
    a.out.mkdir(parents=True,exist_ok=True)
    try:
        if a.mode=="download":
            receipts=download(a.private)
            result={"status":"PUBLISHED_TWO_ORIGINAL_FILES_MD5_AND_SIZE_VERIFIED",
                    "source_original_Zenodo_DOI":"10.5281/zenodo.17927769",
                    "no_original_biological_values_opened":True,
                    "original_private_files_only":True,
                    "file_receipts":receipts}
            fn="source_only_download_receipt.json"
        else:
            if a.tsv is None:ap.error("--tsv required for finalize")
            result={
                "schema":"structural.frde99_Cours2026_original_RData_Rmd_method_only.v1",
                "original_zenodo_DOI":"10.5281/zenodo.17927769",
                "source_original_two_MD5_pinned_files":True,
                "author_99plots_methods_only_not_99_independent_studies":True,
                "author_fir_56_spruce_28_oak_15_method_height_confounded":True,
                "original_RData_opaque_object_schema":safe_tsv_schema(a.tsv),
                "original_Rmd_method_token_lexical_audit":method_only(
                    (a.private/"Analysis_Cascade_Decline_Salvage.Rmd").read_text(
                        encoding="utf-8-sig",errors="replace")),
                "source_original_plot_ID_beetle_observation_and_field_resource_row_JOIN_NOT_YET_ESTABLISHED":True,
                "no_original_observations_taxa_traits_abundances_or_SEM_results_read":True,
                "all_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_prior_effects_sealed":True,
                "eBird_used":False,
                "status":"RDATA_ORIGINAL_OBJECT_SHAPES_AUDITED_PREBIOLOGY_JOIN_NOT_ESTABLISHED",
            }
            fn="frde99_original_RData_method_sourceonly.json"
    except SourceStop as err:
        result={"schema":"structural.frde99_Cours2026_sourceonly_stop.v1",
                "status":str(err),
                "no_original_biological_effect_scored":True}
        fn="frde99_original_sourceonly_STOP.json"
    (a.out/fn).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
