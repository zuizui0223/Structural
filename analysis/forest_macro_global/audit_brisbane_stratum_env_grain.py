#!/usr/bin/env python3
"""Inspect original Brisbane beetle sampling strata and field join SUPPORT.

Read original source-pinned CC0 OOXML workbook *only first 12 metadata columns*
from 80 trap rows, 50 Ground environment rows and 29 Canopy environment rows.
All taxon abundance columns are skipped. No ecological beta diversity/effect.
"""
from __future__ import annotations

import argparse,hashlib,json,math,re,statistics,xml.etree.ElementTree as ET,zipfile
from collections import Counter
from pathlib import Path

from audit_brisbane_canopy_ground_original_xlsx import (
    SOURCE_MD5,SOURCE_DOI,OOXML,content_types,shared_text,celltext,colindex,
)


def read_first_columns(z,path,strings,cutoff=12):
    root=ET.fromstring(z.read(path))
    rows=[]
    for node in root.findall(f".//{{{OOXML}}}sheetData/{{{OOXML}}}row"):
        rec={}
        for c in node.findall(f"{{{OOXML}}}c"):
            col=re.match(r"[A-Z]+",c.get("r",""))
            if col is None:continue
            idx=colindex(col.group())
            if idx>=cutoff:continue
            txt=celltext(c,strings)
            if txt:rec[idx]=txt.strip()
        rows.append(rec)
    return rows


def string_distinct(counter):
    if len(counter)<=10:
        return dict(counter)
    return {"distinct_count":len(counter)}


def audit(path):
    content=Path(path).read_bytes()
    if hashlib.md5(content).hexdigest()!=SOURCE_MD5:
        raise ValueError("original_Brisbane_xlsx_source_hash_mismatch")
    with zipfile.ZipFile(path) as z:
        files=dict(content_types(z))
        if set(("Beetle data","Ground level enviros","Canopy level enviros"))-files.keys():
            raise ValueError("missing_original_CanopyGroundEnvironmental_sheets")
        strings=shared_text(z)
        data={name:read_first_columns(z,path,strings) for name,path in files.items()}
    beetles=data["Beetle data"]
    ground=data["Ground level enviros"]
    canopy=data["Canopy level enviros"]
    if (len(beetles),len(ground),len(canopy))!=(81,51,30):
        raise ValueError("original_Brisbane_80_traps_50_ground_29_canopy_env_drift")
    headers={name:rows[0] for name,rows in data.items()}
    beetle_meta={i:v for i,v in headers["Beetle data"].items() if i<12}
    height_cols=[i for i,v in beetle_meta.items() if re.search(r"(?i)^height$",v)]
    if len(height_cols)!=1:raise ValueError("source_beetle_trap_height_field_not_identified")
    height_col=height_cols[0]
    hvals=Counter(row.get(height_col,"") for row in beetles[1:])
    edge_cols=[i for i,v in beetle_meta.items() if re.search(r"(?i)^edge[. _-]?dist",v)]
    edgenonempty=sum(bool(row.get(edge_cols[0])) for row in beetles[1:]) if edge_cols else 0
    # Environment first column is an index even if its original header is blank.
    primary_ids={row.get(0,"") for row in beetles[1:] if row.get(0)}
    g_ids={row.get(0,"") for row in ground[1:] if row.get(0)}
    c_ids={row.get(0,"") for row in canopy[1:] if row.get(0)}
    # The source book may use numeric trap numbers under different columns,
    # so first-field equality is a DIAGNOSTIC only, not a valid ecological join.
    matches_g=len(primary_ids&g_ids)
    matches_c=len(primary_ids&c_ids)
    return {
        "schema":"structural.brisbane_canopy_ground_original_80trap_metadata_grain.v1",
        "original_source_MD5":SOURCE_MD5,
        "source_DOI":SOURCE_DOI,
        "source_original_Beetle_data_TRAP_records_NOT_80_FORESTS":len(beetles)-1,
        "source_Ground_level_environment_rows":len(ground)-1,
        "source_Canopy_level_environment_rows":len(canopy)-1,
        "source_environment_rows_total":len(ground)+len(canopy)-2,
        "beetle_source_early_metadata_field_names":list(beetle_meta.values()),
        "ground_source_early_metadata_field_names":[v for i,v in sorted(headers["Ground level enviros"].items()) if v],
        "canopy_source_early_metadata_field_names":[v for i,v in sorted(headers["Canopy level enviros"].items()) if v],
        "source_original_Height_stratum_or_value_counts":string_distinct(hvals),
        "beetle_source_Edge_dist_nonempty_record_count":edgenonempty,
        "original_first_column_nonempty_source_record_counts":{
            "beetle":len(primary_ids),"ground_env":len(g_ids),"canopy_env":len(c_ids)},
        "original_first_column_beetle_vs_env_ID_overlap_NOT_JOIN_PROOF":{
            "ground":matches_g,"canopy":matches_c},
        "one_fewer_source_environment_row_than_biological_trap_count":(len(beetles)-1)-
            (len(ground)+len(canopy)-2),
        "source_study_species_below_2_trap_locations_excluded":True,
        "taxon_abundance_source_columns_read":0,
        "independent_original_study_region_count":1,
        "forest_fragment_and_stratum_source_hierarchy_not_yet_resolved":True,
        "source_species_sample_level_join_not_yet_admitted":True,
        "no_original_taxon_names_trap_IDs_raw_environment_values_exported":True,
        "new_biological_effect_calculated":False
    }


def run(path,out):
    result=audit(path)
    d=Path(out);d.mkdir(parents=True,exist_ok=True)
    (d/"Brisbane_original_ground_canopy_meta_grain.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.source,a.out)
