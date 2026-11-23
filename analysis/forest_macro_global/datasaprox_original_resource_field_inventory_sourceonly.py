#!/usr/bin/env python3
"""DATASAPROX v1.6 source original METHOD-FIELD NAME audit for wood resources.

Never inspect organism/taxon/abundance/core species cells or original
dynamicProperties values as biological measurements. Original publisher
response stays sealed; only exact source event metadata and field names used.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from collections import Counter,defaultdict
from pathlib import Path

import datasaprox_source_metadata_gate as source

SHA="4163a2f8f72d756e74f64319b8e199b284ecc6414196147e4465d342d7dcb6d0"
N_SOURCE_ROWS=675525
N_SOURCE_EVENTS=65642
N_METHOD_CONFLICTS=1133
N_METHOD_CONSISTENT=64509

META_WHITELIST={"eventID","ownerInstitutionCode","datasetName","year","month",
                "eventDate","dynamicProperties","sampleSizeValue","sampleSizeUnit"}

NEVER_RESOURCE_KEYS={
    "id_plot","id_subplot","id_condition","trap_model","trap_type",
    "trap_stratum","trap_bait","trap_colour","samplingprotocol",
    "eventid","sampleid","trap_id","id_trap","stratum","year",
    "yearmonth","date","eventdate","substrate_trap", "method",
}
CATEGORIES={
   "direct_wood_host_identity":re.compile(
       r"(^|[_ ./-])(host(_species|_tree|_wood)?|tree(_species|_taxon|_genus|_id|_type)?|wood(_species|_tree|_type)?|"
       r"substrate(_species|_tree|_wood)?|substrat(e|_arbre|_bois|_essence)?|"
       r"essence(_arbre|_bois)?|arbre|baumart|holzart|h[oô]te|h[ôo]te)([_ ./-]|$)",re.I),
   "wood_decay_or_age":re.compile(
       r"decay|d[eé]compos|decompos|degradation_du_bois|"
       r"pourri|verrott|wood_age|deadwood_age|"
       r"rot_stage|wood_rot|deadwood_stage|stade.*bois",re.I),
   "wood_bark":re.compile(r"bark|[eé]corce|ecorce|rinde|borke",re.I),
   "wood_amount_or_dimension":re.compile(
       r"deadwood|dead_wood|wood_volume|volume.*(wood|bois)|"
       r"volume_bois|diam[eè]t|diamet|durchmesser|"
       r"log_length|wood_length|longueur.*bois|"
       r"wood_amount|wood_density|d[eé]bris|stump|souche|chablis|"
       r"bois_mort|holzmenge",re.I),
   "microhabitat":re.compile(
       r"microhabitat|micro_habitat|trems|tree.related.microhabitat|"
       r"wood_cavity|wood_hole|trou.*arbre|champignon|"
       r"fungus|myc[oé]|fungal",re.I),
   "forest_structure_context":re.compile(
       r"forest|for[eê]t|for[eê]st|canopy|canop[eé]|stand|"
       r"peuplement|climatic|lumi[eè]re|temperature|"
       r"temp[eé]rature|stamm|management|sylviculture",re.I),
}

SAFE_LABEL=re.compile(r"^[A-Za-zÀ-ÿ0-9_ .()+/\-]{2,70}$")
TEXT_KEY=re.compile(r"(?u)(?:^|[;,{|])\s*['\"]?([^\s;,{|:'\"=][^;,{|:'\"=]{0,67})['\"]?\s*[:=]")


def canon(s):
    x=unicodedata.normalize("NFKC",str(s or "")).casefold().strip()
    return re.sub(r"\s+","_",x)


def method_field_names(raw):
    if not raw:
        return frozenset(),False
    try:
        obj=json.loads(raw)
        if isinstance(obj,dict):
            return frozenset(canon(x) for x in obj.keys() if x),True
    except (ValueError,TypeError):
        pass
    return frozenset(canon(x) for x in TEXT_KEY.findall(raw) if x),False


def roles(keys):
    eligible={x for x in keys if x not in NEVER_RESOURCE_KEYS}
    found={}
    for name,rx in CATEGORIES.items():
        found[name]={k for k in eligible if rx.search(k)}
    return found


def source_audit(archive):
    p=Path(archive)
    if not p.is_file() or p.stat().st_size>source.MAX_COMPRESSED:
        raise ValueError("SOURCE_ARCHIVE_OR_COMPRESSED_SIZE_STOP")
    if hashlib.sha256(p.read_bytes()).hexdigest()!=SHA:
        raise ValueError("SOURCE_ORIGINAL_V1_6_SHA256_STOP")
    with zipfile.ZipFile(p) as z:
        if sum(i.file_size for i in z.infolist())>source.MAX_UNCOMPRESSED:
            raise ValueError("SOURCE_ORIGINAL_UNCOMPRESSED_CAP_STOP")
        spec=source.schema(z)
        index=spec["fields"]
        required=META_WHITELIST
        if not required.issubset(index):
            raise ValueError("SOURCE_REQUIRED_METHOD_AND_EVENT_FIELDS_MISSING_STOP")
        native={
            k:v for k,v in sorted(index.items())
            if any(needle in k.casefold() for needle in (
                "habitat","substrate","wood","tree","forest","canopy","samp",
                "event","latitude","longitude","uncertainty","occurrencestatus"))
        }
        events={}
        conflicts=set()
        rows=0
        nonjson_rows=0
        with z.open(spec["file"]) as fh:
            inp=io.TextIOWrapper(fh,encoding="utf-8-sig",errors="strict",newline="")
            reader=csv.reader(inp,delimiter=spec["delimiter"],
                              quotechar=spec["quote"] or '"',
                              quoting=csv.QUOTE_MINIMAL if spec["quote"] else csv.QUOTE_NONE)
            for _ in range(spec["header"]):next(reader)
            for row in reader:
                if not row:continue
                rows+=1
                if rows>source.MAX_ROWS:
                    raise ValueError("SOURCE_ORIGINAL_ROWS_CAP_STOP")
                def value(k):
                    j=index.get(k)
                    return row[j].strip() if j is not None and j<len(row) else ""
                producer,project,eid=(value(k) for k in
                     ("ownerInstitutionCode","datasetName","eventID"))
                if not project or not eid:continue
                key=(producer,project,eid)
                props=value("dynamicProperties")
                pvals=source.properties(props)
                yr,mon=value("year"),value("month")
                dt=value("eventDate")
                if (not yr or not mon) and re.match(r"^\d{4}-\d{2}",dt):
                    yr,mon=yr or dt[:4],mon or dt[5:7]
                ym=f"{yr}-{mon.zfill(2)}" if yr and mon else ""
                method=(source.layer(pvals.get("trap_stratum","")),
                    pvals.get("id_plot",""),pvals.get("trap_model",""),
                    pvals.get("trap_type",""),pvals.get("id_condition",""),
                    pvals.get("trap_bait",""),pvals.get("trap_colour",""),
                    ym,source.duration(value("sampleSizeValue"),value("sampleSizeUnit")))
                names,isjson=method_field_names(props)
                if props and not isjson:nonjson_rows+=1
                if key not in events:
                    events[key]=[method,set(names)]
                else:
                    if events[key][0]!=method:
                        conflicts.add(key)
                    else:
                        events[key][1].update(names)
    if rows!=N_SOURCE_ROWS or len(events)!=N_SOURCE_EVENTS or len(conflicts)!=N_METHOD_CONFLICTS:
        raise ValueError("SOURCE_EVENT_BASELINE_DENOMINATOR_DRIFT_STOP")
    eligible={k:val for k,val in events.items() if k not in conflicts}
    if len(eligible)!=N_METHOD_CONSISTENT:
        raise ValueError("SOURCE_METHOD_CONSISTENT_DENOMINATOR_DRIFT")
    total_fields=Counter()
    category_events=Counter()
    candidate_projects=defaultdict(lambda:Counter())
    co=Counter()
    field_spelling=defaultdict(lambda:Counter())
    for (producer,project,eid),(method,names) in eligible.items():
        total_fields.update(names)
        found=roles(names)
        for category,ids in found.items():
            if ids:
                category_events[category]+=1
                candidate_projects[(producer,project)][category]+=1
                for label in ids:
                    field_spelling[category][label]+=1
        if found["direct_wood_host_identity"] and found["wood_decay_or_age"]:
            co["host_decay_same_source_event"]+=1
            candidate_projects[(producer,project)]["host_decay_same_source_event"]+=1
        if found["direct_wood_host_identity"] and (
            found["wood_amount_or_dimension"] or found["wood_decay_or_age"]):
            co["host_and_wood_amount_or_decay_same_event"]+=1
    all_projects={(x[0],x[1]) for x in eligible}
    count_by_category={
      category:sum(table[category]>0 for table in candidate_projects.values())
      for category in CATEGORIES
    }
    count_by_category["host_decay_same_source_event"] = sum(
      table["host_decay_same_source_event"]>0 for table in candidate_projects.values())
    host_decay_project_histogram=sorted(
      t["host_decay_same_source_event"] for t in candidate_projects.values()
      if t["host_decay_same_source_event"]>0)
    qualified_projects=sum(n>=10 for n in host_decay_project_histogram)
    names_by_category={
      category:[{"published_metadata_key_name_only":key,
                 "original_consistent_event_keys":val}
                for key,val in sorted(ids.items(),key=lambda x:(-x[1],x[0]))
                if SAFE_LABEL.match(key)][:40]
      for category,ids in field_spelling.items()
    }
    return {
      "source_publisher_v1_6_SHA256":SHA,
      "original_occurrence_core_rows_method_only":rows,
      "source_unique_original_events":len(events),
      "source_method_conflicting_event_keys_removed":len(conflicts),
      "source_method_consistent_event_keys":len(eligible),
      "non_JSON_dynamicProperties_occurrence_ROWS_diagnostic":nonjson_rows,
      "all_original_distinct_dynamicProperties_FIELDNAME_keys":len(total_fields),
      "original_producer_project_keys_method_consistent":len(all_projects),
      "original_core_metadata_field_presence_subset":sorted(native),
      "source_event_keys_with_resource_lexical_field_roles":dict(sorted(category_events.items())),
      "source_distinct_project_counts_by_resource_lexical_role":dict(sorted(count_by_category.items())),
      "source_event_cooccurrence_counts":dict(sorted(co.items())),
      "source_project_host_and_decay_candidate_event_counts_sorted_nonidentifying":
          host_decay_project_histogram[:80],
      "source_projects_ge_10_host_and_decay_named_source_events":qualified_projects,
      "source_lexical_field_NAMES_ONLY_by_category":names_by_category,
      "proposed_ge_2_projects_with_ge10_source_events_prefilter":
          qualified_projects>=2,
      "original_actual_deadwood_amount_host_and_decay_measured_confirmed":False,
      "original_site_tree_beetle_species_join_admitted":False,
      "original_species_or_beetle_abundance_values_read":0,
      "new_ecological_effects_scored":0,
      "status":(
          "SOURCE_LEXICAL_RESOURCE_CANDIDATE_GE2_PROJECTS_CODEBOOK_HOLD"
          if qualified_projects>=2 else
          "SOURCE_ORIGINAL_RESOURCE_HOST_AND_DECAY_COLUMN_SUPPORT_NOT_VERIFIED_HOLD")
    }


def test():
    names,ok=method_field_names('{"ID_plot":"fake","tree_species":"Fagus","decay_stage":"3","trap_model":"x"}')
    assert ok
    assert "id_plot" in names and "decay_stage" in names and "tree_species" in names
    a=roles(names)
    assert "tree_species" in a["direct_wood_host_identity"]
    assert "decay_stage" in a["wood_decay_or_age"]
    assert not a["direct_wood_host_identity"].intersection({"id_plot","trap_model"})
    assert not roles({"id_condition","trap_stratum","id_subplot"})["direct_wood_host_identity"]
    b,j=method_field_names("ID_plot: 23; ID_condition: blue; wood_volume: 0.04")
    assert "wood_volume" in b
    print("DATASAPROX_ORIGINAL_RESOURCE_FIELD_NAMES_ONLY_FIXTURE_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--archive")
    p.add_argument("--out",default="datasaprox_resource_fieldnames_only/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    if not a.archive:
        p.error("--archive required: original DATASAPROX v1.6 author ZIP")
    result={
      "schema":"structural.datasaprox_v16_original_resource_field_names_only.v1",
      "original_dataset_UUID":source.UUID,
      "source_original_publisher_SHA256_expected":SHA,
      "source_species_taxon_organism_numeric_values_read":0,
      "previous_datasets_scientific_stops_unchanged":True,
      "original_source_archived_in_git":False,
      "eBird_used":False,
      "TinyFish_used":False,
      "status":"SOURCE_ORIGINAL_RESOURCE_FIELD_VOCAB_NOT_STARTED"}
    try:
        result["source_only_field_inventory"]=source_audit(a.archive)
        result["status"]=result["source_only_field_inventory"]["status"]
    except Exception as e:
        result["status"]="SOURCE_ORIGINAL_RESOURCE_FIELD_SCHEMA_OR_METHOD_STOP"
        result["error_type"]=type(e).__name__
        result["source_code_only_error"]=str(e)[:170] if isinstance(e,ValueError) else ""
    out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("RESOURCE_FIELD_SOURCE_STATUS",result["status"])
    if "source_only_field_inventory" in result:
        s=result["source_only_field_inventory"]
        print("HOST_KEY_EVENTS",s["source_event_keys_with_resource_lexical_field_roles"].get(
            "direct_wood_host_identity",0))
        print("HOST_DECAY_PROJECTS_AT_LEAST_10_EVENTS",
            s["source_projects_ge_10_host_and_decay_named_source_events"])
    print("SOURCE_BEETLE_SPECIES_OR_ABUNDANCE_VALUES_READ",result["source_species_taxon_organism_numeric_values_read"])

if __name__=="__main__":
    main()
