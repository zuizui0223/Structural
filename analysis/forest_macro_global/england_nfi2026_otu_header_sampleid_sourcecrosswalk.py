#!/usr/bin/env python3
"""Original 328-OTU CSV FIRST HEADER ↔ author 24-source Sample_ID exact join.

NEVER opens original OTU/taxon response values or its CSV data rows.
Only original 24-field sampling metadata rows are parsed in private runner.
All original sample / plot / region ID values stay runner private.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import io
import json
from pathlib import Path
import re
import tempfile
import urllib.error
import zipfile

from england_nfi2026_canopy_subcanopy_source_gate import (
    SOURCE_UUID, retrieve_original, SourceStop
)
from england_nfi2026_plot_trap_year_metadata_only import (
    ORIGINAL_BYTES, ORIGINAL_SHA256, AUTHOR_FIELDS,
    sequenced, source_year, intervals_and_quality, overlap
)

PRESPEC = "docs/FOREST_NFI_ENGLAND_2026_328COL_SAMPLE_HEADER_EXACT_JOIN_PRESPEC_20261119.md"
EXPECTED_SOURCE_24_IDS=331
EXPECTED_SOURCE_SEQ_YES=316
EXPECTED_SOURCE_PLOTS=83
EXPECTED_SOURCE_REGIONS=8
EXPECTED_CANDIDATE_BOTH=83
EXPECTED_CANDIDATE_BOTH_SEQ_OVERLAP=77
EXPECTED_SAMPLES_BY_METHOD={"Canopy":166,"Malaise":165}
FAMILIES={
    "OTU_identifier":re.compile(r"(?i)(^otu$|otu[_ ]?id|marker|sequence[_ ]?id)"),
    "DNA_sequence":re.compile(r"(?i)(sequence|dna[_ ]?seq|consensus|nucleotide)"),
    "taxonomic_rank":re.compile(r"(?i)(kingdom|phylum|class|order|family|genus|species|taxon)"),
    "IUCN_or_invasive_status":re.compile(r"(?i)(iucn|red[_ ]?list|invasive|status)"),
    "sample_detection_summary":re.compile(r"(?i)(sample.?count|number.?samples|frequency|occurren)"),
}

def first_csv_header(zf,member):
    with zf.open(member) as f:
        raw=f.readline(8*1024*1024+1)
    if len(raw)>8*1024*1024 or b"\n" not in raw:
        raise SourceStop("SOURCE_NFI2026_OTU_FIRST_LINE_HEADER_BOUND_STOP")
    try:
        return next(csv.reader([raw.decode("utf-8-sig").rstrip("\r\n")],strict=True))
    except (ValueError,UnicodeError,csv.Error,StopIteration):
        raise SourceStop("SOURCE_NFI2026_OTU_OR_SAMPLE_HEADER_PARSE_STOP") from None

def reconcile(sample_rows,otu_headers,strict_original=True):
    raw_samples={}
    groups=defaultdict(list)
    seq=Counter()
    methods=Counter()
    years=Counter()
    regions=set()
    original_plots=set()
    n=0
    for row in sample_rows:
        if None in row or set(row)!=set(AUTHOR_FIELDS):
            raise SourceStop("SOURCE_NFI2026_24COL_SAMPLE_RECORD_GRAMMAR_STOP")
        n+=1
        ident=str(row["Sample_ID"] or "").strip()
        if not ident or ident in raw_samples:
            raise SourceStop("SOURCE_NFI2026_ORIGINAL_SAMPLE_ID_BLANK_OR_DUPLICATE")
        method=str(row["Trap_type"] or "").strip()
        if method not in ("Canopy","Malaise"):
            raise SourceStop("SOURCE_NFI2026_ORIGINAL_METHOD_CATEGORY_DRIFT")
        y,ybin=source_year(row["Year"])
        year=y or ybin
        region=str(row["NFI_region"] or "").strip()
        plot=str(row["Plot_ID"] or "").strip()
        windows,_=intervals_and_quality(row)
        is_yes=sequenced(row["Sample_sequenced"])=="yes"
        raw_samples[ident]={"method":method,"year":year,"seq":is_yes}
        methods[method]+=1
        if is_yes:seq[method]+=1
        years[ybin]+=1
        if region:regions.add(region)
        if region and plot:original_plots.add((region,plot))
        if region and plot and y:
            groups[(region,plot,y)].append({
              "sample":ident, "method":method,
              "seq_yes":is_yes,"windows":windows,
            })
        if n>100000:raise SourceStop("SOURCE_NFI2026_ORIGINAL_SAMPLE_RECORD_COUNT_TOO_BIG")
    if strict_original and not (
        n==EXPECTED_SOURCE_24_IDS and len(raw_samples)==331
        and sum(seq.values())==EXPECTED_SOURCE_SEQ_YES
        and methods==EXPECTED_SAMPLES_BY_METHOD
        and len(regions)==EXPECTED_SOURCE_REGIONS
        and len(original_plots)==EXPECTED_SOURCE_PLOTS
        and len(groups)==EXPECTED_SOURCE_PLOTS
        and [years[y] for y in ("2023","2024","2025","2026")]==[95,116,120,0]
    ):
        raise SourceStop("SOURCE_NFI2026_PRIOR_ORIGINAL_SAMPLE_METHOD_FRAME_DRIFT")
    # No header strings, sample IDs, source taxon names or site/region values
    # are written out, even when a data column is unexpectedly non-sample.
    stripped=[h.strip() for h in otu_headers]
    if len(stripped)!=328:
        raise SourceStop("SOURCE_NFI2026_ORIGINAL_OTU_WIDE_328_HEADER_COUNT_DRIFT")
    distinct_headers=set(stripped)
    duplicate_headers=len(stripped)-len(distinct_headers)
    sample_ids=set(raw_samples)
    matched_sample_headers=distinct_headers & sample_ids
    matching_yes={ident for ident in matched_sample_headers if raw_samples[ident]["seq"]}
    matching_no=matched_sample_headers-matching_yes
    sequenced_id_set={ident for ident,r in raw_samples.items() if r["seq"]}
    other_headers=distinct_headers-sample_ids
    # Header-only lexical family flags; NO exact non-sample header text exported.
    header_field_family_counts={
        key:sum(bool(pattern.search(field)) for field in other_headers)
        for key,pattern in FAMILIES.items()
    }
    paired_source=0
    seq_paired_source=0
    matched_seq_paired=0
    by_year_seq_paired=Counter()
    matched_region=Counter()
    for (region,plot,year),obs in groups.items():
        a=[q for q in obs if q["method"]=="Canopy"]
        b=[q for q in obs if q["method"]=="Malaise"]
        if not a or not b:continue
        paired_source+=1
        yes_overlap=any(
            x["seq_yes"] and y["seq_yes"] and overlap(x["windows"],y["windows"])
            for x in a for y in b
        )
        if yes_overlap:seq_paired_source+=1
        matched_overlap=any(
            x["seq_yes"] and y["seq_yes"]
            and x["sample"] in matching_yes and y["sample"] in matching_yes
            and overlap(x["windows"],y["windows"])
            for x in a for y in b
        )
        if matched_overlap:
            matched_seq_paired+=1
            by_year_seq_paired[year]+=1
            matched_region[region]+=1
    if strict_original and (paired_source!=83 or seq_paired_source!=77):
        raise SourceStop("SOURCE_NFI2026_PRIOR_83_AND_77_ORIGINAL_SAMPLE_EFFORT_DRIFT")
    report={
       "schema":"structural.england_NFI2026_original_328wide_FIRST_HEADER_SampleID_exact_join.v1",
       "source_metadata_24col_original_sample_rows":n,
       "source_original_sample_sequenced_yes_ids":len(sequenced_id_set),
       "source_original_sample_sequenced_yes_by_method":{k:seq[k] for k in ("Canopy","Malaise")},
       "original_328_wide_CSV_first_header_field_count":len(stripped),
       "original_328_wide_CSV_unique_header_field_count":len(distinct_headers),
       "original_328_wide_CSV_duplicate_header_fields":duplicate_headers,
       "source_original_331_Sample_ID_values_exactly_matched_to_wide_HEADER":len(matched_sample_headers),
       "source_original_316_sequenced_yes_Sample_ID_values_exact_header_match":len(matching_yes),
       "source_original_316_yes_ids_MISSING_from_wide_header":len(sequenced_id_set-matching_yes),
       "source_original_15_unsequenced_ID_values_UNEXPECTEDLY_matched":len(matching_no),
       "source_original_328_header_nonmatching_sampleID_DISTINCT_field_count":len(other_headers),
       "source_original_non_sample_header_field_semantic_COUNTS_only":header_field_family_counts,
       "source_sample_columns_matched_to_header_by_original_method":{
          method:sum(raw_samples[s]["method"]==method for s in matching_yes)
          for method in ("Canopy","Malaise")
       },
       "source_83_candidate_region_plot_year_groups_with_BOTH_methods":paired_source,
       "source_77_candidate_region_plot_year_groups_with_BOTH_method_yes_concurrent":seq_paired_source,
       "source_candidate_region_plot_year_groups_with_exact_header_MATCHED_both_yes_concurrent":matched_seq_paired,
       "source_exact_matched_both_yes_concurrent_plotyear_count_by_source_YEAR":{
          str(y):by_year_seq_paired[str(y)] for y in (2023,2024,2025,2026)
       },
       "source_NFI_regions_with_exact_matched_both_yes_concurrent_plotyears":len(matched_region),
       "source_per_region_exact_matched_both_yes_concurrent_plotyears_ANONYMOUS_SORTED":sorted(matched_region.values()),
       "source_original_328_field_species_OTU_readcount_DATA_ROWS_OPENED":0,
       "source_original_24_sample_metadata_rows_ONLY":n,
       "source_original_328_header_sample_ID_OR_taxon_field_names_EXPORTED":False,
       "source_original_sample_site_coordinates_taxa_gene_values_EXPORTED":False,
       "source_delocalization_NOT_SITE_ID":True,
       "source_method_and_vertical_layer_PERFECTLY_CONFOUNDED":True,
       "source_field_PlotID_independent_forest_sites_NOT_CERTIFIED":True,
       "source_original_OTU_species_counts_and_any_ecological_score_NOT_COMPUTED":True,
    }
    source_join_valid=(
        len(sequenced_id_set)==316 and len(matching_yes)==316
        and len(sequenced_id_set-matching_yes)==0
        and duplicate_headers==0 and matched_seq_paired>=77
    )
    report["status"]=(
        "SOURCE_NFI2026_OTU_HEADER_SAMPLE_ID_EXACT_JOIN_PASS_NO_BIOLOGY"
        if source_join_valid
        else "SOURCE_NFI2026_OTU_HEADER_SAMPLE_JOIN_HOLD"
    )
    return report

def original_archive_headers_plus_sample_rows(source,strict_original=True):
    with zipfile.ZipFile(source) as zf:
        infos=[x for x in zf.infolist() if not x.is_dir()]
        if len(infos)!=2 or any(not x.filename.lower().endswith(".csv") for x in infos):
            raise SourceStop("SOURCE_NFI2026_ORIGINAL_TWO_CSV_FILE_DRIFT")
        sample_info=None
        otu_info=None
        for info in infos:
            h=first_csv_header(zf,info)
            if len(h)==24:
                if tuple(h)!=AUTHOR_FIELDS:
                    raise SourceStop("SOURCE_NFI2026_SAMPLE_HEADER_ORIGINAL_FIELDS_DRIFT")
                sample_info=info
            elif len(h)==328:otu_info=info
            else:raise SourceStop("SOURCE_NFI2026_NOT_24_PLUS_328_SCHEMA")
        if sample_info is None or otu_info is None:
            raise SourceStop("SOURCE_NFI2026_MISSING_SOURCE_SAMPLE_OR_OTU_HEADER")
        otu_header=first_csv_header(zf,otu_info)  # EXACT FIRST ROW ONLY.
        with zf.open(sample_info) as binary:
            with io.TextIOWrapper(binary,encoding="utf-8-sig",newline="") as inp:
                metadata=csv.DictReader(inp,strict=True)
                if tuple(metadata.fieldnames or ())!=AUTHOR_FIELDS:
                    raise SourceStop("SOURCE_NFI2026_24_METADATA_FIELDS_DRIFT")
                return reconcile(metadata,otu_header,strict_original)

def synthetic_test():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"mock.zip"
        a=[]
        def row(sid,typ,seq):
            o={k:"" for k in AUTHOR_FIELDS}
            o.update({
                "Sample_ID":sid,"Plot_ID":"private_plot_A","NFI_region":"private_region",
                "Year":"2024","Trap_type":typ,"Sample_sequenced":seq,
                "Activation_1_date":"2024-06-01","Collection_1_date":"2024-06-20",
                "SW_x_coordinates":"private_coord","Delocation_unique_ID":"private_deloc"
            })
            return o
        a=[row("PRIVATE_C","Canopy","Yes"),row("PRIVATE_M","Malaise","Yes"),
           row("PRIVATE_N","Canopy","No")]
        sio=io.StringIO(newline="")
        writer=csv.DictWriter(sio,fieldnames=AUTHOR_FIELDS)
        writer.writeheader();writer.writerows(a)
        otu=["Kingdom","Family"]+["TaxonField"+str(i) for i in range(324)]+["PRIVATE_C","PRIVATE_M"]
        assert len(otu)==328
        with zipfile.ZipFile(p,"w") as z:
            z.writestr("original_sample_source.csv",sio.getvalue())
            z.writestr("original_biological_source.csv",
                ",".join(otu)+"\nPRIVATE_OTU_VALUE_NEVER_OPENED")
        r=original_archive_headers_plus_sample_rows(p,strict_original=False)
        assert r["source_original_316_sequenced_yes_Sample_ID_values_exact_header_match"]==2
        assert r["source_original_15_unsequenced_ID_values_UNEXPECTEDLY_matched"]==0
        assert r["source_candidate_region_plot_year_groups_with_exact_header_MATCHED_both_yes_concurrent"]==1
        assert r["source_original_328_field_species_OTU_readcount_DATA_ROWS_OPENED"]==0
        joined=json.dumps(r)
        for raw in ("PRIVATE_C","PRIVATE_M","PRIVATE_N","private_plot","private_region",
                    "PRIVATE_OTU_VALUE_NEVER_OPENED","private_coord"):
            assert raw not in joined
    print("SYNTHETIC_EXACT_NFI_328HEADER_24META_SAMPLEID_CROSSWALK_NO_OTU_ROWS_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic_test()
    if a.test:return
    if a.out is None:p.error("--out required")
    obj={
      "schema":"structural.england_NFI2026_original_sample_header_source_gate.v1",
      "precommit":PRESPEC,
      "source_official_UUID":SOURCE_UUID,
      "official_original_zip_bytes":ORIGINAL_BYTES,
      "official_original_zip_sha256":ORIGINAL_SHA256,
      "no_328wide_original_taxon_OR_readcount_biology_ROWS_READ":True,
      "old_Finland_Carpathian_Chiu_PREDICTS_Thai_NEON_BALA_GEB_original_scores_NOT_REOPENED":True,
      "method_layer_unchanged_CONFOUNDED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/"original_zip"
        try:
            n,sha,_=retrieve_original(f)
            if n!=ORIGINAL_BYTES or sha!=ORIGINAL_SHA256:
                raise SourceStop("SOURCE_NFI2026_PRECOMMITTED_SOURCE_ARCHIVE_SHA_SIZE_CHANGED")
            obj["source_header_only_sample_source_matching_aggregates"]=original_archive_headers_plus_sample_rows(f)
            obj["status"]=obj["source_header_only_sample_source_matching_aggregates"]["status"]
        except (SourceStop,urllib.error.URLError,TimeoutError,OSError,
                zipfile.BadZipFile,csv.Error,UnicodeError,ValueError) as exc:
            obj["status"]=(str(exc) if isinstance(exc,SourceStop)
                           else "SOURCE_NFI2026_HEADER_CROSSWALK_TRANSPORT_OR_PARSE_STOP")
            obj["source_taxonomy_or_original_format_stop_NOT_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"England_NFI2026_328header_316_sampleID_exact_source_gate.json").write_text(
        json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("NFI2026_ONLY_OTU_FIRST_HEADER_EXACT_SAMPLEID_JOIN",obj["status"])
    print("NO_ORIGINAL_SPECIES_OR_OTU_DATA_ROWS_OPENED")
if __name__=="__main__":main()
