#!/usr/bin/env python3
"""Open Sweden hollow-tree beetle resource/microclimate source data schema audit.

Original SND/SLU DOI 10.5878/856g-v725 includes 9,766 observation rows of
ambient and internal logger measurements, tree-level beetle characteristics
and 500 recapture rows. Records are from one region and one species
(Osmoderma eremita), NOT a globally replicated canopy vs ground community.

Audit original TSV schema, source file SHA256, and candidate temporal / tree
join keys without fitting ecological responses or exporting coordinates,
individual/trap IDs, individual temperatures, or specimen-level data.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from collections import Counter
from pathlib import Path

SOURCE_ID="2022-71-1"
SOURCE_DOI="10.5878/856g-v725"
EXPECTED_FILES={
    "ambient":"OE_MC_publish_ambient.tsv",
    "internal":"OE_MC_publish_internal.tsv",
    "individual":"Specimens_data_publish_b_length-habitat-MC.tsv",
    "recapture":"Specimens_data_publish_Recapture.tsv"
}

def source_table(path):
    p=Path(path)
    if not p.exists() or p.stat().st_size<100:raise ValueError("missing_or_unexpectedly_tiny_open_TSV")
    try:
        with p.open("r",encoding="utf-8-sig",newline="") as f:
            d=csv.DictReader(f,delimiter="\t")
            if not d.fieldnames or len(d.fieldnames)<2:raise ValueError("source_not_TAB_delimited")
            original=d.fieldnames
            names=[str(x or "").strip() for x in original]
            if any(not x for x in names) or len(names)!=len(set(names)):
                raise ValueError("duplicated_or_blank_original_headers")
            d.fieldnames=names
            count=0
            row_empties=Counter()
            potential_samples=[]
            firstcol_first=[]
            for row in d:
                count+=1
                for k,v in row.items():
                    if v is None or v.strip().lower() in ("","na","nan","null","-999"):
                        row_empties[k]+=1
                if count<=4:
                    firstcol_first.append(str(row[names[0]] or "").strip())
                if count<=3:
                    potential_samples.append(tuple(
                        str(row.get(k,"") or "").strip()
                        for k in names[:3]
                    ))
    except UnicodeError:
        raise ValueError("source_TSV_not_UTF8")
    if count<100:raise ValueError("source_not_original_observation_table")
    hints=[name for name in names if re.search(
        r"(?i)date|time|year|tree|hollow|id|temp|ambient|degree|cavity|recapture|"
        r"lat|lon|body|length|mass|weight|beetle|capture|humidity|RH",
        name)]
    return {
        "file_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
        "data_rows":count,
        "source_field_count":len(names),
        "original_field_names":names,
        "candidate_join_or_environment_fields":hints,
        "source_missing_counts_by_field":dict(row_empties),
        "_internal_firstcol_first4":firstcol_first
    }

def audit(ambient,internal,individual,recapture):
    files={
        "ambient":source_table(ambient),
        "internal":source_table(internal),
        "individual":source_table(individual),
        "recapture":source_table(recapture),
    }
    # Only in-memory first-column diagnostic: not a proven time join.
    a,b=files["ambient"],files["internal"]
    first4_identical=(a["_internal_firstcol_first4"]==b["_internal_firstcol_first4"])
    for val in files.values():val.pop("_internal_firstcol_first4",None)
    report={
        "schema":"structural.forest_hollow_beetle_Sweden_original_source_inventory.v1",
        "source_DOI":SOURCE_DOI,
        "source_SND_dataset_id":SOURCE_ID,
        "source_published_version":"1",
        "source_species":"Osmoderma eremita",
        "original_data_files":files,
        "catalog_advertised_ambient_rows":9766,
        "catalog_advertised_internal_rows":9766,
        "catalog_advertised_specimen_data_rows":256,
        "catalog_advertised_recapture_rows":500,
        "climate_sample_row_count_match":a["data_rows"]==b["data_rows"],
        "first_four_records_first_field_match":first4_identical,
        "candidate_tree_and_time_join_verified":False,
        "one_species_not_forest_beetle_species_community":True,
        "true_canopy_understorey_trap_strata_not_present":True,
        "hollow_resource_constraint_is_study_context_not_inferred_movement":True,
        "new_ecological_microclimate_effect_or_thermal_refuge_test_scored":False,
        "original_raw_beetle_or_logger_values_and_site_identifiers_exported":False,
        "eBird_used":False
    }
    return report


def run(ambient,internal,individual,recapture,out):
    report=audit(ambient,internal,individual,recapture)
    path=Path(out);path.mkdir(parents=True,exist_ok=True)
    (path/"Sweden_hollow_beetle_climate_source_manifest.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("ambient","internal","individual","recapture","out"):
        p.add_argument("--"+key,required=True)
    a=p.parse_args()
    run(a.ambient,a.internal,a.individual,a.recapture,a.out)
