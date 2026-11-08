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
    SOURCE_MD5,SOURCE_DOI,OOXML,REL,PKGREL,content_types,shared_text,celltext,colindex,
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
    def layer_name(v):
        x=str(v or "").strip().lower()
        if x=="ground":return "Ground"
        if x=="canopy":return "Canopy"
        return "UNKNOWN"
    layer_edges=Counter()
    for row in beetles[1:]:
        kind=layer_name(row.get(height_col,""))
        ed=row.get(edge_cols[0],"") if edge_cols else ""
        layer_edges[f"{kind}|{ed}"]+=1
    expected={"Ground|1":10,"Ground|4":10,"Ground|16":10,
              "Ground|64":10,"Ground|256":10,
              "Canopy|1":10,"Canopy|16":10,"Canopy|256":10}
    def anonymous_id_shape(x):
        return "".join("#" if c.isdigit() else "A" if c.isalpha()
                       else c for c in str(x or ""))[:20]
    first20=[anonymous_id_shape(row.get(0,"")) for row in beetles[1:21]]
    block8=[]
    motif_template=Counter({(x.split("|")[0],x.split("|")[1]):1 for x in expected})
    for i in range(10):
        rows=beetles[1+i*8:1+(i+1)*8]
        motif=Counter((layer_name(row.get(height_col,"")),
                      row.get(edge_cols[0],"") if edge_cols else "")
                      for row in rows)
        block8.append(motif==motif_template)
    def numeric_n(row,idx):
        try:return float(row.get(idx,""))
        except (ValueError,TypeError):return None
    # Inspect the publisher's Obs code for an actual site key instead of
    # inferring site identity by spreadsheet row order. Data are sorted partly
    # by height, so adjacent sets of eight are NOT necessarily one forest site.
    sitegroups={}
    structural_codes=Counter()
    obs_parse_count=0
    for row in beetles[1:]:
        original_code=row.get(0,"")
        match=re.fullmatch(r"([A-Za-z]+)([0-9]+)([A-Za-z]+)([0-9]+)([A-Za-z]+)",original_code)
        if match is None:continue
        prefix,site_number,layer_token,edge_num,suffix=match.groups()
        source_site=(prefix,site_number)
        obs_parse_count+=1
        lvl=layer_name(row.get(height_col,""))
        try:distance=int(float(row.get(edge_cols[0],"")))
        except (ValueError,TypeError):distance=None
        if distance is None or distance!=int(edge_num):
            structural_codes["edge_distance_disagreement"]+=1
        structural_codes[f"encoded_layer_{layer_token}_source_height_{lvl}"]+=1
        sitegroups.setdefault(source_site,Counter())[(lvl,distance)]+=1
    valid_site_motif=Counter({(x.split("|")[0],int(x.split("|")[1])):1 for x in expected})
    source_site_count=len(sitegroups)
    sites_with_complete_5ground_3canopy=sum(
        v==valid_site_motif for v in sitegroups.values())
    def original_meta(colnames,data):
        head=data[0]
        idx=[i for i,x in head.items() if x in colnames]
        if not idx:return {"field_present":False}
        vals=[numeric_n(row,idx[0]) for row in data[1:]]
        valid=[x for x in vals if x is not None and math.isfinite(x)]
        return {
            "field_present":True,"original_numeric_rows":len(valid),
            "original_distinct_numeric_values":len(set(valid)),
            "source_min":min(valid) if valid else None,
            "source_max":max(valid) if valid else None
        }
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
        "original_height_x_edge_stratum_counts":dict(layer_edges),
        "ten_sites_eight_traps_each_original_column_height_and_edge_design":
            dict(layer_edges)==expected,
        "eight_record_repeating_site_order_motif_verified_count":sum(block8),
        "original_Obs_site_layer_edge_pattern_parse_rows":obs_parse_count,
        "original_Obs_code_distinct_site_labels_count":source_site_count,
        "original_Obs_site_codes_with_complete_8trap_5ground3canopy_design":
            sites_with_complete_5ground_3canopy,
        "original_Obs_embedded_edge_distance_label_mismatch":structural_codes["edge_distance_disagreement"],
        "original_Obs_embedded_stratum_token_vs_source_height_diagnostics":{
            k:v for k,v in structural_codes.items() if k!="edge_distance_disagreement"},
        "exact_thirty_ground_canopy_site_by_edge_pair_opportunities_verified":
            sites_with_complete_5ground_3canopy==10 and source_site_count==10
            and obs_parse_count==80
            and structural_codes["edge_distance_disagreement"]==0,
        "original_Obs_first_20_ID_shape_only":first20,
        "ground_environment_Dist_CBD_field_numeric_support":
            original_meta({"Dist.CBD"},ground),
        "canopy_environment_Dist_CBD_field_numeric_support":
            original_meta({"Dist.CBD"},canopy),
        "ground_environment_Canopy_cover_numeric_support":
            original_meta({"Can.cov"},ground),
        "canopy_environment_Canopy_cover_numeric_support":
            original_meta({"Can.cov"},canopy),
        "canopy_environment_Trap_height_numeric_support":
            original_meta({"Trap.height"},canopy),
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
