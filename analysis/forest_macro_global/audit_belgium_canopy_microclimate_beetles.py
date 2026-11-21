#!/usr/bin/env python3
"""Source-frozen, original Dryad Belgium canopy/microclimate/ground-beetle audit.

Independent of Thai source. 36 within-one-forest plots, two pitfall traps/plot,
2022 season plus 2022-23 daily Tmicro/VWC and canopy/wood plot properties.
Only metadata and anonymous counts are exported: source PlotID, coordinates,
raw taxon labels, individual records are never written.

The published Verdonck et al. 2025 analysis already studied canopy buffering
and ground beetles (doi:10.1111/1365-2664.70137). Here we check independent
input availability/identity, not claim a newly discovered thermal process.
"""
from __future__ import annotations

import argparse,csv,datetime,hashlib,json,math,re,statistics
from collections import Counter,defaultdict
from pathlib import Path

DOI="10.5061/dryad.tmpg4f5b0"
SOURCE_LINKS={
    "plot":"https://datadryad.org/downloads/file_stream/4194844",
    "micro":"https://datadryad.org/downloads/file_stream/4194845",
    "arth":"https://datadryad.org/downloads/file_stream/4194846",
}
NA={"","na","n/a","null","none","nan","-999","-9999"}

def read_semicolon(path):
    f=Path(path)
    if not f.is_file():raise ValueError("dryad_file_missing:"+str(f))
    with f.open(encoding="utf-8-sig",newline="") as inp:
        reader=csv.DictReader(inp,delimiter=";")
        keys=reader.fieldnames or []
        if not keys or len(keys)<3:raise ValueError("not_an_original_semicolon_csv")
        keys=[k.strip() for k in keys]
        if len(set(keys))!=len(keys):raise ValueError("source_duplicate_field_names")
        reader.fieldnames=keys
        rows=[{k:(v or "").strip() for k,v in row.items() if k is not None} for row in reader]
    if not rows:raise ValueError("original_empty_csv")
    return rows,keys

def parse_float(value):
    s=str(value or "").strip()
    if s.lower() in NA:return None
    if "," in s and "." in s:
        # Locale decimal comma and dot-thousands is not safely inferred.
        raise ValueError("ambiguous_decimal_separator")
    if "," in s:s=s.replace(",",".")
    try:
        z=float(s)
    except ValueError:
        return None
    return z if math.isfinite(z) else None

def date_of(value):
    s=str(value or "").strip()
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y","%Y/%m/%d",
                "%m/%d/%Y","%Y-%m-%d %H:%M:%S"):
        try:return datetime.datetime.strptime(s[:19],fmt).date()
        except ValueError:pass
    return None

def survey_fields(rows, required):
    d=rows[0]
    missing=set(required)-set(d)
    if missing:raise ValueError("source_schema_missing_columns:"+",".join(sorted(missing)))

def audit(plot_path,micro_path,arth_path):
    plots,pc=read_semicolon(plot_path)
    micro,mc=read_semicolon(micro_path)
    arth,ac=read_semicolon(arth_path)
    survey_fields(plots,("PlotID","TreeSpecies","CanopyCover","BasalArea","DeadWood"))
    survey_fields(micro,("PlotID","Date","Tmacro","Tmicro","VWC"))
    survey_fields(arth,("PlotID","TrapID","Date","Period","SpeciesGroup","Species","Count"))
    ps={r["PlotID"]:r for r in plots}
    if "" in ps or len(ps)!=len(plots):raise ValueError("source_plot_ID_missing_or_duplicate")
    if len(plots)!=36:raise ValueError("source_original_36_plots_not_reproduced")
    plotfields=Counter()
    canopy=[]
    tree=Counter()
    for p in plots:
        tree[p["TreeSpecies"]]+=1
        for key in ("CanopyCover","BasalArea","DeadWood","LitterDepth","VegetationCoverage",
                    "VegetationRichness"):
            if key in p and parse_float(p[key]) is not None:plotfields[key]+=1
        cv=parse_float(p["CanopyCover"])
        if cv is not None:canopy.append(cv)
    if len(canopy)<25:raise ValueError("most_original_canopy_cover_unavailable")
    climate_records=Counter()
    climate_sites=defaultdict(set)
    day_pairs=set()
    days2022=defaultdict(list)
    day_by_year=Counter()
    unique_microkeys=set()
    match_macro=Counter()
    for r in micro:
        pid=r["PlotID"]
        if pid not in ps:raise ValueError("unmatched_original_microclimate_plot")
        date=date_of(r["Date"])
        if date is None:raise ValueError("unparseable_original_micro_date")
        if (pid,date) in unique_microkeys:
            raise ValueError("duplicated_plot_day_temperature")
        unique_microkeys.add((pid,date))
        day_by_year[date.year]+=1
        tmacro,tlocal=[parse_float(r[key]) for key in ("Tmacro","Tmicro")]
        vwc=parse_float(r["VWC"])
        if tmacro is not None and tlocal is not None:
            climate_records["Tmacro_Tmicro_both"]+=1
            climate_sites[date.year].add(pid)
            if date.year==2022:
                days2022[pid].append((date,tmacro,tlocal,vwc))
        if vwc is not None:climate_records["VWC_present"]+=1
    groups=Counter()
    group_counts=Counter()
    arth_year=Counter()
    sample_keys=defaultdict(set)
    beetle_label_classes=defaultdict(set)
    missing_counts=Counter()
    source_count=0
    for r in arth:
        pid=r["PlotID"]
        if pid not in ps:raise ValueError("unmatched_original_beetle_plot")
        date=date_of(r["Date"])
        if date is None:raise ValueError("unparseable_original_arthropod_date")
        key=(r["SpeciesGroup"] or "").strip()
        groups[key]+=1
        arth_year[date.year]+=1
        c=parse_float(r["Count"])
        if c is not None:
            if c<0 or not c.is_integer():raise ValueError("invalid_original_arthropod_count")
            group_counts[key]+=int(c)
        else:missing_counts[key]+=1
        sample_keys[key].add((pid,r["TrapID"],date,r["Period"]))
        if r["Species"]:beetle_label_classes[key].add(r["Species"])
    if len(arth)<100 or len(micro)<100:
        raise ValueError("source_trial_not_a_real_field_dataset")
    common_2022_micro=set(days2022)
    all_arth_plot_ids={r["PlotID"] for r in arth if date_of(r["Date"]).year==2022}
    report={
        "schema":"structural.belgium_forest_microclimate_beetles_dryad_source_audit.v1",
        "source_dryad_DOI":DOI,
        "source_pub_year":2025,
        "source_journal_DOI":"10.1111/1365-2664.70137",
        "original_files_sha256":{
            name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in
            (("plot",plot_path),("micro",micro_path),("arth",arth_path))},
        "original_plot_characteristics_rows":len(plots),
        "original_unique_plot_IDs_not_independent_forests":len(ps),
        "original_plots_by_dominant_tree_species":dict(tree),
        "original_canopy_cover_nonmissing_n":len(canopy),
        "original_canopy_cover_min":min(canopy),
        "original_canopy_cover_max":max(canopy),
        "original_canopy_cover_median":statistics.median(canopy),
        "original_plot_field_nonmissing":dict(plotfields),
        "original_microclimate_rows":len(micro),
        "source_plotday_Tmicro_Tmacro_both":climate_records["Tmacro_Tmicro_both"],
        "source_plotday_VWC":climate_records["VWC_present"],
        "source_microclimate_year_rows":dict(day_by_year),
        "source_microclimate_2022_plot_n":len(common_2022_micro),
        "original_arthropod_rows":len(arth),
        "original_arthropod_year_rows":dict(arth_year),
        "original_taxon_group_row_counts":dict(groups),
        "original_taxon_group_counted_individuals":dict(group_counts),
        "original_taxon_group_missing_count_rows":dict(missing_counts),
        "original_taxon_group_unique_species_labels_not_species_richness":{
            k:len(v) for k,v in beetle_label_classes.items()},
        "original_trap_date_period_keys_by_taxon_group":{
            k:len(v) for k,v in sample_keys.items()},
        "site_overlap_2022_microclimate_vs_arthropod_2022_n":
            len(common_2022_micro & all_arth_plot_ids),
        "all_36_field_plots_from_one_forest":True,
        "original_paper_has_already_published_canopy_buffering_and_beetle_response":True,
        "independent_new_macro_forest_regions_added_to_test":1,
        "new_thermal_effect_or_vertical_escape_scored":False,
        "original_raw_plot_IDs_species_names_or_coordinates_exported":False,
        "eBird_used":False,
    }
    return report


def run(plot,micro,arth,out):
    r=audit(plot,micro,arth)
    path=Path(out);path.mkdir(parents=True,exist_ok=True)
    (path/"belgium_original_climate_beetle_source_quality.json").write_text(
        json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,ensure_ascii=False))
    return r


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--plot",required=True)
    p.add_argument("--micro",required=True)
    p.add_argument("--arth",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.plot,a.micro,a.arth,a.out)
