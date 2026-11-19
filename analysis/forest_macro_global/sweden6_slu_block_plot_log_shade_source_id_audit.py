#!/usr/bin/env python3
"""Original Sweden6 SLU published Block/Plot/Log→Shade identifiers ONLY.

FROZEN pre-outcome physical-unit inspection. No Species, Number, STI, CTI,
Richness, micro/macro temperature, Bark, Diameter or numerical effects read.
Author codebook maps exact Log 1..15 into three HORIZONTAL shade treatments.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from sweden6_slu_original_three_file_header_gate import (
    official_get, ORIGINAL_URLS, first_header_only, SourceStop
)

PRESPEC="docs/FOREST_SWEDEN6_SOURCE_PUBLISHED_29PLOT_NAMED_KEY_IDENTITY_AUDIT_PRESPEC_20261119.md"
AUTHOR_LOGS={
  1:(1,4,7,10,13),
  2:(2,5,8,11,14),
  3:(3,6,9,12,15)
}
LOG_TO_SHADE={v:k for k,vs in AUTHOR_LOGS.items() for v in vs}
BLOCK_PLOTS={
    1:set(range(11,16)),
    2:set(range(6,11)),
    3:set(range(16,21)),
    4:set(range(21,26)),
    5:set(range(1,6)),
    6:set(range(26,31))
}
EXPECTED_SPECIES_HASH="a67a905ee05e3994f3e85bc29f8b68fbb314677d6e5a6cc4cd479b2b9d87ec9a"
EXPECTED_SPECIES_BYTES=157911
REQUIRED_CLIMATE=("Block","Plot","Shade")
REQUIRED_BEETLES=("Block","Plot","Log","Sampling_date")
CSV_SEPS={"comma":",","semicolon":";","tab":"\t"}
YEAR_RX=re.compile(r"(?<!\d)((?:19|20)\d\d)(?!\d)")
INT_RX=re.compile(r"^(?:[1-9]|[1-9][0-9])$")

def source_num(raw,kind):
    text=str(raw).strip()
    if not INT_RX.fullmatch(text):
        raise SourceStop("SLU_SOURCE_"+kind+"_NOT_EXACT_POSITIVE_INTEGER")
    return int(text)

def get_columns(blob,expected,mandatory):
    audit=first_header_only(blob,expected)
    names=audit["original_HEADER_exact_author_field_names"]
    if any(names.count(c)!=1 for c in mandatory):
        raise SourceStop("SLU_SOURCE_"+str(expected)+"_HEADER_REQUIRED_AUTHOR_NAMED_KEY_MISSING")
    return audit,dict((k,names.index(k)) for k in mandatory)

def id_rows_from_original_bytes(blob,meta,cols,mode):
    # csv.reader uses all source tokens as transport but only selected
    # original source ID positions are semantically inspected.
    try:
        stream=io.StringIO(blob.decode("utf-8-sig"),newline="")
    except UnicodeError:
        raise SourceStop("SLU_SOURCE_ORIGINAL_CSV_UTF8_DATA_TRANSPORT_STOP") from None
    reader=csv.reader(stream,delimiter=CSV_SEPS[meta["original_CSV_header_delimiter"]],strict=True)
    try:
        actual=next(reader)
    except (StopIteration,csv.Error):
        raise SourceStop("SLU_ORIGINAL_SOURCE_FIRSTLINE_MISSING") from None
    if tuple(actual)!=tuple(meta["original_HEADER_exact_author_field_names"]):
        raise SourceStop("SLU_ORIGINAL_CSV_FIRSTLINE_MISMATCH")
    n=0
    block_plots=set()
    combos=set()
    duplicate_source_keys=0
    block_counts=Counter()
    shade_counts=Counter()
    sample_dates=Counter()
    non2021_dates=0
    source_logs=set()
    invalid_year_or_blank_date=0
    for row in reader:
        n+=1
        if len(row)!=meta["original_header_declared_field_count"]:
            raise SourceStop("SLU_ORIGINAL_CSV_SOURCE_ROW_FIELD_COUNT_DRIFT")
        if n>10000:
            raise SourceStop("SLU_ORIGINAL_SOURCE_ROW_COUNT_EXCEEDS_10000")
        block=source_num(row[cols["Block"]],"Block")
        plot=source_num(row[cols["Plot"]],"Plot")
        if block not in BLOCK_PLOTS or plot not in BLOCK_PLOTS[block]:
            raise SourceStop("SLU_ORIGINAL_SOURCE_BLOCK_PLOT_OUTSIDE_AUTHOR_PUBLISHED_CODEBOOK")
        block_plots.add((block,plot))
        block_counts[block]+=1
        if mode=="climate":
            shade=source_num(row[cols["Shade"]],"Shade")
            if shade not in (1,2,3):
                raise SourceStop("SLU_ORIGINAL_SOURCE_SHADE_NOT_AUTHOR_CATEGORY_1_2_3")
            key=(block,plot,shade)
        else:
            log=source_num(row[cols["Log"]],"Log")
            if log not in LOG_TO_SHADE:
                raise SourceStop("SLU_ORIGINAL_SOURCE_LOG_OUTSIDE_AUTHOR_CODEBOOK_1_15")
            shade=LOG_TO_SHADE[log]
            source_logs.add((block,plot,log))
            key=(block,plot,shade)
            date=str(row[cols["Sampling_date"]]).strip()
            matches=set(YEAR_RX.findall(date))
            if len(matches)!=1:
                invalid_year_or_blank_date+=1
            else:
                yr=next(iter(matches))
                sample_dates[yr]+=1
                if yr!="2021":non2021_dates+=1
        shade_counts[shade]+=1
        if mode=="climate" and key in combos:
            duplicate_source_keys+=1
        combos.add(key)
    if n==0:raise SourceStop("SLU_ORIGINAL_CSV_EMPTY_SOURCE_BODY")
    result={
        "original_source_source_identity_sample_record_ROWS":n,
        "source_original_unique_Block_Plot_candidate_physical_sites":len(block_plots),
        "source_original_source_regions_with_field_records":len({x[0] for x in block_plots}),
        "source_original_n_plot_code_slots_allowed_30_not_claimed_observed":30,
        "source_original_per_Block_plot_count_ANONYMOUS_SORTED":
             sorted(Counter(k[0] for k in block_plots).values()),
        "source_original_unique_Block_Plot_Shade_COMBINATION_KEYS":len(combos),
        "source_original_shade_category_counts_original_records":{
            str(i):shade_counts[i] for i in (1,2,3)
        },
        "source_original_source_ID_codebook_uses_exact_author_Block_Plot_and_Log_Shade":True,
        "source_original_plot_sample_IDs_NOT_EXPORTED":True,
        "source_original_species_abundance_STI_original_values_SEMANTICALLY_READ":0,
        "source_original_CTIRichness_temperature_resource_original_values_SEMANTICALLY_READ":0,
    }
    if mode=="climate":
        expected={(b,p,s) for b,p in block_plots for s in (1,2,3)}
        result.update({
         "source_original_duplicate_climate_Block_Plot_Shade_rows":duplicate_source_keys,
         "source_original_expected_three_shades_per_observed_plot_candidate_n":len(expected),
         "source_original_missing_shade_keys_for_observed_Block_Plot_sites":len(expected-combos),
         "source_original_unexpected_shade_keys_OUTSIDE_OBSERVED_PLOTS":len(combos-expected),
         "source_original_88rows_vs_published87theoretical_DISAGREEMENT":
              n!=87,
        })
    else:
        result.update({
          "source_original_distinct_Block_Plot_Log_with_atleastone_source_record":len(source_logs),
          "original_recorded_positive_beetle_Log_dates_NUMBER_NOT_INFERRED":True,
          "source_original_species_record_year_token_counts":dict(sorted(sample_dates.items())),
          "source_original_species_record_no_unique_fourdigit_year":invalid_year_or_blank_date,
          "source_original_species_records_year_not2021_if_parsed":non2021_dates,
          "source_original_435_placed_logs_not_claimed_identical_to_positive_log_ids":True,
        })
    result["_private_block_plots"]=block_plots
    result["_private_shade_keys"]=combos
    return result

def source_only_once(get=official_get):
    names=("boreal_forest_climate_data.csv","specieslist_xylo.csv")
    files={}
    for name in names:
        data=get(ORIGINAL_URLS[name][0])
        files[name]=data
    if (len(files["specieslist_xylo.csv"])!=EXPECTED_SPECIES_BYTES or
        hashlib.sha256(files["specieslist_xylo.csv"]).hexdigest()!=EXPECTED_SPECIES_HASH):
        raise SourceStop("SLU_ORIGINAL_SPECIES_FILE_SHA_OR_BYTE_SIZE_DRIFT")
    schema_climate,climate_cols=get_columns(files[names[0]],12,REQUIRED_CLIMATE)
    schema_beetles,beetle_cols=get_columns(files[names[1]],7,REQUIRED_BEETLES)
    if schema_beetles["original_CSV_header_delimiter"]!="semicolon":
        raise SourceStop("SLU_ORIGINAL_SPECIES_SEMICOLON_DID_NOT_PERSIST")
    if (schema_beetles["original_HEADER_exact_author_field_names"]!=
        ["Block","Plot","Log","Sampling_date","Species","Number","STI"]):
        raise SourceStop("SLU_ORIGINAL_BEETLE_SEVEN_AUTHOR_FIELDS_CHANGED")
    # All FIRST HEADER gates above pass before entering any original ID row.
    climate=id_rows_from_original_bytes(files[names[0]],schema_climate,climate_cols,"climate")
    beetles=id_rows_from_original_bytes(files[names[1]],schema_beetles,beetle_cols,"beetles")
    matches=climate["_private_shade_keys"] & beetles["_private_shade_keys"]
    missing=beetles["_private_shade_keys"]-climate["_private_shade_keys"]
    climate_plots=climate["_private_block_plots"]
    beetle_plots=beetles["_private_block_plots"]
    clean_identity=(
        len(climate_plots)==29
        and climate["source_original_per_Block_plot_count_ANONYMOUS_SORTED"]==[4,5,5,5,5,5]
        and len(climate["_private_shade_keys"])==87
        and climate["source_original_duplicate_climate_Block_Plot_Shade_rows"]==0
        and climate["source_original_missing_shade_keys_for_observed_Block_Plot_sites"]==0
        and len(missing)==0 and beetle_plots<=climate_plots
    )
    for result in (climate,beetles):
        result.pop("_private_block_plots",None)
        result.pop("_private_shade_keys",None)
    return {
       "source_publisher_original_species_file_bytes":EXPECTED_SPECIES_BYTES,
       "source_publisher_original_species_sha256":EXPECTED_SPECIES_HASH,
       "source_publisher_original_climate_file_bytes":len(files[names[0]]),
       "source_publisher_original_climate_sha256":hashlib.sha256(files[names[0]]).hexdigest(),
       "source_publisher_climate_firstheader_source_fields_ONLY":schema_climate["original_HEADER_exact_author_field_names"],
       "source_original_species_7_field_semicolon_VERIFIED":True,
       "source_original_author_log_shade_dictionary15_to3_FROZEN_BEFORE_SAMPLE_IDS":True,
       "source_original_climate_ID_unit_checks":climate,
       "source_original_species_ID_unit_checks":beetles,
       "source_original_source_shade_keys_with_positive_beetle_RECORDS_matching_climate_metadata":len(matches),
       "source_original_beetle_shade_keys_NOT_PRESENT_IN_CLIMATE_metadata":len(missing),
       "source_author_first_header_and_source_identity_only":True,
       "source_original_biological_or_numeric_environment_eyes_opened":False,
       "source_truly_clean_29plot_87shade_one_to_one_eligibility":clean_identity,
       "status":("SOURCE_SWEDEN6_29PLOT_87PLOTSHADE_METHOD_IDS_ONE_TO_ONE_READY_NO_BIOLOGY"
                 if clean_identity else
                 "SOURCE_SWEDEN6_SOURCE_IDENTITY_METADATA_DIAG_PASS_BIOLOGY_HOLD"),
    }

def known_truth():
    assert len(LOG_TO_SHADE)==15
    assert set(LOG_TO_SHADE)==set(range(1,16))
    assert all(len(v)==5 for v in AUTHOR_LOGS.values())
    assert LOG_TO_SHADE[1]==LOG_TO_SHADE[4]==1
    assert LOG_TO_SHADE[2]==LOG_TO_SHADE[5]==2
    assert LOG_TO_SHADE[3]==LOG_TO_SHADE[15]==3
    assert sum(len(v) for v in BLOCK_PLOTS.values())==30
    assert source_num("7","Log")==7
    for bad in ("0","16","1.0","-1","A"):
        try:
            x=source_num(bad,"Log")
            assert x not in LOG_TO_SHADE
        except SourceStop:pass
    import csv as _csv
    climate_fields=["R","Block","Plot","Shade","Micro","CTI","Bark","Diameter","Tmacro","Aspect","Rich","Abund"]
    b=(";".join(climate_fields)+"\n"+
       "private;1;11;1;SECRET_CLIMATE;42;16;21;18;2;3;4\n").encode()
    aa,cc=get_columns(b,12,REQUIRED_CLIMATE)
    r=id_rows_from_original_bytes(b,aa,cc,"climate")
    assert r["source_original_unique_Block_Plot_candidate_physical_sites"]==1
    assert r["source_original_expected_three_shades_per_observed_plot_candidate_n"]==3
    assert r["source_original_CTIRichness_temperature_resource_original_values_SEMANTICALLY_READ"]==0
    assert "SECRET_CLIMATE" not in json.dumps({k:v for k,v in r.items() if not k.startswith("_private")})
    s=("Block;Plot;Log;Sampling_date;Species;Number;STI\n"+
       "1;11;1;2021-04-10;SECRET_SPECIES;93;6.2\n").encode()
    bb,bc=get_columns(s,7,REQUIRED_BEETLES)
    u=id_rows_from_original_bytes(s,bb,bc,"beetles")
    assert u["source_original_distinct_Block_Plot_Log_with_atleastone_source_record"]==1
    assert u["source_original_species_record_year_token_counts"]=={"2021":1}
    assert "SECRET_SPECIES" not in json.dumps({k:v for k,v in u.items() if not k.startswith("_private")})
    print("SYNTHETIC_SLU_BLOCK_PLOT_LOG_SHADE_IDENTITIES_NO_BIOLOGICAL_VALUES_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--test",action="store_true")
    a.add_argument("--out",type=Path)
    args=a.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:a.error("--out required")
    result={
      "schema":"structural.SLU_sweden6_author_named29plot_source_metadata_only.v1",
      "precommit":PRESPEC,
      "source_original_publication_DOI":"10.1111/ddi.13836",
      "source_original_deposit_DOI":"10.5878/dhmc-bq15",
      "historical_6species_header_and_climate_first3_source_STOPS_RETAINED":True,
      "source_original_beetle_Species_Number_STI_and_climate_CTIRichness_read":0,
      "source_2020_temperature_2021_emergence_time_MISMATCH_NOT_FORGOTTEN":True,
      "source_original_3_shades_HORIZONTALLY_NOT_VERTICALLY_separated":True,
      "historical_England_Finland_Carpathian_PREDICTS_Thai_NEON_BALA_GEB_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        d=source_only_once()
        result["original_source_site_and_experiment_identity_anonymous_ONLY"]=d
        result["status"]=d["status"]
    except SourceStop as e:
        result["status"]=str(e)
        result["original_key_or_file_quality_STOP_not_ecological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"SLU_sweden6_original_29plot_logshade_site_identity_only.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SLU_SWEDEN6_PUBLISHED_29PLOT_LOG_SHADE_SITE_METHOD_SOURCE",result["status"])
    print("NO_ORIGINAL_BEETLE_ABUNDANCE_TAXON_OR_CLIMATE_NUMERIC_VALUE_READ")
if __name__=="__main__":
    main()
