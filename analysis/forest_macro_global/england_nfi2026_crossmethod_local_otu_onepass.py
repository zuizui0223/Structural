#!/usr/bin/env python3
"""ONE preregistered original England NFI 77-plot-year cross-method local OTU test.

Original 328-wide OTU rows were unopened at development/prespec time.
This is a method-conditional, region-year-stratified plot fingerprint test,
NOT ecological vertical niche/thermal/refuge/canopy-causal inference.
Original IDs, taxa, sequences and read-count rows never leave runner memory.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import argparse
import csv
from decimal import Decimal, InvalidOperation
import io
import json
import math
from pathlib import Path
import random
import re
import statistics
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
from england_nfi2026_otu_header_sampleid_sourcecrosswalk import first_csv_header

PRESPEC="docs/FOREST_NFI_ENGLAND_2026_CROSS_METHOD_LOCAL_OTU_SIGNATURE_EXPLORATORY_ONEPASS_PRESPEC_20261119.md"
SEED=20261119
N_PERM=9999
N_BOOT=4000
MIN_OTU_ROWS=100
METHODS=("Canopy","Malaise")
EXPECTED_YEARS={"2023":95,"2024":116,"2025":120,"2026":0}

def get_member_roles(zf):
    original=[x for x in zf.infolist() if not x.is_dir()]
    if len(original)!=2 or any(not x.filename.lower().endswith(".csv") for x in original):
        raise SourceStop("ORIGINAL_NFI2026_EXPECTED_EXACT_TWO_SOURCE_CSV_FILES")
    out={}
    for m in original:
        h=first_csv_header(zf,m)
        if len(h)==24:
            if tuple(h)!=AUTHOR_FIELDS:
                raise SourceStop("ORIGINAL_NFI2026_24_SAMPLE_AUTHOR_FIELDS_CHANGED")
            out["sample"]=(m,h)
        elif len(h)==328:
            out["otu"]=(m,h)
        else:
            raise SourceStop("ORIGINAL_NFI2026_WIDE_TABLE_HEADER_WIDTH_DRIFT")
    if set(out)!={"sample","otu"}:
        raise SourceStop("ORIGINAL_NFI2026_ONE_24_AND_ONE_328_SCHEMA_STOP")
    return out

def source_response_blind_admission(rows,wide_headers,strict=True):
    by_site=defaultdict(list)
    source_samples={}
    method_counts=Counter()
    years=Counter()
    regions=set()
    plots=set()
    n=0
    for r in rows:
        if None in r or set(r)!=set(AUTHOR_FIELDS):
            raise SourceStop("ORIGINAL_NFI2026_SOURCE_SAMPLE_ROW_FIELD_COUNT_DRIFT")
        n+=1
        sid=str(r["Sample_ID"] or "").strip()
        site=str(r["Plot_ID"] or "").strip()
        region=str(r["NFI_region"] or "").strip()
        year, year_bin=source_year(r["Year"])
        method=str(r["Trap_type"] or "").strip()
        if not sid or sid in source_samples:
            raise SourceStop("ORIGINAL_NFI2026_SOURCE_SAMPLE_ID_MISSING_OR_DUPLICATE")
        if method not in METHODS:
            raise SourceStop("ORIGINAL_NFI2026_SOURCE_TRAP_METHOD_LITERAL_DRIFT")
        if not region or not site or not year:
            raise SourceStop("ORIGINAL_NFI2026_SAMPLE_REGION_PLOT_YEAR_MISSING")
        yes=sequenced(r["Sample_sequenced"])=="yes"
        win,_=intervals_and_quality(r)
        source_samples[sid]={"seq":yes,"method":method}
        plots.add((region,site))
        regions.add(region)
        years[year_bin]+=1
        method_counts[method]+=1
        by_site[(region,site,year)].append({
            "sample":sid,"method":method,"seq":yes,"windows":win,
        })
    if strict and (
        n!=331 or method_counts!={"Canopy":166,"Malaise":165}
        or len(regions)!=8 or len(plots)!=83 or len(by_site)!=83
        or sum(v["seq"] for v in source_samples.values())!=316
        or any(years[k]!=EXPECTED_YEARS[k] for k in EXPECTED_YEARS)
    ):
        raise SourceStop("ORIGINAL_NFI2026_FIXED_331_316_83_8_FRAME_CHANGED")
    wide=[x.strip() for x in wide_headers]
    if len(wide)!=328 or len(set(wide))!=328:
        raise SourceStop("ORIGINAL_NFI2026_328_WIDE_HEADER_DUPLICATE_OR_LENGTH_DRIFT")
    wide_set=set(wide)
    yesids={s for s,x in source_samples.items() if x["seq"]}
    noids=set(source_samples)-yesids
    field_names=wide_set-set(source_samples)
    if strict and not (
        len(yesids)==316 and yesids <=wide_set and not noids&wide_set
        and len(field_names)==12
    ):
        raise SourceStop("ORIGINAL_NFI2026_316_SAMPLE_ID_EXACT_WIDE_HEADER_JOIN_STOP")
    sequence_fields=[
        x for x in field_names if re.search(r"(?i)sequence",x)
    ]
    if len(sequence_fields)!=1:
        raise SourceStop("ORIGINAL_NFI2026_SEQUENCE_SOURCE_COLUMN_NOT_UNIQUE")
    otu_sequence_field=sequence_fields[0]
    admitted=[]
    by_region_year=defaultdict(list)
    source_paired=0
    paired_yes=0
    for (region,plot,year),original in by_site.items():
        a=[x for x in original if x["method"]=="Canopy"]
        b=[x for x in original if x["method"]=="Malaise"]
        if a and b:source_paired+=1
        if not a or not b:continue
        qualified_C={
            x["sample"] for x in a if x["seq"] and x["sample"] in wide_set
            and any(y["seq"] and y["sample"] in wide_set and
                    overlap(x["windows"],y["windows"]) for y in b)
        }
        qualified_M={
            y["sample"] for y in b if y["seq"] and y["sample"] in wide_set
            and any(x["seq"] and x["sample"] in wide_set and
                    overlap(x["windows"],y["windows"]) for x in a)
        }
        if not qualified_C or not qualified_M:continue
        paired_yes+=1
        item={
           "region":region, "year":year, "site":plot,
           "C":qualified_C, "M":qualified_M,
        }
        admitted.append(item)
        by_region_year[(region,year)].append(item)
    if strict and (source_paired!=83 or paired_yes!=77):
        raise SourceStop("ORIGINAL_NFI2026_ORIGINAL_PAIRED_83_77_METHOD_METADATA_CHANGED")
    if any(len(x)<2 for x in by_region_year.values()):
        raise SourceStop("ORIGINAL_NFI2026_WITHIN_REGION_YEAR_EXCHANGEABILITY_SINGLETON_STOP")
    if strict and len({x["region"] for x in admitted})!=8:
        raise SourceStop("ORIGINAL_NFI2026_EIGHT_REGION_COHORT_CHANGED")
    return {
        "_private_admitted":admitted,
        "_private_groups":by_region_year,
        "_private_sample_headers":yesids,
        "_private_sequence_field":otu_sequence_field,
        "source_sample_metadata_original_records":n,
        "source_sequenced_yes_SampleID_header_exact_coverage":len(yesids&wide_set),
        "source_non_sample_328header_field_count":len(field_names),
        "source_eligible_original_paired_site_year_groups":len(admitted),
        "source_original_NFI_regions_in_paired_cohort":len({x["region"] for x in admitted}),
        "source_region_year_permutation_blocks":len(by_region_year),
        "source_region_year_min_sites_per_block":min((len(x) for x in by_region_year.values()),default=0),
        "source_eligible_plotyear_groups_by_year":{
           y:sum(x["year"]==y for x in admitted) for y in ("2023","2024","2025","2026")
        },
        "source_OTU_species_or_readcount_BIOLOGICAL_ROWS_OPENED_AT_ADMISSION":0,
    }

def source_readcount_to_binary(raw):
    txt=str(raw or "").strip()
    if not txt:
        return False,"blank"
    try:
        v=Decimal(txt)
    except (InvalidOperation,ValueError,OverflowError):
        raise SourceStop("ORIGINAL_NFI2026_OTU_CELL_NOT_NUMERIC")
    if not v.is_finite() or v<0 or v!=v.to_integral_value():
        raise SourceStop("ORIGINAL_NFI2026_OTU_CELL_NEGATIVE_NONFINITE_OR_FRACTIONAL")
    return v>0,"positive" if v>0 else "zero"

def original_otu_incidence_rows(source_stream,otu_headers,yes_header,sequence_field):
    response_by_sample={sid:set() for sid in yes_header}
    seen_sequence=set()
    response_rows=0
    valid=Counter()
    reader=csv.DictReader(source_stream,strict=True)
    if tuple(reader.fieldnames or ())!=tuple(otu_headers):
        raise SourceStop("ORIGINAL_NFI2026_OTU_CSV_BODY_HEADER_DRIFT")
    for row in reader:
        if None in row or set(row)!=set(otu_headers):
            raise SourceStop("ORIGINAL_NFI2026_OTU_ORIGINAL_CSV_ROW_WIDTH_STOP")
        seq=str(row[sequence_field] or "").strip()
        if not seq or seq in seen_sequence:
            raise SourceStop("ORIGINAL_NFI2026_OTU_SEQUENCE_ID_BLANK_OR_DUPLICATE_STOP")
        seen_sequence.add(seq)
        for sid in yes_header:
            detected,tag=source_readcount_to_binary(row[sid])
            valid[tag]+=1
            if detected:
                response_by_sample[sid].add(response_rows)
        response_rows+=1
        if response_rows>200000:
            raise SourceStop("ORIGINAL_NFI2026_UNEXPECTED_GT200K_OTU_SOURCE_ROWS")
    if response_rows<MIN_OTU_ROWS:
        raise SourceStop("ORIGINAL_NFI2026_FROZEN_MIN100_OTU_ROWS_NOT_MET")
    return response_by_sample,{
        "original_source_DISTINCT_sequence_OTU_row_count":response_rows,
        "source_316sequenced_sample_OTU_cells_blank":valid["blank"],
        "source_316sequenced_sample_OTU_cells_literal_numeric_zero":valid["zero"],
        "source_316sequenced_sample_OTU_cells_positive_reads":valid["positive"],
        "all_316_sample_columns_numeric_quality_passed":True,
        "original_sequence_or_taxon_values_EXPORTED":False,
    }

def jaccard(a,b):
    u=len(a|b)
    return (len(a&b)/u) if u else 0.0

def percentile(values,p):
    ordered=sorted(values)
    if not ordered:return float("nan")
    x=(len(ordered)-1)*p
    lo=int(math.floor(x)); hi=int(math.ceil(x))
    return ordered[lo]+(ordered[hi]-ordered[lo])*(x-lo)

def one_test(admission,response,n_perm=N_PERM,n_boot=N_BOOT,region_expect=None):
    by_group=admission["_private_groups"]
    if region_expect is not None and len({r for r,y in by_group})!=region_expect:
        raise SourceStop("NFI2026_PERMUTATION_EXPECTED_REGION_NUMBER_CHANGED")
    region_n=Counter()
    obs_by_region=Counter()
    null_by_region=Counter()
    fixed_matrices=[]
    site_detect_counts={"Canopy":[],"Malaise":[]}
    for (region,year),groups in by_group.items():
        if len(groups)<2:raise SourceStop("NFI2026_SINGLETON_PERMUTATION_GROUP")
        Cs=[];Ms=[]
        for info in groups:
            C=set().union(*(response[s] for s in info["C"]))
            M=set().union(*(response[s] for s in info["M"]))
            Cs.append(C);Ms.append(M)
            site_detect_counts["Canopy"].append(len(C))
            site_detect_counts["Malaise"].append(len(M))
        k=len(groups)
        sim=[[jaccard(Cs[i],Ms[j]) for j in range(k)] for i in range(k)]
        region_n[region]+=k
        obs_by_region[region]+=sum(sim[i][i] for i in range(k))
        null_by_region[region]+=sum(sum(sim[i])/k for i in range(k))
        fixed_matrices.append((region,sim))
    region_delta={
        region:(obs_by_region[region]-null_by_region[region])/region_n[region]
        for region in region_n
    }
    R=len(region_n)
    Tobs=statistics.fmean(obs_by_region[r]/region_n[r] for r in region_n)
    expected=statistics.fmean(null_by_region[r]/region_n[r] for r in region_n)
    delta=Tobs-expected
    rng=random.Random(SEED)
    exceed=0
    for it in range(n_perm):
        values=Counter()
        for region,mat in fixed_matrices:
            k=len(mat)
            labels=list(range(k))
            rng.shuffle(labels)
            values[region]+=sum(mat[i][labels[i]] for i in range(k))
        trial=statistics.fmean(values[r]/region_n[r] for r in region_n)
        if trial>=Tobs-1e-12:exceed+=1
    p=(1+exceed)/(n_perm+1)
    ds=list(region_delta.values())
    boot=[statistics.fmean(rng.choice(ds) for _ in ds) for _ in range(n_boot)]
    lo,hi=percentile(boot,.025),percentile(boot,.975)
    positive=sum(x>0 for x in ds)
    support=delta>0 and p<0.05 and lo>0 and positive>=6 and R==8
    return {
      "original_sample_method_matched_plot_years_observed":sum(region_n.values()),
      "original_NFI_regions_nonindependent_biome_n":R,
      "region_year_stratified_source_blocks":len(fixed_matrices),
      "original_method_site_detected_OTU_count_median":{
          k:statistics.median(v) if v else None for k,v in site_detect_counts.items()
      },
      "region_equal_original_within_site_Canopy_Malaise_OTU_Jaccard":Tobs,
      "region_equal_source_region_year_random_match_expected_Jaccard":expected,
      "region_equal_local_method_crosssite_excess_OTU_Jaccard":delta,
      "source_NFI_regions_with_positive_local_signature":positive,
      "fixed_9999_within_source_region_year_label_permutations":n_perm,
      "fixed_one_sided_conditional_permutation_p":p,
      "fixed_extreme_permutation_count":exceed,
      "fixed_4000_region_block_bootstrap_replicates":n_boot,
      "region_bootstrap95_delta_Jaccard":[lo,hi],
      "frozen_exploratory_support_threshold_met":support,
      "status":(
          "EXPLORATORY_NFI_FOREST_CROSS_METHOD_LOCAL_OTU_SIGNATURE_DIRECTIONAL_SUPPORT_ONLY"
          if support else "EXPLORATORY_NFI_FOREST_CROSS_METHOD_LOCAL_OTU_SIGNATURE_NOT_SUPPORTED"
      ),
      "original_method_Lindgren_canopy_vs_Malaise_subcanopy_PERFECTLY_CONFOUNDED":True,
      "species_richness_or_population_OTU_abundance_EFFECT_NOT_ESTIMATED":True,
      "global_forest_thermal_3D_effect_NOT_ESTIMATED":True,
    }

def original_once(source):
    with zipfile.ZipFile(source) as zf:
        role=get_member_roles(zf)
        otu_info,otu_header=role["otu"]
        sample_info,original_header=role["sample"]
        with zf.open(sample_info) as raw:
            with io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as inp:
                reader=csv.DictReader(inp,strict=True)
                if tuple(reader.fieldnames or ())!=AUTHOR_FIELDS:
                    raise SourceStop("ORIGINAL_NFI2026_SAMPLE_AUTHOR_HEADER_DRIFT")
                admitted=source_response_blind_admission(reader,otu_header,strict=True)
        # CRITICAL: ALL eligibility constraints above must pass before the
        # first OTU/sequence biological source row is opened.
        with zf.open(otu_info) as raw:
            with io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as inp:
                sample_response,read_quality=original_otu_incidence_rows(
                    inp,otu_header,admitted["_private_sample_headers"],
                    admitted["_private_sequence_field"]
                )
        effect=one_test(admitted,sample_response,region_expect=8)
    for key in list(admitted):
        if key.startswith("_private_"):admitted.pop(key)
    return {
        "source_original_response_blind_design_gates":admitted,
        "source_original_316_sample_OTU_row_quality":read_quality,
        "original_one_precommitted_cross_method_local_OTU_response_result":effect,
        "status":effect["status"],
        "original_328wide_biological_OTU_rows_opened_ONCE":True,
        "original_raw_OTU_or_site_rows_SAVED_TO_REPO_OR_ARTIFACT":False,
    }

def known_truth():
    assert source_readcount_to_binary("")[0] is False
    assert source_readcount_to_binary("0")[0] is False
    assert source_readcount_to_binary("4")[0] is True
    for bad in ("-1","0.3","Inf","NA"):
        try:
            source_readcount_to_binary(bad)
            raise AssertionError("expected_stop")
        except SourceStop:pass
    assert abs(jaccard({0,1},{1,2})-1/3)<1e-10
    assert jaccard(set(),set())==0
    # One completely synthetic 2-region × 2-sites + known perfectly shared
    # site signatures, no original or external organism data touched.
    synthetic={
      "_private_groups":defaultdict(list)
    }
    resp={}
    for r in ("r1","r2"):
        for n in range(2):
            i=len(resp)//2
            c=f"SYNTH_C_{r}_{n}";m=f"SYNTH_M_{r}_{n}"
            resp[c]={i*10+j for j in range(6)}
            resp[m]=set(resp[c])
            synthetic["_private_groups"][(r,"2024")].append(
                {"region":r,"year":"2024","site":f"fake_{r}_{n}",
                 "C":{c},"M":{m}}
            )
    x=one_test(synthetic,resp,n_perm=63,n_boot=80,region_expect=2)
    assert x["region_equal_local_method_crosssite_excess_OTU_Jaccard"]>0
    assert x["region_equal_original_within_site_Canopy_Malaise_OTU_Jaccard"]==1
    assert x["global_forest_thermal_3D_effect_NOT_ESTIMATED"]
    assert "SYNTH_" not in json.dumps(x)
    print("SYNTHETIC_77PLOT_CONTEXT_OTU_BINARY_JACCARD_REGION_STRATIFIED_ONEPASS_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:p.error("--out required")
    report={
      "schema":"structural.england_NFI2026_original_77_candidate_plotyear_OTU_crossmethod_onepass.v1",
      "precommit":PRESPEC,
      "source_original_forestry_commission_dataset_uuid":SOURCE_UUID,
      "original_source_archive_bytes":ORIGINAL_BYTES,
      "original_source_archive_SHA256":ORIGINAL_SHA256,
      "source_original_77paired_and_316columns_gate_FROZEN_BEFORE_OUTCOME":True,
      "source_layer_method_CONFOUNDED":True,
      "previous_biology_Finland_Carpathian_Chiu_PREDICTS_Thai_NEON_BALA_GEB_NOT_REOPENED":True,
      "no_species_or_site_identifiers_exported":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    with tempfile.TemporaryDirectory() as d:
        archive=Path(d)/"official_nfi2026.zip"
        try:
            n,sha,_=retrieve_original(archive)
            if n!=ORIGINAL_BYTES or sha!=ORIGINAL_SHA256:
                raise SourceStop("ORIGINAL_NFI2026_FROZEN_PUBLISHER_ZIP_CHANGED")
            report["onepass_original_source_ecological_test"]=original_once(archive)
            report["status"]=report["onepass_original_source_ecological_test"]["status"]
        except (SourceStop,urllib.error.URLError,TimeoutError,OSError,
                zipfile.BadZipFile,UnicodeError,ValueError,csv.Error) as exc:
            report["status"]=(str(exc) if isinstance(exc,SourceStop)
                              else "ORIGINAL_NFI2026_SOURCE_TRANSPORT_OR_ORIGINAL_CSV_STOP")
            report["source_or_method_quality_STOP_NOT_ecological_null"]=True
            report["no_eligible_cross_method_response_effect"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"NFI2026_frozen_original_77plot_OTU_crossmethod_local_signature.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("NFI2026_ORIGINAL_77PLOT_CROSSMETHOD_OTU_LOCAL_SIGNATURE",report["status"])
    print("NO_ORIGINAL_GENOMIC_TAXON_SITE_VALUES_EXPORTED")
if __name__=="__main__":main()
