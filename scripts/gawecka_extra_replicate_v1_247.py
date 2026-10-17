#!/usr/bin/env python3
"""v1.247: explicit paper 60 landscapes vs original-file 62 sensitivity.

A different, postresponse denominator-aware replay of already frozen v1.246
first-positive-detection definitions; no p-values or route/colonization claims.
"""
import argparse,csv,io,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
from gawecka_star_first_detection_v1_246 import (
    SOURCE_BLOB,SOURCE_META,SOURCE_LAYOUT,COMMUNITIES,git_blob,
    analyze,first_detected,center_and_far_category,parse_timestamp,
    nonnegative_int_or_missing
)
EXTRA={("BRBR_LIER_DIRA","1C",6),("BRBR_LIER_DIRA","1P",6)}
EXPECTED_ALL_ROWS=693
EXPECTED_CONTROL_ROWS=135
EXPECTED_EXTRA_ROWS=18
ORIGINAL_MAIN_60_LANDSCAPES=60
REPORTED_EXTRA_LANDSCAPES=2

def groups_of_raw(raw):
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    head=reader.fieldnames
    if head is None or any(f"patch{i}_BRBR" not in head for i in range(1,6)):
        raise ValueError("Original source columns not found")
    rows=list(reader)
    if len(rows)!=EXPECTED_ALL_ROWS:
        raise ValueError("Original observed author record count differs")
    for r in rows:
        if None in r:
            raise ValueError("Malformed original observation row")
    out=defaultdict(list)
    controls=0
    for row in rows:
        comm=row["community"];layout=row["landscape"]
        rep=nonnegative_int_or_missing(row["replica"])
        if layout=="5":
            controls+=1
        else:
            out[(comm,layout,rep)].append(row)
    if controls!=EXPECTED_CONTROL_ROWS or len(out)!=62:
        raise ValueError("Original source control or 62 non-control landscapes changed")
    for key,part in out.items():
        if len(part)!=9:
            raise ValueError("Original experimental landscape must have exactly 9 visits")
        if key[0] not in COMMUNITIES or key[1] not in SOURCE_LAYOUT or key[2] is None:
            raise ValueError("Unexpected treatment level")
    actual_extras={key for key in out if key[2]>5}
    if actual_extras!=EXTRA:
        raise ValueError("Original replicate-six treatment placement differs")
    return head,rows,out,controls

def reencode_rows(header,rows):
    f=io.StringIO(newline="")
    writer=csv.DictWriter(f,fieldnames=header,lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return f.getvalue().encode("utf-8")

def extra_landscape_records(key,source_rows):
    comm,layout,rep=key
    seq=[]
    for row in source_rows:
        t=parse_timestamp(row["date"],row["time"])
        counts={i:nonnegative_int_or_missing(row[f"patch{i}_BRBR"])
                for i in range(1,6)}
        seq.append((t,counts))
    seq.sort(key=lambda z:z[0])
    if len({t for t,x in seq})!=9:
        raise ValueError("Duplicate source time")
    sources=set(SOURCE_LAYOUT[layout])
    empty={x for x in range(1,6) if x not in sources}
    for p in range(1,6):
        c=seq[0][1][p]
        if c is None or (p in sources and c<=0) or (p in empty and c!=0):
            raise ValueError("Extra replicate initial source or zero patch differs")
    detections={p:first_detected(seq,p) for p in empty}
    if layout=="1P":
        if empty!={1,3,4,5}:
            raise AssertionError("Wrong geometry for extra 1P")
        center=detections[1]
        far=[detections[p] for p in (3,4,5)]
        category=center_and_far_category(center,far)
    else:
        category=None
    return {
        "community":comm,"layout":layout,"replica":rep,
        "n_visits":len(seq),
        "source_first_positivity_by_initially_empty_patch":{
            str(p):x for p,x in detections.items()},
        "focal_1P_first_center_vs_distal_category":category
    }

def evaluate(raw):
    head,rows,groups,control=groups_of_raw(raw)
    removed={(key) for key in groups if key in EXTRA}
    if removed!=EXTRA:
        raise ValueError("Pre-specified two original extra-replicate groups absent")
    main_rows=[
        row for row in rows
        if not (row["community"]=="BRBR_LIER_DIRA" and
                row["landscape"] in ("1C","1P") and
                nonnegative_int_or_missing(row["replica"])==6)]
    if len(main_rows)!=675 or len(rows)-len(main_rows)!=18:
        raise ValueError("Original source row scope expected 675 + 18")
    paper=analyze(reencode_rows(head,main_rows))
    if (paper["total_independent_spatial_treatment_landscapes"]!=60 or
        paper["one_peripheral_source_independent_landscapes"]!=15 or
        paper["original_empty_patch_series_total"]!=150):
        raise ValueError("Paper-described original design support not recovered")
    # Main 60 result is always reported, along with exact original 62.
    extras=[extra_landscape_records(key,groups[key]) for key in sorted(EXTRA)]
    extended=Counter(paper["focal_classification_counts"])
    for item in extras:
        if item["focal_1P_first_center_vs_distal_category"]:
            extended[item["focal_1P_first_center_vs_distal_category"]]+=1
    if sum(extended.values())!=16:
        raise ValueError("All-file 16 1P landscapes not reconciled")
    by_foodweb=dict(paper["focal_three_community_summary"])
    raw_all_62={
        "landscapes_total":62,
        "one_source_peripheral_landscapes":16,
        "initially_empty_patch_series":158,
        "distance1_empty_patch_series":110,
        "distance2_empty_patch_series":48,
        "1P_first_centre_vs_distal_category_counts":dict(extended),
        "all_two_extra_landscapes":extras,
        "BRBR_LIER_DIRA_1P_replicate_6_is_extra":True
    }
    return {
        "schema":"structural.gawecka_original_60_vs_62_first_detection_v1_247",
        "status":"PASS_ORIGINAL_SOURCE_DESIGN_DENOMINATOR_SENSITIVITY_POSTOUTCOME",
        "source_raw_git_blob_sha1":SOURCE_BLOB,
        "source_metadata_git_blob_sha1":SOURCE_META,
        "previous_v246_60_landscape_design_scientific_stop_retained":True,
        "original_source_records_including_5_source_control":len(rows),
        "source_original_5_source_control_records":control,
        "paper_described_60_landscapes":{
           "total_landscapes":paper["total_independent_spatial_treatment_landscapes"],
           "n_independent_focal_1P_landscapes":paper["one_peripheral_source_independent_landscapes"],
           "total_initially_empty_patches":paper["original_empty_patch_series_total"],
           "focal_first_centre_vs_distal_category_counts":paper["focal_classification_counts"],
           "all_15_independent_focal_landscapes":paper["per_focal_1P_landscape"],
           "all_60_landscape_sampling":paper["all_60_landscape_sampling_effort"],
           "all_150_empty_patch_first_positivity":paper["all_150_empty_patch_first_positivity_and_censoring"],
           "stratified_all_three_foodweb_community_results":paper["focal_three_community_summary"]
        },
        "all_62_original_source_landscape_sensitivity":raw_all_62,
        "authors_derived_Output_file_also_contains_62_landscapes":True,
        "declared_source_discrepancy_not_inferred_as_data_corruption":True,
        "sampling_first_positivity_not_verified_individual_migration_or_colonization":True,
        "nonobserved_centre_does_not_imply_disconnected_graph":True,
        "no_synchrony_measurement_or_spatial_hydra_intervention":True,
        "study_published_and_not_new_confirmatory_evidence":True,
        "GEB_scientific_HOLD":True,"eBird_used":False
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("author_checkout",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    root=args.author_checkout/"Data"
    raw=(root/"experiment_data.csv").read_bytes()
    met=(root/"metadata.txt").read_bytes()
    if git_blob(raw)!=SOURCE_BLOB or git_blob(met)!=SOURCE_META:
        raise ValueError("Published source version or file bytes changed")
    ans=evaluate(raw)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(ans,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":ans["schema"],"status":ans["status"],
        "paper_scope_15_focal":ans["paper_described_60_landscapes"]["focal_first_centre_vs_distal_category_counts"],
        "complete_source_16_focal":ans["all_62_original_source_landscape_sensitivity"]["1P_first_centre_vs_distal_category_counts"],
        "extra_replica_6":ans["all_62_original_source_landscape_sensitivity"]["all_two_extra_landscapes"]
    },sort_keys=True))
if __name__=="__main__":
    main()
