#!/usr/bin/env python3
"""Source-only diagnosis of SLU original Block↔Plot mismatches.

Reads ONLY original fixed ID columns, not beetle Species/Number/STI nor
2020 temperature, CTI, Bark, Diameter, richness or abundance values.
Prior strict cohort STOP is not modified; this measures the mismatch.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from sweden6_slu_original_three_file_header_gate import official_get, ORIGINAL_URLS, SourceStop, first_header_only

PRESPEC = "docs/FOREST_SWEDEN6_BLOCK_PLOT_AUTHOR_CODEBOOK_CONFLICT_SOURCE_DIAGNOSTIC_20261119.md"
FILES={
  "climate":("boreal_forest_climate_data.csv",7019,"d546273c352fb2cab97f63f35883f970baea09790348fa4c0dda3e1bc55ba776",12,("Block","Plot","Shade")),
  "beetles":("specieslist_xylo.csv",157911,"a67a905ee05e3994f3e85bc29f8b68fbb314677d6e5a6cc4cd479b2b9d87ec9a",7,("Block","Plot","Log","Sampling_date"))
}
PUBLISHED_PLOT_CODES={1:set(range(11,16)),2:set(range(6,11)),
                      3:set(range(16,21)),4:set(range(21,26)),
                      5:set(range(1,6)),6:set(range(26,31))}
LOG_SHADE={i:1+((i-1)%3) for i in range(1,16)}
ASCII_INT=re.compile(r"^[0-9]+$")
YEAR=re.compile(r"(?<![0-9])((?:19|20)[0-9]{2})(?![0-9])")
SEPARATORS={"comma":",","semicolon":";","tab":"\t"}

def numeric_literal(x,low,high):
    s=str(x).strip()
    if not ASCII_INT.fullmatch(s):return None
    n=int(s)
    return n if low<=n<=high else None

def inspect_nonresponse_rows(blob,head,idfields,which):
    # csv parses full row boundaries, but semantic values are examined only
    # through explicit source identifiers selected before biological access.
    try:
        s=blob.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("SWEDEN6_SOURCE_ORIGINAL_UTF8_RECORD_PARSE_STOP") from None
    f=io.StringIO(s,newline="")
    reader=csv.reader(f,delimiter=SEPARATORS[head["original_CSV_header_delimiter"]],strict=True)
    actual=next(reader,None)
    if actual!=head["original_HEADER_exact_author_field_names"]:
        raise SourceStop("SWEDEN6_SOURCE_CSV_HEADER_NOT_IDENTICAL_AT_READ")
    pos={key:actual.index(key) for key in idfields}
    plot_by_block=defaultdict(set)
    key_counts=Counter()
    shade_by_plot=defaultdict(set)
    log_keys=set()
    year_counts=Counter()
    valid_pair_keys=set()
    valid_site_shade=set()
    failures=Counter()
    n=0
    for row in reader:
        n+=1
        if n>10000 or len(row)!=len(actual):
            raise SourceStop("SWEDEN6_ORIGINAL_SOURCE_ID_ROW_COUNT_OR_WIDTH_STOP")
        block=numeric_literal(row[pos["Block"]],1,6)
        plot=numeric_literal(row[pos["Plot"]],1,30)
        if block is None:failures["block_invalid_literal_or_outside_1to6"]+=1
        if plot is None:failures["plot_invalid_literal_or_outside_1to30"]+=1
        if block is None or plot is None:continue
        plot_by_block[block].add(plot)
        valid_pair_keys.add((block,plot))
        if which=="climate":
            shade=numeric_literal(row[pos["Shade"]],1,3)
            if shade is None:
                failures["shade_invalid_literal_or_outside_1to3"]+=1
                continue
            shade_by_plot[(block,plot)].add(shade)
            key_counts[(block,plot,shade)]+=1
            valid_site_shade.add((block,plot,shade))
        else:
            log=numeric_literal(row[pos["Log"]],1,15)
            if log is None:
                failures["log_invalid_literal_or_outside_1to15"]+=1
                continue
            log_keys.add((block,plot,log))
            valid_site_shade.add((block,plot,LOG_SHADE[log]))
            date=str(row[pos["Sampling_date"]]).strip()
            years=YEAR.findall(date)
            if len(years)==1:
                year_counts[years[0]]+=1
            else:
                failures["date_year_unrecognised"]+=1
    if not n:raise SourceStop("SWEDEN6_SOURCE_EMPTY_ID_TABLE")
    per_block={}
    invalid_pairs=set()
    for block, plots in sorted(plot_by_block.items()):
        invalid=plots-PUBLISHED_PLOT_CODES[block]
        invalid_pairs|={(block,p) for p in invalid}
        per_block[str(block)]={
          "unique_plot_codes_count":len(plots),
          "original_code_min":min(plots) if plots else None,
          "original_code_max":max(plots) if plots else None,
          "unique_plot_codes_matching_published_block_range":len(plots-invalid),
          "unique_plot_codes_outside_published_block_range":len(invalid),
        }
    result={
      "source_ID_field_only_original_rows_count":n,
      "source_Block_categories_in_original_ID_records_count":len(plot_by_block),
      "source_unique_numeric_Block_Plot_keys":len(valid_pair_keys),
      "source_original_plot_codes_by_Block_ANONYMOUS_NUMERIC_SUMMARY":per_block,
      "source_original_Block_Plot_pair_keys_outside_published_codebook":len(invalid_pairs),
      "source_original_ID_literal_format_or_range_issues":dict(sorted(failures.items())),
      "source_original_unique_Block_Plot_Shade_ID_keys":len(valid_site_shade),
      "source_original_ID_columns_only_SEMANTICALLY_READ":list(idfields),
      "source_original_numeric_biology_or_environment_fields_SEMANTICALLY_READ":0,
      "source_original_ID_values_or_taxon_names_EXPORTED":False,
      "_private_plot_keys":valid_pair_keys,
      "_private_shade_keys":valid_site_shade,
    }
    if which=="climate":
        expected={(b,p,s) for b,p in valid_pair_keys for s in (1,2,3)}
        result.update({
          "source_climate_key_count_duplicate_records":sum(v-1 for v in key_counts.values() if v>1),
          "source_climate_unique_keys_with_duplicates":sum(v>1 for v in key_counts.values()),
          "source_climate_key_triplets_missing_from_three_per_observed_plot":len(expected-valid_site_shade),
          "source_original_recorded_climate_88_catalog_rows_observed":n==88,
        })
    else:
        result.update({
          "source_species_file_DISTINCT_log_ID_keys_with_positive_source_records":len(log_keys),
          "source_species_file_original_sample_date_year_token_counts":dict(sorted(year_counts.items())),
          "source_species_file_missing_or_zero_capture_LOGS_NOT_INFERRED":True,
        })
    return result

def source_only(get=official_get):
    metadata={}
    outputs={}
    for key,(name,expected_bytes,sha,ncol,cols) in FILES.items():
        raw=get(ORIGINAL_URLS[name][0])
        if len(raw)!=expected_bytes or hashlib.sha256(raw).hexdigest()!=sha:
            raise SourceStop("SWEDEN6_ORIGINAL_"+key.upper()+"_PINNED_SOURCE_FINGERPRINT_DRIFT")
        head=first_header_only(raw,ncol)
        if any(head["original_HEADER_exact_author_field_names"].count(x)!=1 for x in cols):
            raise SourceStop("SWEDEN6_SOURCE_"+key.upper()+"_REQUIRED_AUTHOR_FIELD_MISSING")
        if key=="beetles" and (
          head["original_CSV_header_delimiter"]!="semicolon" or
          head["original_HEADER_exact_author_field_names"]!=[
              "Block","Plot","Log","Sampling_date","Species","Number","STI"]):
            raise SourceStop("SWEDEN6_ORIGINAL_7FIELD_SPECIES_SOURCE_SCHEMA_DRIFT")
        metadata[key]={"source_original_file_sha256":sha,"source_file_byte_size":expected_bytes,
                       "source_nonresponse_fields_exact":list(cols)}
        outputs[key]=inspect_nonresponse_rows(raw,head,cols,key)
    c=outputs["climate"]
    b=outputs["beetles"]
    cp=c.pop("_private_plot_keys")
    bp=b.pop("_private_plot_keys")
    cs=c.pop("_private_shade_keys")
    bs=b.pop("_private_shade_keys")
    return {
      "source_official_slufile_metadata_attested":metadata,
      "original_climate_ID_only":c,
      "original_beetle_ID_only":b,
      "original_Block_Plot_pair_source_intersection_count":len(cp&bp),
      "original_Block_Plot_pair_in_climate_not_beetle_source_count":len(cp-bp),
      "original_Block_Plot_pair_in_beetle_not_climate_source_count":len(bp-cp),
      "original_Block_Plot_Shade_source_intersection_count":len(cs&bs),
      "original_beetle_source_shade_keys_missing_from_climate_ID_table":len(bs-cs),
      "original_climate_source_shade_keys_without_positive_beetle_source":len(cs-bs),
      "old_strict_BLOCK_PLOT_codebook_scientific_STOP_PRESERVED":True,
      "source_beetle_species_number_STI_original_values_SEMANTICALLY_READ":0,
      "source_temperature_CTIRichness_BarkDiameter_original_values_SEMANTICALLY_READ":0,
      "original_site_taxon_specimen_values_NOT_EXPORTED":True,
      "new_biological_or_holdout_effect_COMPUTED":False,
      "status":"SOURCE_SWEDEN6_AUTHOR_BLOCK_PLOT_CONFLICT_DIAGNOSIS_COMPLETE_BIOLOGY_HOLD"
    }

def synthetic():
    import io
    climate=("Block;A;Plot;Shade;CTI\n"
             "1;PRIVATE_TEMP;11;1;99\n"
             "1;PRIVATE_TEMP;11;2;98\n"
             "1;PRIVATE_TEMP;12;1;98\n").encode()
    species=("Block;Plot;Log;Sampling_date;Species;Number;STI\n"
             "1;11;1;2021-07-10;SECRET_SPECIES;44;12.8\n"
             "1;12;2;2021-08-10;SECRET_SPECIES;22;13.1\n").encode()
    h1={"original_CSV_header_delimiter":"semicolon",
        "original_HEADER_exact_author_field_names":["Block","A","Plot","Shade","CTI"]}
    h2={"original_CSV_header_delimiter":"semicolon",
        "original_HEADER_exact_author_field_names":[
            "Block","Plot","Log","Sampling_date","Species","Number","STI"]}
    c=inspect_nonresponse_rows(climate,h1,("Block","Plot","Shade"),"climate")
    b=inspect_nonresponse_rows(species,h2,("Block","Plot","Log","Sampling_date"),"beetles")
    assert c["source_unique_numeric_Block_Plot_keys"]==2
    assert c["source_original_Block_Plot_pair_keys_outside_published_codebook"]==0
    assert c["source_climate_key_triplets_missing_from_three_per_observed_plot"]==3
    assert b["source_species_file_DISTINCT_log_ID_keys_with_positive_source_records"]==2
    assert b["source_species_file_original_sample_date_year_token_counts"]=={"2021":2}
    out=json.dumps({key:val for key,val in c.items() if not key.startswith("_private")})
    assert "PRIVATE_TEMP" not in out and "SECRET_SPECIES" not in out
    # Independent source codebook violation test, no real organism.
    wrong=b"Block;Plot;Shade\n1;1;1\n"
    h={"original_CSV_header_delimiter":"semicolon",
       "original_HEADER_exact_author_field_names":["Block","Plot","Shade"]}
    a=inspect_nonresponse_rows(wrong,h,("Block","Plot","Shade"),"climate")
    assert a["source_original_Block_Plot_pair_keys_outside_published_codebook"]==1
    print("SYNTHETIC_SWEDEN6_ORIGINAL_BLOCK_PLOT_CONFLICT_DIAGNOSIS_OUTCOME_SEALED_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out required")
    r={
      "schema":"structural.SLU_sweden6_original_blockplot_source_conflict_DIAG_v1",
      "precommit":PRESPEC,
      "author_original_repo_data_DOI":"10.5878/dhmc-bq15",
      "author_paper_DOI":"10.1111/ddi.13836",
      "previous_SLUpublisher_BLOCKPLOT_assumption_STOP_UNCHANGED":True,
      "source_original_species_environment_biological_values_SEMANTICALLY_READ":0,
      "source_original_treated_sunshade_as_HORIZONTAL_not_canopyheight":True,
      "source_historical_England_Finland_Carpathian_Thai_NEON_PREDICTS_BALA_GEB_outcomes_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        d=source_only()
        r["source_original_ID_conflict_diagnosis_aggregates_only"]=d
        r["status"]=d["status"]
    except (SourceStop,ValueError,csv.Error,UnicodeError) as e:
        r["status"]=str(e) if isinstance(e,SourceStop) else "SLU_ORIGINAL_SOURCE_ID_TRANSPORT_OR_PARSE_STOP"
        r["source_method_or_original_format_STOP_NOT_ECOLOGICAL_NULL"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"SLU_sweden6_original_BlockPlot_2025SOURCE_conflict_diagnosis.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SLU_SWEDEN6_ORIGINAL_BLOCKPLOT_CONFLICT_DIAGNOSIS",r["status"])
    print("NO_BEETLE_SPECIES_ORIGINAL_RESPONSE_OR_MICROCLIMATE_VALUES_SEMANTICALLY_READ")
if __name__=="__main__": main()
