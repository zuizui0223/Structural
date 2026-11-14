#!/usr/bin/env python3
"""Source metadata and sampling-grain audit of Pierick et al. 2026 original data.

Original DOI 10.5281/zenodo.19883322 v1 (2026), file main_dataset.csv.
Analyzes file headers, plot/source key and variable *presence*, never fits
taxon or physical response effects. No raw site labels, taxon IDs, coordinates,
temperatures, measurements or source rows are exported.
The single 30-plot Central European study does NOT constitute 30 independent
forest regions or a new global confirmation.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re
from collections import Counter
from pathlib import Path

SOURCE_DOI="10.5281/zenodo.19883322"
SOURCE_PAPER_DOI="10.1016/j.ecolind.2026.114874"
ORIGINAL_MD5="8fca5fca0fbb7c9918f90efef4390bae"
EXPECTED_AUTHOR_PLOTS=30
MAX_FILE_BYTES=2_000_000
MAX_ROWS=100_000
BAD={"","na","nan","none","null","-999","-9999","n/a"}
PATTERNS={
    "candidate_original_plot_identity":r"(?i)(^|[_ .-])(plot|stand|site)([_ .-]?(id|number|no|name))?($|[_ .-])",
    "canopy_structure":r"(?i)canop|cover|leaf.?area|gap.?fraction|sky.?view|lai|openness|gapfrac",
    "three_dimensional_structure_or_lidar":r"(?i)lidar|laser|3d|structur|rugos|complex|height|vci|prai|effective.?number",
    "microclimate_temperature":r"(?i)temp|tmax|tmin|tmean|microclimat|heat|air.?t",
    "microclimate_heterogeneity":r"(?i)heterogen|variance|variab|range|gradient|sd.?temp|cv.?temp",
    "humidity_or_vpd":r"(?i)humid|vpd|vapou?r|soil.?moist|water",
    "biodiversity_response_schema_ONLY":r"(?i)richness|divers|species|taxon|spider|hymenop|dipter|plant|beetle",
    "source_management_or_treatment":r"(?i)management|treat|silvi|thinning|control|forest.?type|stand.?type",
    "observation_time":r"(?i)year|month|date|time|season|period",
}
def decode_original(path):
    src=Path(path)
    if not src.is_file() or src.stat().st_size<1000 or src.stat().st_size>MAX_FILE_BYTES:
        raise ValueError("SCIENTIFIC_STOP_ORIGINAL_FILE_UNAVAILABLE_OR_SIZE")
    raw=src.read_bytes()
    md5=hashlib.md5(raw).hexdigest()
    if md5!=ORIGINAL_MD5:
        raise ValueError("SCIENTIFIC_STOP_ORIGINAL_ZENODO_V1_MD5_CHANGED")
    text=raw.decode("utf-8-sig")
    sample=text[:8192]
    try:delimiter=csv.Sniffer().sniff(sample,delimiters=",;\t").delimiter
    except csv.Error:raise ValueError("SCIENTIFIC_STOP_CANNOT_DETERMINE_SOURCE_DELIMITER")
    reader=csv.DictReader(io.StringIO(text),delimiter=delimiter)
    fields=[str(x or "").strip() for x in (reader.fieldnames or [])]
    if not fields or len(fields)!=len(set(fields)) or any(not x for x in fields):
        raise ValueError("SCIENTIFIC_STOP_SOURCE_HEADER_MISSING_OR_DUPLICATED")
    reader.fieldnames=fields
    rows=list(reader)
    if not rows or len(rows)>MAX_ROWS:
        raise ValueError("SCIENTIFIC_STOP_SOURCE_ROW_COUNT")
    if any(None in v or any(k not in fields for k in v) for v in rows):
        raise ValueError("SCIENTIFIC_STOP_ORIGINAL_COLUMN_WIDTH_DRIFT")
    return src,md5,delimiter,fields,rows

def source_grain(fields,rows):
    original_plot_candidates=[
        k for k in fields if re.search(PATTERNS["candidate_original_plot_identity"],k)
    ]
    plausible_priority=[
        "plotid","plot_id","plot id","plot","plotnumber","plot_number",
        "siteid","site_id","standid","stand_id","stand"
    ]
    lowered={k.lower():k for k in original_plot_candidates}
    possible=[lowered[k] for k in plausible_priority if k in lowered]
    status="CANDIDATE_PLOT_LABEL_NOT_AUTHOR_VERIFIED"
    key=None;count=None;blank=None;max_repeats=None
    if possible:
        key=possible[0]
        counts=Counter(str(row.get(key,"") or "").strip() for row in rows)
        blank=sum(z for k,z in counts.items() if k.lower() in BAD)
        distinct={k for k in counts if k.lower() not in BAD}
        count=len(distinct)
        max_repeats=max((counts[k] for k in distinct),default=0)
        status=("AUTHOR_PLOT_COLUMN_CANDIDATE_AND_30_UNIQUE_LABELS"
            if count==EXPECTED_AUTHOR_PLOTS and not blank
            else "SCIENTIFIC_STOP_PLOT_KEY_CARDINALITY_NOT_30")
    return {
        "original_declared_Plot_column_candidate":key,
        "original_plot_candidate_header_count":len(original_plot_candidates),
        "original_plot_identity_distinct_source_label_count":count,
        "original_plot_identity_missing_row_count":blank,
        "max_source_rows_per_canonical_plot_key":max_repeats,
        "original_30_plot_grain_metadata_status":status,
        "author_original_independent_forest_network_IDs_verified":False,
    }

LONG_FORMAT_META=("patch","region","climhet_var","structure_var","treatment","taxogroup")
def audit_long_format_metadata(fields,rows):
    """Examine only column identity/categorical factor labels; no numeric response."""
    if not all(k in fields for k in LONG_FORMAT_META):
        return {
            "long_format_design_status":"NOT_THE_PUBLISHED_WIDE_TO_LONG_FACTOR_SCHEMA",
            "long_format_required_factor_names_present":{
                k:k in fields for k in LONG_FORMAT_META},
            "original_physical_plot_count_author_verified":False,
        }
    n=len(rows)
    distinct=lambda key:{str(row.get(key) or "").strip() for row in rows
                         if str(row.get(key) or "").strip().lower() not in BAD}
    unique_patch=distinct("patch")
    unique_region=distinct("region")
    plot_keys={(str(r["region"]).strip(),str(r["patch"]).strip())
              for r in rows if str(r["region"]).strip() and str(r["patch"]).strip()}
    perplot=Counter((str(r["region"]).strip(),str(r["patch"]).strip())
                    for r in rows)
    per_metadata_combinations={
        (str(r["region"]).strip(),str(r["patch"]).strip(),
         str(r["climhet_var"]).strip(),str(r["structure_var"]).strip(),
         str(r["taxogroup"]).strip(),str(r["treatment"]).strip())
        for r in rows}
    category_list={}
    for field in ("climhet_var","structure_var","taxogroup"):
        levels=distinct(field)
        category_list[field]=sorted(levels) if len(levels)<=50 and all(
            0<len(z)<=90 and not re.search(r"[\n\r]",z) for z in levels) else []
    counts={k:len(distinct(k)) for k in LONG_FORMAT_META}
    status=("LONG_FORMAT_30_REGION_PATCH_KEYS_CANDIDATE"
            if len(plot_keys)==EXPECTED_AUTHOR_PLOTS else
            "SCIENTIFIC_STOP_SOURCE_REGION_PATCH_COUNT_NOT_30")
    # Matching identical year/region/forest networks still needs primary
    # author's original plot hierarchy. Region labels are NOT automatically
    # independent forest sites.
    return {
      "long_format_design_status":status,
      "source_observation_rows_NOT_independent_field_plots":n,
      "source_unique_patch_codes":len(unique_patch),
      "source_unique_region_codes_NOT_independent_forest_studies":len(unique_region),
      "source_region_patch_unique_keys_NOT_certified_independent_forests":len(plot_keys),
      "source_rows_per_region_patch_min":min(perplot.values()) if perplot else None,
      "source_rows_per_region_patch_max":max(perplot.values()) if perplot else None,
      "source_unique_region_patch_climhet_structure_taxogroup_treatment_combinations":len(per_metadata_combinations),
      "source_duplicate_original_factor_combination_rows":n-len(per_metadata_combinations),
      "source_nonmissing_category_cardinality_NOT_values":counts,
      "source_original_climhet_structure_taxogroup_FACTOR_LABELS_not_effects":category_list,
      "original_biodiversity_div_values_NOT_READ":True,
      "original_structure_val_measurements_NOT_READ":True,
      "original_climhet_val_measurements_NOT_READ":True,
      "original_region_patch_identifier_VALUES_NOT_EXPORTED":True,
      "field_replicates_not_independent_regions":True,
      "source_30_plot_authored_hierarchy_not_independently_verified":True,
    }

def audit(path):
    src,md5,delimiter,fields,rows=decode_original(path)
    candidates={
        name:[f for f in fields if re.search(pattern,f)]
        for name,pattern in PATTERNS.items()
    }
    original_plot=source_grain(fields,rows)
    long_grain=audit_long_format_metadata(fields,rows)
    return {
        "schema":"structural.pierick2026_3Dforest_original_source_header_grain.v1",
        "source_DOI":SOURCE_DOI,
        "source_related_published_2026_paper_DOI":SOURCE_PAPER_DOI,
        "original_Zenodo_version":"v1",
        "source_original_main_dataset_csv_md5":md5,
        "original_data_file_byte_size":src.stat().st_size,
        "original_data_row_count":len(rows),
        "source_csv_delimiter":repr(delimiter),
        "source_field_count":len(fields),
        "source_author_field_names_original":fields,
        "source_candidate_variable_families_FROM_HEADERS_ONLY":candidates,
        "published_field_design_30_Central_European_broadleaf_forest_0p25ha_plots":True,
        "published_biodiversity_microclimate_structure_correlations_already_analyzed":True,
        "original_dataset_species_or_microclimate_or_structure_values_fit":False,
        "original_response_biodiversity_values_semantically_read":False,
        "original_plot_rows_values_redistributed":False,
        "original_plot_names_taxon_labels_coordinates_not_exported":True,
        "no_independent_multi_region_or_global_confirmation":True,
        "eBird_used":False,
        **original_plot,
        **long_grain,
    }

def main(path,out):
    result=audit(path)
    dst=Path(out);dst.mkdir(parents=True,exist_ok=True)
    (dst/"pierick2026_3D_forest_source_only_schema.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--file",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    main(a.file,a.out)
