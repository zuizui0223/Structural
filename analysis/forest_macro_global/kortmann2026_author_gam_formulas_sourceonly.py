#!/usr/bin/env python3
"""Hash-pinned Kortmann 2026 ORIGINAL R GAM-call static cues; ZERO data rows.

Parses only the original small R *code* member, does NOT execute code and
never reads source .rda/.xlsx or any original biological values.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from kortmann2026_17775805_original_zip_directory_only import (
    SourceStop, original_file_metadata, official_get_one_zip, inspect_central_directory_only,
)

PRESPEC="docs/FOREST_MACRO_KORTMANN_AUTHOR_GAM_FORMULA_METADATA_PREFREEZE_20261121.md"
SCRIPT="scripts_public/models.R"
SCRIPT_SIZE=16103
SCRIPT_SHA="240d1b37150db6cf0b8b0288906dd0ba653fe92661a8a07e86a942f5af797b32"
DATA_SOURCE_MEMBERS={
    "data_public/diversity_satellite.rda",
    "data_public/otu_matrix.rda",
    "data_public/phylogenetic_tree.rda",
    "data_public/FT_Retz_RV-UniWue-2022-003_COI_w-1-tons_results_AIMIDs.xlsx"
}
ROLE_TERMS={
    "site_patch":("site","siteid","site_id","plot","plotid","plot_id","patch","patchid","patch_id","triplet","forestsite"),
    "forest_tree":("foresttype","forest_type","forest","tree","spruce","beech","pine","oak"),
    "management":("management","manage","managed","disturbance","disturbed","treatment","treat","cleared","clear","logging","logged","salvage"),
    "time_effort":("sample","sampling","year","date","day","days","effort","period","round","duration","samplinglength","sampling_length","trapdays","offset"),
    "coverage_otu":("otu","otus","coverage","completeness","reads","abundance","iNEXT3D","iNEXT"),
}
TERM_RE=re.compile(r"(?<![A-Za-z0-9._])[A-Za-z][A-Za-z0-9._]*(?![A-Za-z0-9._])")
GAM_RE=re.compile(r"(?<![A-Za-z0-9._])gam\s*\(",re.I)
OFFSET_RE=re.compile(r"(?<![A-Za-z0-9._])offset\s*\(",re.I)
S_RE=re.compile(r"(?<![A-Za-z0-9._])s\s*\(",re.I)

def mask_comments_and_strings(source):
    # Preserve original indexes, but mask all quoted literals and comments.
    # Backtick names are masked too, so unknown source labels cannot leak.
    a=list(source)
    mode=None;i=0
    while i<len(a):
        c=source[i]
        if mode is None:
            if c=="#":
                mode="comment";a[i]=" "
            elif c in ('"', "'", "`"):
                mode=c;a[i]=" "
        elif mode=="comment":
            if c=="\n":
                mode=None
            else:a[i]=" "
        elif mode in ('"', "'", "`"):
            a[i]=" "
            if c=="\\" and i+1<len(a):
                i+=1;a[i]=" "
            elif c==mode:mode=None
        i+=1
    if mode not in (None,"comment"):
        raise SourceStop("SOURCE_AUTHOR_R_SCRIPT_UNCLOSED_STRING")
    return "".join(a)

def extract_real_gam_calls(original):
    mask=mask_comments_and_strings(original)
    positions=list(GAM_RE.finditer(mask))
    if len(positions)>100:
        raise SourceStop("SOURCE_AUTHOR_EXCESS_GAM_EXPRESSION_COUNT")
    bodies=[]
    for m in positions:
        start=m.end()-1
        d=0;end=None
        for i in range(start,len(mask)):
            if mask[i]=="(":d+=1
            elif mask[i]==")":
                d-=1
                if d==0:
                    end=i;break
        if end is None or end-start>12000:
            raise SourceStop("SOURCE_AUTHOR_GAM_PARENTHESES_OR_SIZE_STOP")
        bodies.append((mask[start+1:end],original[start+1:end]))
    return bodies

def method_cues_from_original_code(source):
    bodies=extract_real_gam_calls(source)
    if not bodies:
        raise SourceStop("SOURCE_AUTHOR_CODE_NO_PARSEABLE_GAM")
    # Exclude arbitrary R tokens; release only fixed role names/counts.
    results=[]
    for masked,original in bodies:
        tokens=set(t.casefold() for t in TERM_RE.findall(masked))
        names={role:sorted(set(t.casefold() for t in candidate)&tokens)
               for role,candidate in ROLE_TERMS.items()}
        re_smooth=len(S_RE.findall(masked))
        re_offset=len(OFFSET_RE.findall(masked))
        # Presence of bs="re" in source is an R-method syntax hint only,
        # NOT proof of original physical site identity or random effects fit.
        re_bs=bool(re.search(r"\bbs\s*=\s*['\"]re['\"]",original,re.I))
        results.append((names,re_smooth,re_offset,re_bs))
    aggregates={
        "parseable_gam_call_count":len(results),
        "calls_with_role":{
            role:sum(bool(r[0][role]) for r in results)
            for role in ROLE_TERMS
        },
        "predeclared_role_names_seen_in_GAM_calls_ONLY":{
            role:sorted(set().union(*(set(r[0][role]) for r in results)))
            for role in ROLE_TERMS
        },
        "smoothing_function_call_count_in_GAM_expressions":sum(r[1] for r in results),
        "offset_function_call_count_in_GAM_expressions":sum(r[2] for r in results),
        "GAM_calls_containing_literal_bs_re_marker":sum(r[3] for r in results),
        "original_R_code_text_and_formulas_NOT_EXPORTED":True,
        "unknown_literal_field_names_and_strings_NOT_EXPORTED":True,
        "parsed_code_only_NO_RData_or_specimen_values":True,
        "identifiers_in_formulas_NOT_verified_data_columns":True,
    }
    return aggregates

def run():
    link=original_file_metadata()
    raw=official_get_one_zip(link)
    if inspect_central_directory_only(raw)["status"]!="SOURCE_ZIP_CENTRAL_DIRECTORY_READY_METADATA_ONLY":
        raise SourceStop("SOURCE_PUBLISHER_ZIP_DIRECTORY_NOT_READY")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names={info.filename:info for info in z.infolist() if not info.is_dir()}
        if set(names)!=(DATA_SOURCE_MEMBERS|{SCRIPT,"scripts_public/iNEXT3D.R"}):
            raise SourceStop("SOURCE_ORIGINAL_ZIP_FILE_ROSTER_CHANGED")
        if names[SCRIPT].file_size!=SCRIPT_SIZE:
            raise SourceStop("SOURCE_AUTHOR_MODELS_R_SIZE_CHANGED")
        try:code=z.read(SCRIPT) # ORIGINAL METHOD CODE ONLY, never any data
        except (KeyError,zipfile.BadZipFile,OSError):
            raise SourceStop("SOURCE_AUTHOR_MODELS_R_READ_STOP") from None
    if len(code)!=SCRIPT_SIZE or hashlib.sha256(code).hexdigest()!=SCRIPT_SHA:
        raise SourceStop("SOURCE_AUTHOR_MODELS_R_HASH_DRIFT")
    try:text=code.decode("utf-8-sig")
    except UnicodeError:raise SourceStop("SOURCE_AUTHOR_MODELS_R_UTF8_STOP") from None
    report=method_cues_from_original_code(text)
    return{
      "status":("SOURCE_GAM_FORMULA_ROLE_CANDIDATES_NO_FIELD_ADMISSION"
                if report["calls_with_role"]["site_patch"] and report["calls_with_role"]["management"]
                else "SOURCE_AUTHOR_GAM_FIELD_IDENTIFICATION_HOLD"),
      "exact_original_R_script_SHA256":SCRIPT_SHA,
      "author_R_method_expression_summary_ONLY":report,
      "original_R_code_EXECUTED":False,
      "all_original_RData_and_XLSX_members_UNOPENED":True,
      "original_site_sample_rows_read":0,
      "original_OTU_specimen_richness_values_read":0,
      "new_ecological_effects_fitted":0,
    }

def synthetic():
    script = '''
    # gam(site~management) is only a comment!
    example <- "gam(OTU ~ site)"
    fit <- gam(y ~ s(site, bs="re") + management +
      offset(log(trapdays)) + forest_type, family=poisson())
    fit2 <- gam(z ~ s(patch, bs='re') + cleared, family=nb())
    '''
    a=method_cues_from_original_code(script)
    assert a["parseable_gam_call_count"]==2, a["parseable_gam_call_count"]
    assert a["calls_with_role"]["site_patch"]==2
    assert a["calls_with_role"]["management"]==2
    assert a["calls_with_role"]["time_effort"]==1
    assert a["offset_function_call_count_in_GAM_expressions"]==1
    assert a["GAM_calls_containing_literal_bs_re_marker"]==2
    assert "example" not in json.dumps(a)
    assert "poisson" not in json.dumps(a)
    assert "z ~" not in json.dumps(a)
    print("SYNTHETIC_KORTMANN_ORIGINAL_GAM_METHOD_EXPRESSION_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out required")
    out={
      "schema":"structural.Kortmann2026_original_GAM_formula_method_only.v1",
      "prespec":PRESPEC,
      "previous_author_code_broad_word_counts_UNCHANGED":True,
      "historical_BETAFOR99_original_effect_SEALED":True,
      "original_RData_and_XLSX_members_requested":0,
      "biological_source_rows_READ":0,
      "new_field_effects_fit":0,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
      out["source"]=run()
      out["status"]=out["source"]["status"]
    except SourceStop as e:
      out["status"]="SOURCE_GAM_METHOD_STOP_"+str(e)
      out["not_ecological_null"]=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("KORTMANN_AUTHOR_GAM_METHOD_ONLY",out["status"])
    print("ORIGINAL_RDATA_XLSX_SPECIES_AND_MODEL_FITS_ALL_ZERO")

if __name__=="__main__":
    main()
