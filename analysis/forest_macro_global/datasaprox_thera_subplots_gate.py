#!/usr/bin/env python3
"""THERA (EFNO) response-unopened plot/subplot and paired-trap support audit.

Metadata only on fixed original DATASAPROX v1.6 archive, after the
canonical 1,133 conflicting event-key exclusions. Even a pass is
NOT a taxon response, causal height treatment, or independent forest proof.
"""
from __future__ import annotations
import argparse,csv,io,json,math,zipfile
from collections import defaultdict,Counter
from pathlib import Path
from datasaprox_project_method_table7_gate import source_sample_events
from datasaprox_source_metadata_gate import schema,properties

TARGET=("EFNO","THERA")
ALLOWED_UPPER={"Lind noir Canopee superieure","Lind noir Supra canopee"}
ALLOWED_LOWER={"Lind noir Canopee inferieure","Lind noir Infra canopee"}

def audit_subplots(events,bad,extra):
    target={
        k:v for k,v in events.items()
        if k[:2]==TARGET and k not in bad
    }
    source_conflicting_additional=set()
    for k,v in extra.items():
        if len(v)>1:source_conflicting_additional.add(k)
    groups=defaultdict(lambda:{"upper":[],"lower":[]})
    code_errors=0
    for (producer,project,event),descriptor in target.items():
        if (producer,project,event) in source_conflicting_additional:continue
        stratum,plot,model,typ,condition,bait,colour,ym,days=descriptor
        if stratum not in ("upper","lower") or not(plot and model and ym and days is not None):
            continue
        if (stratum=="upper" and condition not in ALLOWED_UPPER) or (
            stratum=="lower" and condition not in ALLOWED_LOWER):
            code_errors+=1
        # Condition is intentionally NOT part of matching. Its publisher
        # field encodes both Lindgren black trap and canopy layer.
        g=(plot,ym,model,typ,bait,colour)
        ent={
            "duration":days,
            "subplots":next(iter(extra.get((producer,project,event),{("", "", "")})))[:1],
            "trapname":next(iter(extra.get((producer,project,event),{("", "", "")})))[2],
        }
        groups[g][stratum].append(ent)
    eligible=[]
    for key,q in groups.items():
        if any(7<=u["duration"]<=35 and 7<=l["duration"]<=35
                and abs(u["duration"]-l["duration"])<=7
                for u in q["upper"] for l in q["lower"]):
            eligible.append((key,q))
    if len(eligible)!=62 or len({k[0] for k,v in eligible})!=20:
        return {"status":"STOP_THERA_PROJECT_PAIR_DESIGN_DRIFT",
                "eligible_plot_month_units_observed":len(eligible),
                "original_species_values_read":False}
    extra_labels=Counter()
    for _,q in eligible:
        upper={z for item in q["upper"] for z in item["subplots"] if z}
        lower={z for item in q["lower"] for z in item["subplots"] if z}
        if upper and lower and upper & lower:
            extra_labels["upper_lower_share_nonempty_author_subplots"]+=1
        elif upper and lower:
            extra_labels["both_subplots_nonempty_but_disjoint"]+=1
        elif not upper and not lower:
            extra_labels["both_subplots_missing"]+=1
        else:
            extra_labels["one_layer_subplots_missing"]+=1
    return {
        "status":"THERA_SOURCE_METHOD_METADATA_EVALUATED_AUTHOR_PROTOCOL_NOT_CONFIRMED",
        "source_project_publication_verified_name":"EFNO THERA",
        "source_original_source_event_keys_retained_after_strict_qa":len(target),
        "source_THERA_additional_subsample_metadata_inconsistency_event_keys":len(source_conflicting_additional),
        "source_author_condition_labels_outside_exact_four_canopy_Lindgren_labels":code_errors,
        "original_plot_month_method_bait_colour_effort_matched_strata":len(eligible),
        "distinct_original_THERA_plot_keys":len({k[0] for k,v in eligible}),
        "source_subplots_comparability_of_62_paired_strata":dict(sorted(extra_labels.items())),
        "source_events_with_subplot_metadata":sum(bool(next(iter(v))[0]) for k,v in extra.items() if k in target and len(v)==1),
        "source_events_with_trapname_metadata":sum(bool(next(iter(v))[2]) for k,v in extra.items() if k in target and len(v)==1),
        "ID_condition_label_clarifies_trap_model_colour_and_stratum_but_not_independent_causal_height":True,
        "publisher_original_THERA_independent_field_hierarchy_confirmed":False,
        "source_Thera_taxon_scoring_authorized":False,
        "original_species_values_read":False,
        "no_original_event_plot_subplot_trap_taxon_or_coordinates_exported":True,
    }

def source_optional_field_metadata(archive,events,bad):
    # Only the original sampling metadata fields are semantically opened.
    extra=defaultdict(set)
    with zipfile.ZipFile(archive) as z:
        meta=schema(z);fm=meta["fields"]
        needed=("eventID","datasetName","ownerInstitutionCode","dynamicProperties")
        if any(k not in fm for k in needed):raise ValueError("STOP_AUTHOR_SAMPLE_SCHEMA_DRIFT")
        with z.open(meta["file"]) as f:
            raw=io.TextIOWrapper(f,encoding="utf-8-sig",newline="")
            rows=csv.reader(raw,delimiter=meta["delimiter"],
                quotechar=meta["quote"] or '"',
                quoting=csv.QUOTE_MINIMAL if meta["quote"] else csv.QUOTE_NONE)
            for _ in range(meta["header"]):next(rows)
            for row in rows:
                if not row:continue
                def fld(n):
                    i=fm[n]
                    return row[i].strip() if i<len(row) else ""
                if (fld("ownerInstitutionCode"),fld("datasetName"))!=TARGET:
                    continue
                k=(*TARGET,fld("eventID"))
                if k in bad or k not in events:continue
                d=properties(fld("dynamicProperties"))
                extra[k].add((d.get("id_subplot",""),d.get("trap_num",""),d.get("trap_name","")))
    return extra

def run(archive,out):
    events,bad,n=source_sample_events(archive)
    extra=source_optional_field_metadata(archive,events,bad)
    report=audit_subplots(events,bad,extra)
    report["source_original_occurrence_metadata_only_rows"]=n
    report["source_archive_release"]="DATASAPROX_v1.6"
    folder=Path(out);folder.mkdir(parents=True,exist_ok=True)
    (folder/"datasaprox_thera_source_subplot_gate.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--archive",required=True)
    a.add_argument("--out",required=True)
    args=a.parse_args()
    run(args.archive,args.out)
