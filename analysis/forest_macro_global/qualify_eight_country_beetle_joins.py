#!/usr/bin/env python3
"""Frozen 2026 8-country, 13-landscape beetle observation/forest-cover grain join.

Nardi et al. 2026 Zenodo v3 CC BY 4.0; NOT canopy-vs-understorey sampling.
Read all four source-original tables, verify their exact MD5 identities,
deduplicate 207 sampled cells, test 3,215 beetle records against those cells,
and test forest-cover SITE vs plot_id equivalence WITHOUT guessing a map.

This is an original source/response eligibility audit; do not fit effects.
Never export original SITE/CELL_ID, labels, environment values or coordinates.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from collections import Counter,defaultdict
from pathlib import Path
from audit_nardi_multiregion_beetle_sources import EXPECTED_MD5

SOURCE_DOI="10.5281/zenodo.17044394"
EXPECTED={"bio_cast":207,"bio_data_trapscale":3215,
          "env_data_sitescale":13,"env_data_trapscale":207}
FILENAMES={
    "bio_cast":"bio_cast.txt",
    "bio_data_trapscale":"bio_data_trapscale.txt",
    "env_data_sitescale":"env_data_sitescale.txt",
    "env_data_trapscale":"env_data_trapscale.txt",
}

def parse(path,role):
    p=Path(path)
    if not p.is_file() or hashlib.md5(p.read_bytes()).hexdigest()!=EXPECTED_MD5[role]:
        raise ValueError("publisher_original_MD5_changed_or_missing:"+role)
    with p.open(encoding="utf-8-sig",newline="") as f:
        d=csv.DictReader(f,delimiter="\t")
        names=[str(x).strip() for x in (d.fieldnames or [])]
        if not names or len(names)!=len(set(names)) or any(not v for v in names):
            raise ValueError("source_header_invalid:"+role)
        d.fieldnames=names
        rows=[]
        for row in d:
            if None in row or any(k not in names for k in row):
                raise ValueError("unexpected_zenodo_row_width:"+role)
            rows.append({k:(v or "").strip() for k,v in row.items()})
    if len(rows)!=EXPECTED[role]:raise ValueError("original_Zenodo_number_of_source_rows_changed:"+role)
    return rows,names

def key(v):
    return str(v or "").strip().casefold()

def count_n(x):
    value=str(x or "").strip()
    if value.lower() in ("","na","nan"):return None
    try:n=float(value)
    except ValueError:raise ValueError("source_arthropod_N_not_numeric")
    if not math.isfinite(n) or n<0 or not n.is_integer():
        raise ValueError("source_arthropod_N_not_nonnegative_integer")
    return int(n)

def build(bio_wide, bio_long, site_env, trap_env):
    w,wn=bio_wide
    b,bn=bio_long
    site,sn=site_env
    trap,tn=trap_env
    if wn[:2]!=["SITE","CELL_ID"] or bn!=["SITE","CELL_ID","SPECIES","STATUS","N"]:
        raise ValueError("source_beetle_original_columns_mismatch")
    if tn!=["SITE","CELL_ID","composition","configuration","urbanization_index"]:
        raise ValueError("source_trap_environment_schema_mismatch")
    if not sn or sn[0]!="plot_id" or not {"forest_2000","forest_3000","forest_4000"}.issubset(sn):
        raise ValueError("source_site_environment_schema_mismatch")
    source_landscape_codes={key(q["SITE"]) for q in w}
    if "" in source_landscape_codes or len(source_landscape_codes)!=13:
        raise ValueError("source_13_landscapes_not_distinct")
    wide_cells=[(key(q["SITE"]),key(q["CELL_ID"])) for q in w]
    env_cells=[(key(q["SITE"]),key(q["CELL_ID"])) for q in trap]
    if any(not a or not b for a,b in wide_cells+env_cells):
        raise ValueError("missing_source_trap_cell_identity")
    if len(set(wide_cells))!=207 or len(set(env_cells))!=207:
        raise ValueError("duplicate_source_cell_identity")
    if set(wide_cells)!=set(env_cells):
        raise ValueError("source_beetle_and_trap_environment_cell_mismatch")
    long_cells=[(key(q["SITE"]),key(q["CELL_ID"])) for q in b]
    if any(q not in set(wide_cells) for q in long_cells):
        raise ValueError("source_beetle_long_rows_with_unknown_sampling_cell")
    per_site=Counter(s for s,c in wide_cells)
    if any(v<4 for v in per_site.values()):
        raise ValueError("original_landscapes_have_unexpectedly_few_trap_cells")
    # Site-scale plot_id has to match SITE values, otherwise it is
    # forbidden to enrich response rows by naive positional row order.
    env_site_ids=[key(q["plot_id"]) for q in site]
    if len(set(env_site_ids))!=13 or "" in env_site_ids:
        raise ValueError("site_environment_plot_id_duplicate_or_missing")
    site_id_matches=set(env_site_ids)==source_landscape_codes
    unmatched_site_codes=len(source_landscape_codes-set(env_site_ids))
    # Check the experimental variable design, but do not interpret unknown
    # numeric units as forest area until publisher documentation is read.
    forest_values={f:[] for f in ("forest_2000","forest_3000","forest_4000")}
    invalid_env=Counter()
    for row in site:
        for name in forest_values:
            val=row[name].strip()
            try:v=float(val)
            except ValueError:
                invalid_env[name]+=1
                continue
            if not math.isfinite(v):
                invalid_env[name]+=1
                continue
            forest_values[name].append(v)
    env_info={
        name:{"numeric_nonmissing_n":len(vals),
              "min_raw_unit_not_interpreted":min(vals) if vals else None,
              "median_raw_unit_not_interpreted":statistics.median(vals) if vals else None,
              "max_raw_unit_not_interpreted":max(vals) if vals else None}
        for name,vals in forest_values.items()
    }
    long_unique_species={q["SPECIES"] for q in b if q["SPECIES"]}
    species_cols=wn[2:]
    overlap=long_unique_species&set(species_cols)
    status=Counter(q["STATUS"] for q in b)
    grouped=Counter()
    raw_count=0
    rows_missing_N=0
    for row in b:
        n=count_n(row["N"])
        if n is None:
            rows_missing_N+=1
        else:
            raw_count+=n
            if row["SPECIES"]:
                grouped[key(row["SITE"]),key(row["CELL_ID"]),row["SPECIES"]]+=n
    # Source wide may store occurrence as 0/1 or count; detect, never assume.
    wide_nonnumeric=0
    wide_numeric_nonmissing=0
    wide_numeric_sum=0
    for row in w:
        for sp in species_cols:
            val=row.get(sp,"").strip()
            if not val or val.upper()=="NA":continue
            try:n=float(val)
            except ValueError:
                wide_nonnumeric+=1
                continue
            if math.isfinite(n):
                wide_numeric_nonmissing+=1
                wide_numeric_sum+=n
    all_names_match=len(long_unique_species)>0 and long_unique_species<=set(species_cols)
    match_per_species_records=0
    mismatch_per_species_records=0
    if all_names_match and rows_missing_N==0 and wide_nonnumeric==0:
        wide_lookup={(key(r["SITE"]),key(r["CELL_ID"])):r for r in w}
        for (a,b_,species),n in grouped.items():
            val=wide_lookup[a,b_].get(species,"")
            try:v=float(val)
            except ValueError:v=float("nan")
            if math.isfinite(v) and abs(v-n)<1e-8:
                match_per_species_records+=1
            else:
                mismatch_per_species_records+=1
    report={
        "schema":"structural.zenodo_13_landscape_beetles_original_cell_join.v1",
        "source_dataset_DOI":SOURCE_DOI,
        "original_bio_wide_sampling_cell_rows":len(w),
        "original_bio_long_rows":len(b),
        "original_environment_trap_rows":len(trap),
        "original_environment_site_rows":len(site),
        "sampling_CELL_ID_SITE_pairs_unique":len(set(wide_cells)),
        "trap_environment_CELL_ID_SITE_pairs_unique":len(set(env_cells)),
        "all_biological_sampling_cells_have_matching_trap_environment":True,
        "original_sampled_landscapes_n":len(per_site),
        "sampled_cell_count_per_landscape_min":min(per_site.values()),
        "sampled_cell_count_per_landscape_median":statistics.median(per_site.values()),
        "sampled_cell_count_per_landscape_max":max(per_site.values()),
        "landscape_env_plot_id_and_biological_SITE_values_exact_match":site_id_matches,
        "landscape_env_SITE_join_unmatched_source_code_count":unmatched_site_codes,
        "site_environment_join_status":(
            "DIRECT_13_LANDSCAPE_ID_EQUIVALENCE" if site_id_matches
            else "STOP_REQUIRES_SOURCE_IDENTITY_CROSSWALK"),
        "site_forest_coverage_source_value_availability":env_info,
        "site_forest_coverage_original_units_not_verified":True,
        "source_bio_wide_NON_ID_column_count_NOT_ALL_IDENTIFIED_SPECIES":len(species_cols),
        "source_beetle_long_unique_species_LABELS_not_verified_species_richness":len(long_unique_species),
        "source_long_species_field_matches_wide_headers_all":all_names_match,
        "source_wide_long_species_label_overlap_count":len(overlap),
        "source_bio_long_STATUS_category_ROW_counts":dict(status) if len(status)<=12 else {"category_count":len(status)},
        "original_long_N_nonmissing_integer_row_count":len(b)-rows_missing_N,
        "original_long_N_missing_row_count":rows_missing_N,
        "original_long_N_sum_NOT_VERIFIED_SAMPLING_EFFORT":raw_count,
        "original_wide_numeric_entry_count":wide_numeric_nonmissing,
        "original_wide_nonnumeric_entry_count":wide_nonnumeric,
        "original_wide_raw_numeric_sum_NOT_ASSUMED_INDIVIDUALS":wide_numeric_sum,
        "matched_n_cell_species_counts_between_wide_long_IF_EXACT_KEY":match_per_species_records,
        "unmatched_n_cell_species_counts_between_wide_long_IF_EXACT_KEY":mismatch_per_species_records,
        "original_landscape_country_or_region_identity_verified":False,
        "original_sampling_trap_exposure_duration_verified":False,
        "original_independent_forest_patches_count_verified":0,
        "unique_original_8_country_13_landscape_scope_from_publication_only":True,
        "species_source_occupancy_or_connectivity_model_fit":False,
        "not_a_vertical_canopy_ground_study":True,
        "no_original_ids_coordinates_species_labels_exported":True,
        "eBird_used":False
    }
    return report


def run(bio_wide,bio_long,site_env,trap_env,out):
    parsed=[
        parse(bio_wide,"bio_cast"),
        parse(bio_long,"bio_data_trapscale"),
        parse(site_env,"env_data_sitescale"),
        parse(trap_env,"env_data_trapscale")
    ]
    report=build(*parsed)
    path=Path(out);path.mkdir(parents=True,exist_ok=True)
    (path/"zenodo_beetle_original_site_and_trap_join.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("bio_wide","bio_long","site_env","trap_env","out"):
        p.add_argument("--"+name,required=True)
    a=p.parse_args()
    run(a.bio_wide,a.bio_long,a.site_env,a.trap_env,a.out)
