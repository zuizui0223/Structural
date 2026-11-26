#!/usr/bin/env python3
"""Audit genuine 8-country / 13-landscape beetle surveillance study source data.

Nardi et al 2026, Ecological Applications, DOI 10.1002/eap.70194
Zenodo source record 17044394, v3, 4 open text tables. Sampling was within
13 landscapes in eight countries, NOT 13 naturally isolated forests and NOT
canopy-vs-understorey vertical surveys. This metadata-only assay checks
original file checksums, content shapes and candidate ecological joins,
not biological source/island mechanism effects.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re
from collections import Counter
from pathlib import Path

SOURCE_DOI="10.5281/zenodo.17044394"
SOURCE_ARTICLE_DOI="10.1002/eap.70194"
EXPECTED_MD5={
 "bio_cast":"617af7a182a3fd3fb6e68e93caee23f8",
 "bio_data_trapscale":"ad729c78fed9c727c5b33728a94f0b6c",
 "env_data_sitescale":"1096c041aab4b166e83ae3390d4b496e",
 "env_data_trapscale":"11113faa4c13dd775c75da7e5238d2c9",
}

def parse_text_source(path, name):
    p=Path(path)
    if not p.is_file() or p.stat().st_size<100:
        raise ValueError("not_a_valid_original_zenodo_text_table:"+name)
    data=p.read_bytes()
    checksum=hashlib.md5(data).hexdigest()
    if checksum!=EXPECTED_MD5[name]:
        raise ValueError("source_Zenodo_2026_v3_md5_version_changed:"+name)
    try:raw=data.decode("utf-8-sig")
    except UnicodeError:raise ValueError("original_Zenodo_text_not_UTF8:"+name)
    first=raw[:12000]
    # R exported tables are tab, comma or semicolon; never split taxon labels
    # by arbitrary whitespace or manually reinterpret a summary as original
    # row-level data.
    head=raw.splitlines()[0]
    counts={sep:head.count(sep) for sep in ("\t",",",";")}
    delim=max(counts,key=counts.get)
    if counts[delim]<1:raise ValueError("cannot_determine_original_table_delimiter:"+name)
    if head.count(delim)<1:raise ValueError("cannot_determine_original_table_delimiter:"+name)
    rdr=csv.reader(io.StringIO(raw),delimiter=delim)
    headers=next(rdr,None)
    if not headers:raise ValueError("empty_source_Zenodo_original")
    header=[str(x or "").strip().strip('"') for x in headers]
    if any(not x for x in header) or len(header)!=len(set(header)):
        raise ValueError("malformed_original_source_column_names:"+name)
    n=0
    incomplete=0
    candidate=Counter()
    ids_by_column={}
    potential=[i for i,x in enumerate(header) if re.fullmatch(
       r"(?i)(?:site|site.?id|landscape|landscape.?id|location|trap|trap.?id|country|plot|plot.?id)",x)]
    ids={i:set() for i in potential}
    for record in rdr:
        if not record or not any(str(x).strip() for x in record):continue
        n+=1
        if len(record)!=len(header):
            incomplete+=1
            continue
        for i in potential:
            s=str(record[i] or "").strip()
            if s:ids[i].add(s)
    if n<=3 or incomplete>0:
        raise ValueError("original_source_rows_empty_or_malformed:"+name)
    return {
        "original_filename":p.name,
        "sha256":hashlib.sha256(data).hexdigest(),
        "source_md5_verified":checksum,
        "source_delimiter":"TAB" if delim=="\t" else "COMMA" if delim=="," else "SEMICOLON",
        "source_row_count":n,
        "source_column_count":len(header),
        "source_fieldnames_suppressed_if_taxon_wide_format":True,
        "source_schema_column_names_ONLY_IF_NARROW":header if len(header)<=30 else None,
        "source_first_two_column_names_IF_WIDE":header[:2] if len(header)>30 else None,
        "source_candidate_ID_field_unique_counts_NOT_independent_sampling_units":{
            header[i]:len(vals) for i,vals in ids.items()
        },
        "source_table_type":name,
        "_private_full_source_header":header
    }


def audit(bio_cast,bio_data_trapscale,env_data_sitescale,env_data_trapscale):
    sources={
       "bio_cast":parse_text_source(bio_cast,"bio_cast"),
       "bio_data_trapscale":parse_text_source(bio_data_trapscale,"bio_data_trapscale"),
       "env_data_sitescale":parse_text_source(env_data_sitescale,"env_data_sitescale"),
       "env_data_trapscale":parse_text_source(env_data_trapscale,"env_data_trapscale")
    }
    # Field names, not values, are matched here. A shared column name is
    # candidate join metadata, NOT proof that original sample IDs align.
    bio=set(x.lower() for x in sources["bio_data_trapscale"]["_private_full_source_header"])
    trap=set(x.lower() for x in sources["env_data_trapscale"]["_private_full_source_header"])
    site=set(x.lower() for x in sources["env_data_sitescale"]["_private_full_source_header"])
    allowed_names=re.compile(r"(?i)^(?:site|site.?id|trap|trap.?id|location|plot|plot.?id|landscape|landscape.?id|country|year|date|sampling.?year|forest|region)$")
    shared_bio_trap=sorted(x for x in bio & trap if allowed_names.fullmatch(x))
    shared_bio_site=sorted(x for x in bio & site if allowed_names.fullmatch(x))
    for x in sources.values():x.pop("_private_full_source_header")
    report={
       "schema":"structural.multiregion_beetle_zenodo_original_13_landscapes_audit.v1",
       "source_record":"https://zenodo.org/records/17044394",
       "source_dataset_DOI":SOURCE_DOI,
       "source_published_article_DOI":SOURCE_ARTICLE_DOI,
       "source_license":"CC-BY-4.0",
       "source_original_version":"v3",
       "source_tables":sources,
       "candidate_shared_field_names_bio_vs_trap_env":shared_bio_trap,
       "candidate_shared_field_names_bio_vs_site_env":shared_bio_site,
       "original_study_reports_13_landscapes_eight_countries":True,
       "published_beetle_counts_by_target_group_REFERENCE_ONLY":{
           "Cerambycidae":15072,"bark_beetles":8416,"ambrosia_beetles":38267
       },
       "published_beetle_species_counts_by_group_REFERENCE_ONLY":{
           "Cerambycidae":167,"bark_beetles":105,"ambrosia_beetles":27
       },
       "independent_original_plot_count_verified":0,
       "source_species_and_trap_effort_meaning_verified":False,
       "site_trap_year_method_keys_verified":False,
       "not_an_insect_canopy_v_ground_vertical_data_source":True,
       "new_source_topology_or_forestation_effect_scored":False,
       "raw_species_values_site_IDs_coordinates_not_exported":True,
       "eBird_used":False
    }
    return report


def run(bio_cast,bio_data_trapscale,env_data_sitescale,env_data_trapscale,out):
    r=audit(bio_cast,bio_data_trapscale,env_data_sitescale,env_data_trapscale)
    d=Path(out);d.mkdir(parents=True,exist_ok=True)
    (d/"zenodo_eight_country_beetle_source_grain.json").write_text(
        json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,ensure_ascii=False))
    return r

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for item in ("bio_cast","bio_data_trapscale","env_data_sitescale","env_data_trapscale","out"):
        p.add_argument("--"+item,required=True)
    a=p.parse_args()
    run(a.bio_cast,a.bio_data_trapscale,a.env_data_sitescale,a.env_data_trapscale,a.out)
