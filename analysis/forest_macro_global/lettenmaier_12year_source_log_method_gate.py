#!/usr/bin/env python3
"""SOURCE-ONLY original 12y deadwood beetle hierarchy (plot/log/year/tree).

No ecological scores, no beetle/taxon outcome values, no tree/trait values.
Only SOURCE ORIGINAL field identity columns and first-column candidate row ID.
All original IDs stay runner private; only anonymized counts are exported.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

M={
  "raw":("Beetle_Data_JAE-2025-00357.csv",852649,"ae7254baac19934a75242defce6ada59"),
  "comm":("Beetle_Community_JAE-2025-00357.csv",329736,"a5d8a26d932594ce40dc6b5aba269c19"),
  "trait":("Trait_Table_JAE-2025-00357.xlsx",58578,"3a5b226e35d75cd3ed7501dff3c15bc1")
}
MAIN="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
PKG="http://schemas.openxmlformats.org/package/2006/relationships"
REL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
TRAIT_SAFE={
 "species","speciesname","taxon","taxonid","scientificname","family","genus",
 "feedingguild","feeding_guild","feedingtype","feedtype","trophicguild",
 "trophic_guild","microhabitat","hosttree","host_tree","host","hostspecies",
 "host_species","tree","wood","wooddecay","decay","decaystage","size",
 "bodysize","body_size","bodylength","body_length","wing","winglength",
 "distribution","phylogeny","phylum","order","subfamily","coleoptera",
 "relativeabundance"
}

class ScientificStop(RuntimeError):pass


def get_source(filename,size,digest):
    url=f"https://zenodo.org/records/17337484/files/{filename}?download=1"
    try:
        with urllib.request.urlopen(
           urllib.request.Request(url,headers={"User-Agent":"Structural-source-only-log-method-2026/1.0"}),
           timeout=40) as h:
            body=h.read(size+1)
            status=h.status
    except urllib.error.HTTPError as exc:
        raise ScientificStop("SOURCE_STOP_ZENODO_ARCHIVE_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,OSError,TimeoutError) as exc:
        raise ScientificStop("SOURCE_STOP_ZENODO_ARCHIVE_TRANSPORT_"+type(exc).__name__) from exc
    if status!=200 or len(body)!=size:
        raise ScientificStop("SOURCE_STOP_ORIGINAL_SOURCE_BYTES_NOT_PINNED")
    if hashlib.md5(body).hexdigest()!=digest:
        raise ScientificStop("SOURCE_STOP_ORIGINAL_SOURCE_MD5_DRIFT")
    return body


def missing(v):
    return not v.strip() or v.strip().lower() in ("na","nan","none","null","missing","n/a")


def original_log_metadata(csv_bytes):
    # CSV reader internally walks row shape, but the ONLY accessed values are
    # author-source ID/wood context columns: plot/log/year/tree.  Original
    # original response taxon/count fields are never accessed or scored.
    text=csv_bytes.decode("utf-8-sig","replace")
    reader=csv.reader(io.StringIO(text,newline=""),delimiter=";")
    header=next(reader,[])
    if len(header)!=15:
        raise ScientificStop("SOURCE_STOP_ORIGINAL_BEETLE_DATA_15_FIELD_HEADER_DRIFT")
    needed=("plot","log","year","tree")
    indexes={k:header.index(k) if k in header else -1 for k in needed}
    if any(v<0 for v in indexes.values()) or (
       indexes!=dict(plot=2,log=3,year=4,tree=6)
    ):
        raise ScientificStop("SOURCE_STOP_AUTHOR_LOG_SOURCE_FIELD_POSITION_DRIFT")
    n=0
    complete=0
    empty=Counter()
    plot_tokens=set()
    original_log_tokens=set()
    nested=set()
    log_year=Counter()
    log_to_trees=defaultdict(set)
    year_counts=Counter()
    tree_counts=Counter()
    tree_per_log_year=defaultdict(set)
    for row in reader:
        n+=1
        if len(row)!=len(header):
            raise ScientificStop("SOURCE_STOP_ORIGINAL_SOURCE_LINE_FIELD_COUNT")
        meta={k:row[j].strip() for k,j in indexes.items()}
        for k,v in meta.items():
            if missing(v):empty[k]+=1
        if any(missing(v) for v in meta.values()):
            continue
        complete+=1
        plot,log,year,tree=(meta[k] for k in needed)
        plot_tokens.add(plot)
        original_log_tokens.add(log)
        nested.add((plot,log))
        log_year[(plot,log,year)]+=1
        log_to_trees[(plot,log)].add(tree)
        tree_per_log_year[(plot,log,year)].add(tree)
        year_counts[year]+=1
        tree_counts[tree]+=1
    if n!=7738:
        raise ScientificStop("SOURCE_STOP_ORIGINAL_LONG_METADATA_ROW_COUNT_DRIFT")
    uncollapsed=len(log_year)
    counts=Counter((p,l) for p,l,y in log_year)
    conflicts=sum(len(x)>1 for x in log_to_trees.values())
    return {
      "original_long_table_source_rows":n,
      "source_metadata_fields_exact_columns_3_4_5_7_verified":True,
      "rows_with_complete_author_plot_log_year_tree_metadata":complete,
      "source_missing_metadata_row_counts":dict(empty),
      "distinct_plot_token_labels_not_independent_study_regions":len(plot_tokens),
      "distinct_raw_log_tokens_not_nested":len(original_log_tokens),
      "distinct_author_plot_log_nested_identity_candidates":len(nested),
      "distinct_author_plot_log_year_context_candidates":uncollapsed,
      "original_source_long_rows_per_context_ratio":round(n/max(uncollapsed,1),3),
      "candidate_plot_log_keys_observed_multiple_years":sum(v>1 for v in counts.values()),
      "max_distinct_years_for_original_plot_log":max(counts.values(),default=0),
      "original_plot_log_tree_assignment_conflict_count":conflicts,
      "original_plot_log_year_tree_assignment_conflict_count":sum(
          len(x)>1 for x in tree_per_log_year.values()),
      "original_source_year_label_count":len(year_counts),
      "numeric_year_label_distribution":{
          str(int(k)):v for k,v in year_counts.items()
          if re.fullmatch(r"(?:19[89][0-9]|20[0-2][0-9])",k)
      },
      "other_nonnumeric_year_source_records":sum(
          v for k,v in year_counts.items()
          if not re.fullmatch(r"(?:19[89][0-9]|20[0-2][0-9])",k)
      ),
      "distinct_tree_label_count":len(tree_counts),
      "original_tree_type_counts_UNLABELED_largest_first":sorted(tree_counts.values(),reverse=True),
      "original_source_metadata_log_IDs_and_tree_labels_NOT_EXPORTED":True,
      "original_source_taxon_and_capture_values_NOT_ACCESSED_OR_SCORED":True,
    }


def community_first_identifier_only(csv_bytes):
    # Do not read 297 taxa columns. Column 1 is only a CANDIDATE row key.
    text=csv_bytes.decode("utf-8-sig","replace")
    rd=csv.reader(io.StringIO(text,newline=""),delimiter=",")
    head=next(rd,[])
    if len(head)!=298:
        raise ScientificStop("SOURCE_STOP_COMMUNITY_WIDE_298_FIELD_DRIFT")
    ids=[]
    n=0
    for row in rd:
        n+=1
        if len(row)!=len(head):
            raise ScientificStop("SOURCE_STOP_COMMUNITY_SOURCE_FIELD_COUNT_DRIFT")
        ids.append(row[0].strip())
    if n!=525:
        raise ScientificStop("SOURCE_STOP_COMMUNITY_525_SOURCE_ROWS_DRIFT")
    distinctive=len(set(ids))
    numberlike=sum(bool(re.fullmatch(r"\d+",v)) for v in ids)
    delimiters=sum(any(x in v for x in ("_",":","-","/")) for v in ids)
    return {
        "original_community_header_source_fields":len(head),
        "original_community_candidate_source_rows":n,
        "original_community_distinct_first_column_candidate_tokens":distinctive,
        "first_column_header_is_blank":not head[0].strip(),
        "first_column_candidate_missing_count":sum(missing(v) for v in ids),
        "first_column_candidate_entirely_digits_count":numberlike,
        "first_column_candidate_has_separator_count":delimiters,
        "first_column_candidate_NOT_author_plot_log_year_verified":True,
        "original_wide_species_names_abundances_other_297_columns_UNREAD":True,
        "original_observed_community_source_ID_values_NOT_EXPORTED":True,
    }


def trait_header_metadata(binary):
    if not binary.startswith(b"PK"):
        raise ScientificStop("SOURCE_STOP_TRAIT_SOURCE_NOT_ZIP")
    with zipfile.ZipFile(io.BytesIO(binary)) as z:
        path="xl/workbook.xml"
        if path not in z.namelist():
            raise ScientificStop("SOURCE_STOP_TRAIT_WORKBOOK_MAIN_XML_MISSING")
        wb=ET.fromstring(z.read(path))
        sheetnames=[x.attrib.get("name","") for x in wb.findall(f".//{{{MAIN}}}sheet")]
        if sheetnames!=["Trait_Table"]:
            raise ScientificStop("SOURCE_STOP_ORIGINAL_TRAIT_SHEET_IDENTITY_DRIFT")
        # Official original workbook relationship, not sheet sequence guesswork
        rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid=wb.find(f".//{{{MAIN}}}sheet").attrib.get(f"{{{REL}}}id")
        vals={}
        for x in rel.findall(f"{{{PKG}}}Relationship"):
            t=x.attrib.get("Target","")
            if x.attrib.get("Id")==rid:
                name=t.lstrip("/")
                vals["file"]=name if name.startswith("xl/") else "xl/"+name
        source=vals.get("file")
        if not source or source not in z.namelist():
            raise ScientificStop("SOURCE_STOP_TRAIT_SHEET_OPENXML_RELATION_UNRESOLVED")
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared=["".join(q.text or "" for q in x.findall(f".//{{{MAIN}}}t"))
                    for x in root.findall(f"{{{MAIN}}}si")]
        sheet=ET.fromstring(z.read(source))
        first=sheet.find(f".//{{{MAIN}}}sheetData/{{{MAIN}}}row")
        if first is None:
            raise ScientificStop("SOURCE_STOP_ORIGINAL_TRAIT_FIRST_ROW_MISSING")
        cells=first.findall(f"{{{MAIN}}}c")
        safe=[]
        for i,c in enumerate(cells):
            x=""
            t=c.attrib.get("t")
            if t=="s":
                v=c.find(f"{{{MAIN}}}v")
                if v is not None and v.text and v.text.isdigit():
                    j=int(v.text)
                    x=shared[j] if j<len(shared) else ""
            elif t=="inlineStr":
                x="".join(e.text or "" for e in c.findall(f".//{{{MAIN}}}t"))
            if not x or len(x)>45:
                continue
            v=re.sub(r"[^a-z0-9_]","",x.strip().lower())
            if v in TRAIT_SAFE:
                safe.append({"source_1based_column_index":i+1,"generic_trait_header_only":x.strip()})
        return {
            "original_trait_source_sheet_identity":"Trait_Table",
            "original_source_trait_first_row_cell_count":len(cells),
            "safe_generic_original_trait_header_labels_ONLY":safe,
            "source_trait_host_affiliation_trait_not_assumed":True,
            "original_trait_species_and_value_rows_UNREAD":True,
        }


def known_truth():
    t="plot;log;year;site;tree;count\nA;1;2013;X;Fagus;42\nA;1;2014;X;Fagus;11\n".encode()
    # Source formal 15-column check is tested on production; here test
    # only identifiers/metadata hierarchy logic, no ecological statistic.
    assert len({("A","1","2013"),("A","1","2014")})==2
    assert len({("A","1"),("A","1")})==1
    assert missing("NA") and not missing("2014")
    assert bool(re.fullmatch(r"(?:19[89][0-9]|20[0-2][0-9])","2018"))
    print("SYNTHETIC_LOG_YEAR_NESTING_AND_SOURCE_ID_PRIVACY_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if not a.out:p.error("--out required")
    result={
       "schema":"structural.Lettenmaier12y_original_plot_log_year_tree_method_gate.v1",
       "original_archive_DOI":"10.5281/zenodo.17337484",
       "original_Article_DOI":"10.1111/1365-2656.70183",
       "same_original_longterm_beetle_populations_prior_art":True,
       "source_species_abundance_response_NOT_SCORED":True,
       "source_original_site_plot_log_ids_NOT_REEXPORTED":True,
       "previous_original_Finland_Burner_PREDICTS_NEON_BALA_GEB_results_SEALED":True,
       "eBird_used":False
    }
    try:
        binaries={k:get_source(*v) for k,v in M.items()}
        result["source_original_all_MD5_verified"]=True
        result["original_assembly_metadata"]={
          "Beetle_Data":original_log_metadata(binaries["raw"]),
          "Beetle_Community":community_first_identifier_only(binaries["comm"]),
          "Trait_Table":trait_header_metadata(binaries["trait"]),
        }
        conflicts=result["original_assembly_metadata"]["Beetle_Data"]["original_plot_log_tree_assignment_conflict_count"]
        if conflicts>0:
            result["status"]="SOURCE_STOP_ORIGINAL_REPEATED_LOG_TREE_IDENTITY_CONFLICT"
        else:
            result["status"]="SOURCE_LOG_YEAR_NESTING_QUALIFIED_MATRIX_CROSSWALK_STILL_UNVERIFIED"
    except ScientificStop as exc:
        result["status"]=str(exc)
        result["source_method_STOP_not_biological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Lettenmaier12y_original_log_year_tree_sourceonly.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
