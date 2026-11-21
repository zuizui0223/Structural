#!/usr/bin/env python3
"""Source-only Piccini 2026 within-stratum method/effort/guild HEADER readiness.

The original 17-field text is read from publisher into runner-private RAM.
Only exact author method columns are selected from individual data records.
Species, guild labels, count, abundance and environmental row values are NEVER used.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
from statistics import median
from piccini2026_gro_original_method_unit_gate import (
    DOI, MAX_FILE, metadata_source_files, head_shape,
    get_one_original_publisher_file, MethodStop
)
from piccini2026_gro_original_header_only_gate import normalized, CATEGORIES

FIELDS_CORE = ("site", "stand", "plot", "stratum", "period")
METHOD_FIELDS = {
    "trap_id": {"trap", "trapid", "trapnumber", "trapcode"},
    "sample_id": {"sample", "sampleid", "samplingid", "samplecode", "collectionid"},
    "replicate": {"replicate", "replicateid"},
    "method": {"method", "samplingmethod", "traptype", "methodtype"},
    "effort": {"effort", "trapdays", "trapnights", "duration",
               "samplingdays", "samplingduration"},
}
MAX_ROWS = 100000
EXPECTED_SOURCE_ROWS = 22414
MAX_PER_LAYER_VALUES_TO_EXPORT = 0

def typed_generic_headers(header: list[str]) -> dict:
    n = [normalized(h) for h in header]
    # Only the 17-column width is global. Non-selected headers can share
    # normalized spellings without changing explicitly selected method roles.
    # Selected core uniqueness and trap-role ambiguity remain guarded below.
    if len(n) != 17:
        raise MethodStop("SOURCE_STOP_ORIGINAL_17COLUMN_HEADER_SHAPE")
    core = {key: [i for i,v in enumerate(n) if v == key] for key in FIELDS_CORE}
    methods = {role: [i for i,v in enumerate(n) if v in names]
               for role,names in METHOD_FIELDS.items()}
    # Only original HEADER NAMES, never biological row values.
    bio = {
        "taxon_header_present": any(z in CATEGORIES["taxon"] for z in n),
        "guild_header_present": any(z in CATEGORIES["guild_affiliation"] for z in n),
        "abundance_or_count_header_present": any(
            z in {"abundance","count","individuals"} for z in n),
        "guild_safe_header_names": sorted(
            z for z in n if z in CATEGORIES["guild_affiliation"]),
    }
    return {"normalized_names": n, "core": core, "methods": methods, "bio": bio}


def min_med_max(values):
    return {"min": int(min(values)), "median": float(median(values)),
            "max": int(max(values))} if values else None


def method_only_qualification(raw: bytes, source_checksum=None):
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),
                            delimiter=";",strict=True)
        header = next(reader)
    except (UnicodeError,StopIteration,csv.Error) as e:
        raise MethodStop("SOURCE_STOP_READER_HEADER_UNAVAILABLE") from e
    roles = typed_generic_headers(header)
    core = roles["core"]
    methods = roles["methods"]
    # Normalize header names only; safe generic names, no author raw codes.
    result = {
        "core_source_field_name_counts": {k:len(v) for k,v in core.items()},
        "method_generic_header_names_by_role": {
            k:[roles["normalized_names"][i] for i in v]
            for k,v in methods.items()},
        "method_header_count_by_role": {k:len(v) for k,v in methods.items()},
        "biology_HEADER_only": roles["bio"],
        "original_biological_row_fields_NEVER_SELECTED": True,
        "no_raw_author_site_trap_period_labels_reexported": True,
        "no_source_species_guild_abundance_or_habitat_values_used": True,
    }
    if any(len(v)!=1 for v in core.values()):
        result["status"]="AUTHOR_NAMED_CORE_METHOD_GRAIN_UNRESOLVED"
        return result
    # No inferred source method-role matching by observed cardinality.
    selected = {i for v in core.values() for i in v}
    selected.update(i for positions in methods.values() for i in positions)
    if len(selected)>12:
        raise MethodStop("SOURCE_STOP_WHITELIST_TOO_BROAD")
    ids = {k:v[0] for k,v in core.items()}
    field_unique = {i:set() for i in selected}
    field_missing = {i:0 for i in selected}
    plot_parents = defaultdict(set)
    plot_stands = defaultdict(set)
    site_stands = defaultdict(set)
    plot_layers = defaultdict(set)
    site_stand_layers = set()
    plot_layer_periods = set()
    plot_layer_pairs = set()
    layer_periods = defaultdict(set)
    layer_row_counts = defaultdict(int)
    layer_plot_period_contexts = defaultdict(set)
    role_keys = defaultdict(lambda:defaultdict(set))
    original_rows = 0
    try:
        for row in reader:
            original_rows += 1
            if original_rows > MAX_ROWS or len(row)!=17:
                raise MethodStop("SOURCE_STOP_SOURCE_ROW_COUNT_OR_WIDTH")
            # biological fields NEVER accessed here
            cells = {i:row[i].strip() for i in selected}
            for i,v in cells.items():
                if v:field_unique[i].add(v)
                else:field_missing[i]+=1
            vals = {k:cells[v] for k,v in ids.items()}
            if any(not vals[k] for k in FIELDS_CORE):
                continue
            site,stand,plot,layer,period=(vals[k] for k in FIELDS_CORE)
            plot_parents[plot].add(site)
            plot_stands[plot].add(stand)
            site_stands[site].add(stand)
            plot_layers[plot].add(layer)
            site_stand_layers.add((site,stand,layer))
            plot_layer_periods.add((plot,layer,period))
            plot_layer_pairs.add((plot,layer))
            layer_periods[layer].add(period)
            layer_plot_period_contexts[layer].add((plot,period))
            layer_row_counts[layer]+=1
            for role,positions in methods.items():
                for i in positions:
                    v=cells[i]
                    if v:
                        role_keys[(role,i)][(plot,layer)].add(v)
    except csv.Error as e:
        raise MethodStop("SOURCE_STOP_CSV_PARSE_DRIFT") from e
    if original_rows!=EXPECTED_SOURCE_ROWS:
        result.update({"status":"SOURCE_STOP_SOURCE_ROW_NUMBER_DRIFT",
                       "source_rows_scanned":original_rows})
        return result
    checksum_state="NOT_ADVERTISED"
    if isinstance(source_checksum,dict) and str(source_checksum.get("type","")).lower()=="md5":
        if hashlib.md5(raw).hexdigest()!=str(source_checksum.get("value","")).lower():
            raise MethodStop("SOURCE_STOP_PUBLISHER_CHECKSUM_MISMATCH")
        checksum_state="PUBLISHER_MD5_MATCH"
    nplot=len(plot_parents)
    parents={next(iter(v)) for v in plot_parents.values() if len(v)==1}
    stands={s for v in site_stands.values() for s in v}
    layers={l for v in plot_layers.values() for l in v}
    result.update({
        "source_rows_scanned":original_rows,
        "publisher_checksum_status":checksum_state,
        "source_parent_sites":len(parents),
        "source_stand_categories":len(stands),
        "source_plot_labels":nplot,
        "source_vertical_categories":len(layers),
        "source_site_stand_layer_cells":len(site_stand_layers),
        "source_plot_stratum_pairs":len(plot_layer_pairs),
        "source_plot_stratum_period_tokens":len(plot_layer_periods),
        "parent_sites_with_five_stands":sum(len(x)==5 for x in site_stands.values()),
        "plots_with_three_strata":sum(len(x)==3 for x in plot_layers.values()),
        "plot_parent_collisions":sum(len(x)!=1 for x in plot_parents.values()),
        "plot_stand_collisions":sum(len(x)!=1 for x in plot_stands.values()),
        "source_row_count_by_anonymous_stratum_SORTED_NOT_EFFORT":
             sorted(layer_row_counts.values()),
        "source_plot_period_context_counts_by_anonymous_stratum_SORTED":
             sorted(len(v) for v in layer_plot_period_contexts.values()),
        "source_period_category_counts_by_anonymous_stratum_SORTED":
             sorted(len(v) for v in layer_periods.values()),
        "method_generic_field_missing_count_by_role": {
           role: sorted(field_missing[i] for i in positions)
           for role,positions in methods.items()},
        "method_generic_field_distinct_label_count_by_role": {
           role: sorted(len(field_unique[i]) for i in positions)
           for role,positions in methods.items()},
        "method_per_plot_stratum_unique_label_count_ranges": {
           role:[
             {
               "safe_header_name": roles["normalized_names"][i],
               "number_plot_stratum_with_recorded_field":len(role_keys[(role,i)]),
               "number_raw_labels_reused_across_plot_strata":sum(
                 len({(p,l) for (p,l),v in role_keys[(role,i)].items()
                      if token in v})>1 for token in field_unique[i]),
               "per_plot_stratum_unique_label_count":min_med_max(
                  [len(z) for z in role_keys[(role,i)].values()])
             }
             for i in positions
           ] for role,positions in methods.items()
        },
        "no_zero_capture_trap_frame_inferred_from_positive_records":True,
        "no_complete_trap_day_effort_assumed_from_taxon_rows":True,
        "no_calendar_year_inferred_from_period_tokens":True,
        "no_cross_stratum_height_effect_estimated":True,
    })
    if (len(parents)!=8 or len(stands)!=5 or nplot!=40 or len(layers)!=3 or
        len(site_stand_layers)!=120 or len(plot_layer_pairs)!=120 or
        result["plot_parent_collisions"]!=0 or result["plot_stand_collisions"]!=0 or
        result["plots_with_three_strata"]!=40 or
        result["parent_sites_with_five_stands"]!=8):
        result["status"]="SOURCE_AUTHOR_8SITE_5STAND_40PLOT_METHOD_HIERARCHY_STOP"
    elif len(methods["trap_id"])!=1:
        result["status"]="SOURCE_TRAP_ID_ROLE_UNRESOLVED_OR_MULTIPLE"
    elif len(methods["method"])!=1 or len(methods["effort"])!=1:
        result["status"]="SOURCE_METHOD_OR_EFFORT_DENOMINATOR_NOT_DEFINED"
    elif not (roles["bio"]["taxon_header_present"] and
              roles["bio"]["guild_header_present"] and
              roles["bio"]["abundance_or_count_header_present"]):
        result["status"]="SOURCE_TAXON_GUILD_OR_ABUNDANCE_HEADER_NOT_IDENTIFIED"
    else:
        # Even with these headers, original complete zero-capture opportunity,
        # trap-days, storm plot relocation and codebook remain unverified.
        result["status"]="SOURCE_METHOD_HEADERS_PRESENT_BUT_FIELD_EFFORT_UNVERIFIED"
    return result

def original_method_source():
    output={"source_original_DOI":DOI,"status":"UNSTARTED",
       "source_2024_canopy_archive_NOT_READ":True,
       "species_guild_abundance_values_NEVER_ACCESSED":True}
    try:
        files=metadata_source_files()
        shapes=[head_shape(f["file_id"]) for f in files]
        candidate=[files[i] for i,h in enumerate(shapes)
           if h["header_column_count"]==17 and h["header_delimiter_category"]=="semicolon"]
        if len(candidate)!=1:
            raise MethodStop("SOURCE_STOP_17COLUMN_FILE_UNIDENTIFIABLE")
        file=candidate[0]
        raw=get_one_original_publisher_file(file["file_id"],file["expected_size"])
        output["result"]=method_only_qualification(raw,file.get("published_checksum"))
        output["status"]=output["result"]["status"]
    except MethodStop as e:
        output["status"]=str(e)
        output["source_STOP_not_ecological_null"]=True
    return output

def synthetic_known_truth():
    header=list(FIELDS_CORE)+[
        "trapID","sampleID","samplingMethod","Species","FeedingGuild","Abundance",
        "extra1","extra2","extra3","extra4","extra5","extra6"]
    assert len(header)==17
    rows=[]
    for si in range(8):
        for st in range(5):
            plot="P"+str(si)+"_"+str(st)
            for layer in ("floor","understorey","canopy"):
                for period in ("alpha","beta"):
                    for tr in range(3):
                        rows.append(["S"+str(si),"T"+str(st),plot,layer,period,
                            plot+"_"+layer+"_"+str(tr),
                            plot+"_"+layer+"_"+period+"_"+str(tr),
                            "method", "PROTECTED_SPECIES","PROTECTED_TRAIT",
                            "999"]+["0"]*6)
    s="\n".join(";".join(r) for r in [header]+rows)+"\n"
    o=method_only_qualification(s.encode())
    assert o["source_rows_scanned"]==720 if False else o["status"]=="SOURCE_STOP_SOURCE_ROW_NUMBER_DRIFT"
    assert "PROTECTED_SPECIES" not in json.dumps(o)
    assert "PROTECTED_TRAIT" not in json.dumps(o)
    # Make exactly 22414 synthetic method-only rows to cover frozen source size.
    n=EXPECTED_SOURCE_ROWS-len(rows)
    assert n>0
    p="\n".join(";".join(r) for r in ([header]+rows+[rows[0]]*n))+"\n"
    v=method_only_qualification(p.encode())
    assert v["source_parent_sites"]==8 and v["source_plot_labels"]==40
    assert v["source_site_stand_layer_cells"]==120 and v["source_plot_stratum_pairs"]==120
    assert v["source_plot_stratum_period_tokens"]==240
    assert v["method_header_count_by_role"]["trap_id"]==1
    assert v["method_header_count_by_role"]["effort"]==0
    assert v["status"]=="SOURCE_METHOD_OR_EFFORT_DENOMINATOR_NOT_DEFINED"
    assert "PROTECTED_SPECIES" not in json.dumps(v)
    assert "PROTECTED_TRAIT" not in json.dumps(v)
    assert "999" not in json.dumps(v)
    duplicate_nonselected=header.copy()
    duplicate_nonselected[-1]=duplicate_nonselected[-2]
    p2="\n".join(";".join(r) for r in ([duplicate_nonselected]+rows+[rows[0]]*n))+"\n"
    v2=method_only_qualification(p2.encode())
    assert v2["status"]=="SOURCE_METHOD_OR_EFFORT_DENOMINATOR_NOT_DEFINED"
    assert v2["source_parent_sites"]==8 and v2["source_plot_labels"]==40
    duplicate_core=header.copy()
    duplicate_core[1]="Site"
    p3="\n".join(";".join(r) for r in ([duplicate_core]+rows+[rows[0]]*n))+"\n"
    w=method_only_qualification(p3.encode())
    assert w["status"]=="AUTHOR_NAMED_CORE_METHOD_GRAIN_UNRESOLVED"
    duplicate_trap=header.copy()
    duplicate_trap[-1]="TrapID"
    p4="\n".join(";".join(r) for r in ([duplicate_trap]+rows+[rows[0]]*n))+"\n"
    z=method_only_qualification(p4.encode())
    assert z["status"]=="SOURCE_TRAP_ID_ROLE_UNRESOLVED_OR_MULTIPLE"
    print("SYNTHETIC_PICCINI_TRAP_METHOD_GUILD_HEADER_AND_SOURCE_GRAIN_FIREWALL_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    synthetic_known_truth()
    if args.test:return
    if not args.out:
        ap.error("--out required")
    obj={
       "schema":"structural.Piccini2026_within_stratum_method_guild_readiness_sourceonly.v1",
       "prespec":"docs/FOREST_BEETLE_PICCINI2026_WITHIN_STRATUM_METHOD_GUILD_READINESS_PRESPEC_20261117.md",
       "original_source":original_method_source(),
       "no_new_beetle_species_guild_abundance_beta_predictive_effect":True,
       "prior_Thai_Finland_PREDICTS_NEON_BALA_mammals_GEB_frozen":True,
       "eBird_used":False,
       "TinyFish_used":False,
    }
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Piccini2026_within_stratum_method_guild_readiness_sourceonly.json").write_text(
       json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(obj,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
