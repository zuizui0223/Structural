#!/usr/bin/env python3
"""Audit independent global *forest* vegetation plots in sPlotOpen v76.

The source for this adapter is the public, derived Netzschleuder CSV bundle of
iDiv sPlotOpen, not the original iDiv ZIP. Audit and modeling are DISTINCT:
this script reads plot node metadata, never reads species edges or fits models.
Field-contributor 'forest' is the primary eligibility label. 'is_forest'
depends on species growth forms and MUST NOT be used to select response plots.
Original plot IDs / raw coordinates / taxon values are never exported.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

NODE_TABLE="nodes.csv"

def flag(value):
    v=str(value or "").strip().lower()
    if v in ("true","t","yes","1","1.0"):return True
    if v in ("false","f","no","0","0.0"):return False
    return None

def number(value):
    try:
        v=float(value)
        return v if math.isfinite(v) else None
    except (TypeError,ValueError):
        return None

def is_nonempty(value):
    return str(value or "").strip().lower() not in ("","nan","na","none","null")

def plot_row(row):
    if flag(row.get("is_plot")) is not True:return None
    forest=flag(row.get("forest"))
    flora_growth=flag(row.get("is_forest"))
    height=number(row.get("height_trees_highest"))
    cover=number(row.get("cover_tree_layer"))
    area=number(row.get("releve_area"))
    richness=number(row.get("species_richness"))
    dataset=str(row.get("givd_id") or row.get("dataset") or "").strip()
    biome=str(row.get("biome") or "").strip()
    country=str(row.get("country") or "").strip()
    plant=str(row.get("plant_recorded") or "").strip().lower()
    # Contributor habitat label, never a species-derived forest classifier.
    eligible=forest is True
    allvascular=("all vascular plants" in plant)
    return {
        "site_id":str(row.get("name") or "").strip(),
        "source_dataset":dataset,
        "biome":biome,
        "country":country,
        "contributor_forest":forest,
        "growth_form_forest_diagnostic":flora_growth,
        "primary_source_forest":eligible,
        "all_vascular_plants":allvascular,
        "plant_recorded_scope":plant,
        "tree_height_valid":height is not None and height>0,
        "tree_cover_valid":cover is not None and cover>=0,
        "area_valid":area is not None and area>0,
        "richness_valid":richness is not None and richness>=0,
        "climate_pc_both_valid":number(row.get("soilclim_pc1")) is not None and number(row.get("soilclim_pc2")) is not None,
        "coordinate_valid":(
            (lambda a,b:a is not None and b is not None and abs(a)<=90 and abs(b)<=180)(
                number(row.get("latitude")),number(row.get("longitude")))),
        "coord_uncertainty_known":number(row.get("location_uncertainty")) is not None and number(row.get("location_uncertainty"))>=0,
        "survey_year_recorded":is_nonempty(row.get("date")) and str(row.get("date")).strip()!="-1",
        "naturalness_present":is_nonempty(row.get("naturalness")),
    }

def audit(zipfile_path,out):
    archive=Path(zipfile_path)
    if not archive.is_file():raise ValueError("source_zip_missing")
    sha=hashlib.sha256()
    with archive.open("rb") as f:
        for chunk in iter(lambda:f.read(2**20),b""):sha.update(chunk)
    all_count=0
    plots=0
    forest_plots=0
    growth_positive=0
    reference_mismatch=0
    field_coverage=Counter()
    groups=defaultdict(Counter)
    scope_counts=defaultdict(Counter)
    combos=defaultdict(Counter)
    all_biomes=defaultdict(Counter)
    site_ids=set()
    with zipfile.ZipFile(archive) as z:
        names=[n for n in z.namelist() if n.rsplit("/",1)[-1]==NODE_TABLE]
        if len(names)!=1:raise ValueError("unique_nodes_csv_not_found")
        with z.open(names[0]) as raw:
            txt=io.TextIOWrapper(raw,encoding="utf-8-sig",newline="",errors="replace")
            rd=csv.DictReader(txt)
            if rd.fieldnames:
                rd.fieldnames=[str(x).strip().lstrip("#").strip() for x in rd.fieldnames]
            if not rd.fieldnames or not {"is_plot","name","forest","is_forest","givd_id","biome","species_richness"}.issubset(rd.fieldnames):
                raise ValueError("sPlotOpen_v76_node_columns_incompatible:" + str((rd.fieldnames or [])[:18]))
            for original in rd:
                all_count+=1
                p=plot_row(original)
                if p is None:continue
                plots+=1
                sid=p["site_id"]
                if not sid or sid in site_ids:raise ValueError("original_sPlotOpen_plot_ID_missing_or_duplicate")
                site_ids.add(sid)
                if p["growth_form_forest_diagnostic"] is True:growth_positive+=1
                if p["contributor_forest"] is True and p["growth_form_forest_diagnostic"] is False:reference_mismatch+=1
                if p["contributor_forest"] is not True:continue
                forest_plots+=1
                sc=scope_counts[p["plant_recorded_scope"]]
                sc["forest_plots"]+=1
                sc["with_height"]+=int(p["tree_height_valid"])
                sc["with_cover"]+=int(p["tree_cover_valid"])
                sc["with_both"]+=int(p["tree_height_valid"] and p["tree_cover_valid"])
                sc["with_area"]+=int(p["area_valid"])
                sc["height_area_climate_richness_complete"]+=int(
                    p["tree_height_valid"] and p["area_valid"] and p["climate_pc_both_valid"]
                    and p["richness_valid"])
                sc["cover_area_climate_richness_complete"]+=int(
                    p["tree_cover_valid"] and p["area_valid"] and p["climate_pc_both_valid"]
                    and p["richness_valid"])
                for key in ("all_vascular_plants","tree_height_valid","tree_cover_valid","area_valid",
                            "richness_valid","climate_pc_both_valid","coordinate_valid",
                            "coord_uncertainty_known","survey_year_recorded","naturalness_present"):
                    field_coverage[key]+=int(p[key])
                if p["tree_height_valid"] and p["tree_cover_valid"]:
                    field_coverage["height_and_cover_valid"]+=1
                if not p["source_dataset"]:raise ValueError("forest_source_dataset_identity_missing")
                key=(p["source_dataset"],p["country"],p["biome"])
                g=groups[key]
                g["forest_plots"]+=1
                scope=p["plant_recorded_scope"]
                if scope=="not specified":
                    g["scope_not_specified"]+=1
                    g["scope_not_specified_both"]+=int(p["tree_height_valid"] and p["tree_cover_valid"])
                elif scope=="all vascular plants":
                    g["scope_complete_vascular_both"]+=int(p["tree_height_valid"] and p["tree_cover_valid"])
                elif scope.startswith("woody plants >="):
                    g["scope_declared_woody_both"]+=int(p["tree_height_valid"] and p["tree_cover_valid"])
                g["forest_all_vascular"]+=int(p["all_vascular_plants"])
                g["forest_with_height"]+=int(p["tree_height_valid"])
                g["forest_with_cover"]+=int(p["tree_cover_valid"])
                g["forest_with_both"]+=int(p["tree_height_valid"] and p["tree_cover_valid"])
                g["forest_with_height_complete_vascular"]+=int(
                    p["tree_height_valid"] and p["all_vascular_plants"] and p["area_valid"]
                    and p["richness_valid"] and p["climate_pc_both_valid"])
                g["forest_with_cover_complete_vascular"]+=int(
                    p["tree_cover_valid"] and p["all_vascular_plants"] and p["area_valid"]
                    and p["richness_valid"] and p["climate_pc_both_valid"])
                all_biomes[p["biome"]]["forest_plots"]+=1
    if all_count<1000 or plots<1000:raise ValueError("network_not_global_sPlotOpen")
    if not forest_plots:raise ValueError("no_contributor_forest_sites")
    # Study dataset x country x biome is a *stratum*, not an independent forest.
    # Publish counts by biome (not raw dataset identifiers, coordinates or site data).
    per_biome=[]
    for biome, c in sorted(all_biomes.items()):
        slices=[v for (d,ct,b),v in groups.items() if b==biome]
        per_biome.append({
            "biome":biome,
            "field_contributor_forest_plots":c["forest_plots"],
            "source_study_datasets":len({d for d,ct,b in groups if b==biome}),
            "independent_source_dataset_country_biome_strata_NOT_FORESTS":len(slices),
            "site_groups_with_10plus_forest_plots":sum(v["forest_plots"]>=10 for v in slices),
            "site_groups_with_10plus_complete_vascular_height_plots":sum(v["forest_with_height_complete_vascular"]>=10 for v in slices),
            "site_groups_with_10plus_complete_vascular_cover_plots":sum(v["forest_with_cover_complete_vascular"]>=10 for v in slices),
            "forest_height_available":sum(v["forest_with_height"] for v in slices),
            "forest_cover_available":sum(v["forest_with_cover"] for v in slices),
            "forest_height_and_cover":sum(v["forest_with_both"] for v in slices)
        })
    source_totals=defaultdict(Counter)
    for (d,c,b),counts in groups.items():
        source_totals[d].update(counts)
    source_rows=[]
    for d,t in sorted(source_totals.items()):
        row={
            "source_givd_dataset":d,
            "forest_plots":t["forest_plots"],
            "all_vascular_forest_plots":t["forest_all_vascular"],
            "contemporaneous_tree_height_plots":t["forest_with_height"],
            "contemporaneous_tree_cover_plots":t["forest_with_cover"],
            "contemporaneous_height_and_cover_plots":t["forest_with_both"],
            "complete_vascular_height_and_cover_plots":t["scope_complete_vascular_both"],
            "declared_woody_height_and_cover_plots":t["scope_declared_woody_both"],
            "UNSPECIFIED_survey_scope_height_and_cover_plots":t["scope_not_specified_both"],
            "country_biome_strata_NOT_independent_regions":sum(x[0]==d for x in groups),
            "community_canopy_evaluation_status":(
                "COMPLETE_VASCULAR_SCOPE_CANOPY_REVIEW" if t["scope_complete_vascular_both"]>=20 else
                "DECLARED_WOODY_SCOPE_CANOPY_REVIEW" if t["scope_declared_woody_both"]>=20 else
                "SAMPLING_SCOPE_UNSPECIFIED_REQUIRES_SOURCE_METHODS" if t["scope_not_specified_both"]>=20 else
                "INSUFFICIENT_MATCHED_CANOPY_WITH_KNOWN_SPECIES_SCOPE")
        }
        source_rows.append(row)
    report={
        "schema":"structural.global_forest_splotopen_v76_metadata_audit.v1",
        "source":"iDiv sPlotOpen v76 (2023-03-07), via public Netzschleuder CSV transform",
        "source_url":"https://networks.skewed.de/net/splotopen/files/splotopen.csv.zip",
        "archive_sha256":sha.hexdigest(),
        "all_nodes":all_count,
        "plot_nodes_unduplicated":plots,
        "source_contributor_forest_plots":forest_plots,
        "species_derived_growth_form_forest_plot_count_NOT_eligibility":growth_positive,
        "contributor_forest_vs_species_growth_form_false_mismatch":reference_mismatch,
        "forest_field_valid_counts":dict(field_coverage),
        "forest_sampling_scope_families":len(scope_counts),
        "source_datasets_with_complete_vascular_scope_at_least20_both_structure":sum(q["complete_vascular_height_and_cover_plots"]>=20 for q in source_rows),
        "source_datasets_with_declared_woody_scope_at_least20_both_structure":sum(q["declared_woody_height_and_cover_plots"]>=20 for q in source_rows),
        "source_datasets_with_unspecified_scope_at_least20_both_structure":sum(q["UNSPECIFIED_survey_scope_height_and_cover_plots"]>=20 for q in source_rows),
        "forest_source_datasets":len({d for d,c,b in groups}),
        "forest_source_dataset_country_biome_strata":len(groups),
        "forest_biome_label_count":len([b for b in all_biomes if b]),
        "forest_country_label_count":len({c for d,c,b in groups if c}),
        "eligible_forest_plant_communities_with_both_field_structure_variables":field_coverage["height_and_cover_valid"],
        "original_taxon_edges_read":0,
        "original_species_values_read":0,
        "species_growth_form_selection_leakage_avoided":True,
        "future_regional_leave_out_not_yet_scored":True,
        "2020_satellite_canopy_used_on_historic_plots":False,
        "independent_forest_regions_verified":0,
        "new_biological_effects_computed":False,
        "splotopen_environmental_balance_not_geographic_representation":True,
        "no_raw_locations_or_site_ids_exported":True,
        "eBird_used":False,
    }
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    with (out/"splotopen_forest_biome_metadata_support.csv").open("w",newline="",encoding="utf-8") as fd:
        w=csv.DictWriter(fd,fieldnames=list(per_biome[0]));w.writeheader();w.writerows(per_biome)
    scope_rows=[{"source_declared_survey_scope":scope, **dict(v)}
                for scope,v in sorted(scope_counts.items())]
    scope_fields=["source_declared_survey_scope", "forest_plots", "with_height","with_cover","with_both",
                  "with_area","height_area_climate_richness_complete",
                  "cover_area_climate_richness_complete"]
    with (out/"splotopen_forest_sampling_scope_audit.csv").open("w",newline="",encoding="utf-8") as fd:
        w=csv.DictWriter(fd,fieldnames=scope_fields)
        w.writeheader()
        w.writerows(scope_rows)
    with (out/"splotopen_GIVD_source_scope_followup_queue.csv").open("w",newline="",encoding="utf-8") as fd:
        w=csv.DictWriter(fd,fieldnames=list(source_rows[0]))
        w.writeheader()
        w.writerows(source_rows)
    (out/"splotopen_forest_source_meta_manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    print("biome aggregate:",json.dumps(per_biome,ensure_ascii=False))
    print("survey scope aggregate:",json.dumps(scope_rows,ensure_ascii=False))
    print("source eligibility statuses:",json.dumps(dict(Counter(q["community_canopy_evaluation_status"] for q in source_rows))))
    priorities=sorted((q for q in source_rows if q["community_canopy_evaluation_status"] !=
                       "INSUFFICIENT_MATCHED_CANOPY_WITH_KNOWN_SPECIES_SCOPE"),
                      key=lambda q:(q["community_canopy_evaluation_status"]!="DECLARED_WOODY_SCOPE_CANOPY_REVIEW",
                                    -q["contemporaneous_height_and_cover_plots"], q["source_givd_dataset"]))
    # Study source IDs and counts only: neither plot IDs nor coordinates/traits.
    print("original GIVD source method-review priorities:", json.dumps(priorities[:20]))
    return report,per_biome

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--archive",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    audit(a.archive,a.out)
