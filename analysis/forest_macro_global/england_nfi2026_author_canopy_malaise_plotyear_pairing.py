#!/usr/bin/env python3
"""Author-literal Canopy×Malaise same-plot/year and effort metadata audit.

This is a separately frozen correction to the sampling METHOD CODEBOOK,
not a revision of any species response or a causal vertical habitat model.
No 328-column taxon response values are ever read.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import io
import json
from pathlib import Path
import statistics
import tempfile
import urllib.error
import zipfile

from england_nfi2026_canopy_subcanopy_source_gate import (
    SOURCE_UUID, retrieve_original, SourceStop
)
from england_nfi2026_plot_trap_year_metadata_only import (
    ORIGINAL_BYTES, ORIGINAL_SHA256, AUTHOR_FIELDS,
    intervals_and_quality, numeric, source_year, sequenced, overlap
)

PRESPEC="docs/FOREST_NFI_ENGLAND_2026_ORIGINAL_CANOPY_MALAISE_PLOT_YEAR_PAIRING_PRESPEC_20261119.md"
METHODS=("Canopy","Malaise")
YEARS=("2023","2024","2025","2026")
EXPECTED_YEARS={"2023":95,"2024":116,"2025":120,"2026":0}

def read_sample_rows(source, strict_original=True):
    with zipfile.ZipFile(source) as zf:
        members=[x for x in zf.infolist() if not x.is_dir()]
        if len(members)!=2 or any(not x.filename.lower().endswith(".csv") for x in members):
            raise SourceStop("SOURCE_NFI2026_ORIGINAL_EXACT_TWO_CSV_FRAME_STOP")
        names_widths=[]
        chosen=None
        for member in members:
            with zf.open(member) as f:
                header=f.readline(8*1024*1024+1)
            if len(header)>8*1024*1024 or b"\n" not in header:
                raise SourceStop("SOURCE_NFI2026_CSV_FIRST_HEADER_INVALID")
            try:
                names=next(csv.reader([header.decode("utf-8-sig").rstrip("\r\n")],strict=True))
            except (UnicodeError,ValueError,csv.Error,StopIteration):
                raise SourceStop("SOURCE_NFI2026_CSV_HEADER_PARSE_STOP") from None
            names_widths.append(len(names))
            if len(names)==24:
                if tuple(names)!=AUTHOR_FIELDS:
                    raise SourceStop("SOURCE_NFI2026_24_FIELDS_POSITION_DRIFT")
                chosen=member
        if sorted(names_widths)!=[24,328] or chosen is None:
            raise SourceStop("SOURCE_NFI2026_ORIGINAL_OTU_SAMPLE_FILES_CHANGED")
        with zf.open(chosen) as binary:
            with io.TextIOWrapper(binary,encoding="utf-8-sig",newline="") as fin:
                r=csv.DictReader(fin,strict=True)
                if tuple(r.fieldnames or ())!=AUTHOR_FIELDS:
                    raise SourceStop("SOURCE_NFI2026_ORIGINAL_24COL_VALUES_SCHEMA_STOP")
                return report_onepass(r,strict_original=strict_original)

def report_onepass(rows,strict_original=True):
    by_group=defaultdict(list)
    unique_sample=set()
    region_plots=set()
    plotyear=set()
    regions=set()
    n=0
    method_counts=Counter()
    years=Counter()
    sequenced_counts=Counter()
    phase_quality=Counter()
    source_letter_keys=set()
    sample_id_duplicate_or_blank=0
    for r in rows:
        if None in r or set(r)!=set(AUTHOR_FIELDS):
            raise SourceStop("SOURCE_NFI2026_ORIGINAL_SAMPLING_ROW_WIDTH_CHANGED")
        n+=1
        if n>100000:raise SourceStop("SOURCE_NFI2026_SAMPLING_ROWS_TOO_MANY")
        sid=str(r["Sample_ID"] or "").strip()
        region=str(r["NFI_region"] or "").strip()
        plot=str(r["Plot_ID"] or "").strip()
        year,year_bin=source_year(r["Year"])
        method=str(r["Trap_type"] or "").strip()
        if method not in METHODS:
            raise SourceStop("SOURCE_NFI2026_EXACT_AUTHOR_TRAP_TYPE_LITERAL_CHANGED")
        if not sid or sid in unique_sample:
            sample_id_duplicate_or_blank+=1
        else:
            unique_sample.add(sid)
        method_counts[method]+=1
        years[year_bin]+=1
        if region:
            regions.add(region)
        if region and plot:
            region_plots.add((region,plot))
        if region and plot and year:
            plotyear.add((region,plot,year))
            windows,q=intervals_and_quality(r)
            phase_quality.update(q)
            seq=sequenced(r["Sample_sequenced"])=="yes"
            if seq:sequenced_counts[method]+=1
            letter=str(r["Trap_letter"] or "").strip()
            if letter:source_letter_keys.add((region,plot,year,method,letter))
            by_group[(region,plot,year)].append({
                "method":method,
                "windows":windows,
                "yes":seq,
                "height":numeric(r["Trap_height_m"]),
                "tree":str(r["Tree_species"] or "").strip(),
                "station":str(r["Surveyor_station"] or "").strip(),
            })
    if strict_original and (
        n!=331 or method_counts!={"Canopy":166,"Malaise":165}
        or len(regions)!=8 or len(region_plots)!=83
        or len(unique_sample)!=331 or sample_id_duplicate_or_blank!=0
        or any(years[y]!=EXPECTED_YEARS[y] for y in YEARS)
        or sum(sequenced_counts.values())!=316
        or phase_quality["valid_deployment_phase"]!=885
    ):
        raise SourceStop("SOURCE_NFI2026_PRIOR_FROZEN_AUTHOR_SAMPLE_FRAME_DRIFT")
    pairs=0
    paired_both_seq=0
    concurrent=0
    concurrent_both_seq=0
    paired_both_height=0
    paired_height_strictly_separated=0
    paired_shared_tree=0
    paired_shared_station=0
    per_year=Counter()
    per_year_concurrent=Counter()
    per_region=Counter()
    per_region_concurrent=Counter()
    method_samp_per_siteyear=defaultdict(list)
    per_siteyear_method_mult_counts=Counter()
    for (region,plot,year),obs in by_group.items():
        top=[x for x in obs if x["method"]=="Canopy"]
        low=[x for x in obs if x["method"]=="Malaise"]
        method_samp_per_siteyear["Canopy"].append(len(top))
        method_samp_per_siteyear["Malaise"].append(len(low))
        per_siteyear_method_mult_counts[f"canopy_{len(top)}_malaise_{len(low)}"]+=1
        if not top or not low:
            continue
        pairs+=1
        per_year[year]+=1
        per_region[region]+=1
        if any(a["yes"] for a in top) and any(b["yes"] for b in low):
            paired_both_seq+=1
        if any(overlap(a["windows"],b["windows"]) for a in top for b in low):
            concurrent+=1
            per_year_concurrent[year]+=1
            per_region_concurrent[region]+=1
        if any(a["yes"] and b["yes"] and overlap(a["windows"],b["windows"])
               for a in top for b in low):
            concurrent_both_seq+=1
        ht=[x["height"] for x in top if x["height"] is not None]
        hl=[x["height"] for x in low if x["height"] is not None]
        if ht and hl:
            paired_both_height+=1
            if min(ht)>max(hl):
                paired_height_strictly_separated+=1
        if {x["tree"] for x in top if x["tree"]}&{x["tree"] for x in low if x["tree"]}:
            paired_shared_tree+=1
        if ({x["station"] for x in top if x["station"]} &
            {x["station"] for x in low if x["station"]}):
            paired_shared_station+=1
    report={
       "schema":"structural.NFI2026_author_Canopy_Malaise_source_plotyear_pairing.v1",
       "original_source_metadata_sample_rows":n,
       "original_sample_IDs_nonblank_unique":len(unique_sample),
       "source_trap_type_exact_literal_rows":{k:method_counts[k] for k in METHODS},
       "original_year_2023to2026_record_counts":{y:years[y] for y in YEARS},
       "original_source_n_regions":len(regions),
       "source_region_plotID_unique_candidate_plots_not_certified_physical":len(region_plots),
       "source_region_plotID_year_candidate_units":len(plotyear),
       "source_original_metadata_trap_letter_unique_n_by_plotyear_type":len(source_letter_keys),
       "source_source_year_site_method_multiplicities_ANONYMOUS":dict(sorted(per_siteyear_method_mult_counts.items())),
       "source_region_plotyear_BOTH_source_methods":pairs,
       "source_region_plotyear_BOTH_with_overlapping_original_deployments":concurrent,
       "source_region_plotyear_BOTH_with_at_least_one_sequenced_sample_in_each":paired_both_seq,
       "source_region_plotyear_BOTH_with_overlapping_yes_yes_original_deployment":concurrent_both_seq,
       "source_region_plotyear_BOTH_with_numeric_trap_height_on_each_method":paired_both_height,
       "source_region_plotyear_BOTH_canopy_all_numeric_heights_above_Malaise":paired_height_strictly_separated,
       "source_region_plotyear_BOTH_with_same_nonmissing_associated_tree_name":paired_shared_tree,
       "source_region_plotyear_BOTH_with_same_nonmissing_surveyor_station":paired_shared_station,
       "source_region_plotyear_BOTH_per_year":{y:per_year[y] for y in YEARS},
       "source_region_plotyear_OVERLAP_per_year":{y:per_year_concurrent[y] for y in YEARS},
       "source_region_n_with_BOTH_methods":len(per_region),
       "source_BOTH_plotyear_counts_per_region_ANONYMOUS_SORTED":sorted(per_region.values()),
       "source_OVERLAP_plotyear_counts_per_region_ANONYMOUS_SORTED":sorted(per_region_concurrent.values()),
       "source_original_sequenced_yes_sample_rows_by_trap_method":{k:sequenced_counts[k] for k in METHODS},
       "source_original_valid_deployment_windows_1to3":phase_quality["valid_deployment_phase"],
       "source_source_sample_rows_without_original_ID_or_year_or_plot_COUNTED_NOT_DROPPED":n-len(unique_sample),
       "original_328col_OTU_species_sample_response_rows_READ":0,
       "original_24col_metadata_sample_records_READ":n,
       "original_site_IDs_tree_labels_dates_coordinates_sample_values_NOT_OUTPUT":True,
       "original_metadata_coordinate_columns_NOT_SEMANTICALLY_USED":True,
       "source_delocation_IS_NOT_USED_AS_PLOT":True,
       "source_author_field_PlotID_physical_plot_independence_NOT_VERIFIED":True,
       "source_layer_vs_trap_method_PERFECTLY_CONFOUNDED":True,
       "new_species_biodiversity_or_thermal_3D_effect_estimated":False,
    }
    if not all([
        concurrent<=pairs,
        concurrent_both_seq<=min(concurrent,paired_both_seq),
        paired_both_height<=pairs,
        paired_shared_tree<=pairs,
        paired_shared_station<=pairs,
        sum(per_region.values())==pairs,
        sum(per_year.values())==pairs,
    ]):
        raise SourceStop("SOURCE_NFI2026_PAIRED_SAMPLE_COUNT_INVARIANT_FAIL")
    report["status"]="SOURCE_NFI2026_AUTHOR_CANOPY_MALAISE_PLOT_YEAR_EFFORT_AUDIT_PASS"
    return report

def synthetic_known_truth():
    import datetime as dt
    with tempfile.TemporaryDirectory() as d:
        archive=Path(d)/"fake_source.zip"
        def row(sid,typ,plot,seq,first,last,tree,st,height):
            r={k:"" for k in AUTHOR_FIELDS}
            r.update({
                "Sample_ID":sid,"Trap_type":typ,"NFI_region":"PRIVATE_REGION",
                "Plot_ID":plot,"Year":"2024","Sample_sequenced":seq,
                "Activation_1_date":first,"Collection_1_date":last,
                "Surveyor_station":st,"Tree_species":tree,"Trap_height_m":height,
                "Delocation_unique_ID":"PRIVATE_DELOCALIZATION",
                "SW_x_coordinates":"PRIVATE_GEO_COORDINATE",
                "Trap_letter":"A" if typ=="Canopy" else "B",
            })
            return r
        src=[
            row("private_canopy_A","private_plot_A","private_plot_A", "yes","2024-06-01","2024-06-10","Oak","S1","18"),
        ]
        # Explicit records: same source plot/year, overlapping valid deployment.
        src=[
            row("PRIVATE_C1","Canopy","PRIVATE_PLOT_A","yes","2024-06-01","2024-06-10","oak","station1","18"),
            row("PRIVATE_M1","Malaise","PRIVATE_PLOT_A","yes","2024-06-05","2024-06-15","oak","station1","2"),
            row("PRIVATE_C2","Canopy","PRIVATE_PLOT_B","no","2024-07-01","2024-07-10","pine","station2","10"),
        ]
        buf=io.StringIO(newline="")
        out=csv.DictWriter(buf,fieldnames=AUTHOR_FIELDS)
        out.writeheader();out.writerows(src)
        with zipfile.ZipFile(archive,"w") as z:
            z.writestr("private_sampledata.csv",buf.getvalue())
            z.writestr("PRIVATE_species.csv",
                ",".join("Taxon_"+str(i) for i in range(328))+"\nPRIVATE_SPECIES_BIOLOGICAL_VALUES\n")
        r=read_sample_rows(archive,strict_original=False)
        assert r["source_region_plotID_year_candidate_units"]==2
        assert r["source_region_plotyear_BOTH_source_methods"]==1
        assert r["source_region_plotyear_BOTH_with_overlapping_original_deployments"]==1
        assert r["source_region_plotyear_BOTH_with_overlapping_yes_yes_original_deployment"]==1
        assert r["source_region_plotyear_BOTH_with_numeric_trap_height_on_each_method"]==1
        assert r["source_region_plotyear_BOTH_canopy_all_numeric_heights_above_Malaise"]==1
        assert r["source_region_plotyear_BOTH_with_same_nonmissing_associated_tree_name"]==1
        assert r["source_region_plotyear_BOTH_with_same_nonmissing_surveyor_station"]==1
        assert r["original_328col_OTU_species_sample_response_rows_READ"]==0
        j=json.dumps(r)
        for token in ("PRIVATE_PLOT","PRIVATE_GEO_COORDINATE","PRIVATE_REGION",
                      "PRIVATE_SPECIES_BIOLOGICAL_VALUES","PRIVATE_DELOCALIZATION"):
            assert token not in j
    print("SYNTHETIC_NFI2026_EXACT_AUTHOR_CANOPY_MALAISE_SAME_YEAR_OVERLAP_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    synthetic_known_truth()
    if args.test:return
    if args.out is None:parser.error("--out required")
    report={
        "schema":"structural.NFI2026_canopy_malaise_meta_sourceonly_onepass.v1",
        "precommit":PRESPEC,
        "source_official_NFI_UUID":SOURCE_UUID,
        "original_exact_archive_sha256":ORIGINAL_SHA256,
        "original_exact_archive_bytes":ORIGINAL_BYTES,
        "earlier_Lindgren_literal_0_and_Other166_CLASSIFICATION_PRESERVED":True,
        "author_original_Trap_type_literals_Canopy166_Malaise165_VERIFIED":True,
        "publisher_Lindgren_canopy_Malaise_subcanopy_METHOD_CONFOUNDED":True,
        "original_328col_biological_response_rows_READ":0,
        "all_earlier_Finland_Carpathian_Chiu_PREDICTS_Thai_NEON_BALA_GEB_outcomes_UNCHANGED":True,
        "eBird_used":False,
        "TinyFish_used":False,
    }
    with tempfile.TemporaryDirectory() as d:
        source=Path(d)/"official_archive.zip"
        try:
            size,sha,_=retrieve_original(source)
            if size!=ORIGINAL_BYTES or sha!=ORIGINAL_SHA256:
                raise SourceStop("SOURCE_NFI2026_ORIGINAL_PUBLISHER_ZIP_FINGERPRINT_DRIFT")
            report["original_sample_only_Canopy_Malaise_PlotID_year_results"]=read_sample_rows(source)
            report["status"]=report["original_sample_only_Canopy_Malaise_PlotID_year_results"]["status"]
        except (SourceStop,urllib.error.URLError,TimeoutError,OSError,ValueError,
                csv.Error,zipfile.BadZipFile,UnicodeError) as e:
            report["status"]=str(e) if isinstance(e,SourceStop) else (
                "SOURCE_NFI2026_SOURCE_SAMPLE_METADATA_PARSE_OR_TRANSPORT_STOP"
            )
            report["no_ecological_species_or_paired_result_eligible"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"England_NFI2026_author_Canopy_Malaise_plotyear_sourceonly.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("NFI2026_SOURCE_ONLY_CANOPY_MALAISE_PLOT_YEAR",report["status"])
    print("NO_ORIGINAL_328_COLUMN_TAXON_DATA_OR_ECOLOGICAL_EFFECT_OPENED")
if __name__=="__main__":main()
