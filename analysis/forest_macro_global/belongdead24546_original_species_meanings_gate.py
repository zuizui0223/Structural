#!/usr/bin/env python3
"""Source-only BExIS 24546 official dataStructure 1027 spec1/spec2 meanings.

No BExIS original data CSV, field plot ID, coordinates, original tree taxon
strings, insect specimen/catch values or traits accessed or written.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from belongdead24546_publisher_datastructure_attribute_gate import public_json,SourceStop

SOURCE_STRUCT="/api/structures/1027"
FIELDS=("spec1","spec2")
GENERIC_KEYS={
 "value","code","id","key","name","label","description","meaning","meanings",
 "concept","definition","shortname","displayname","identifier","text",
 "unit","systemtype","datatype","type","category","term"
}
CODE_ROLES={"code","value","key","identifier"}
DESC_ROLES={"description","label","name","meaning","definition","term","displayname"}

def objects_with_source_field(x,depth=0):
    if depth>30:return
    if isinstance(x,dict):
        for field in FIELDS:
            if any(isinstance(v,str) and v.strip()==field
                   for v in x.values()):
                yield field,x
        for v in x.values():
            yield from objects_with_source_field(v,depth+1)
    elif isinstance(x,list):
        for v in x[:10000]:
            yield from objects_with_source_field(v,depth+1)


def anonymized_meanings(x):
    if x is None:
        return {
            "source_meanings_kind":"null",
            "source_meaning_entries_count":0,
            "source_key_role_pairs_explicitly_declared_count":0,
            "original_source_taxon_codes_and_descriptions_NOT_EXPORTED":True,
        }
    if isinstance(x,list):
        elements=x
        kind="list"
    elif isinstance(x,dict):
        elements=list(x.values())
        kind="dict"
    else:
        return {
            "source_meanings_kind":type(x).__name__,
            "source_meaning_entries_count":0,
            "source_key_role_pairs_explicitly_declared_count":0,
            "original_source_taxon_codes_and_descriptions_NOT_EXPORTED":True,
        }
    property_count={}
    plausible=0
    types={}
    for item in elements:
        t=type(item).__name__
        types[t]=types.get(t,0)+1
        if isinstance(item,dict):
            keys={str(k).lower() for k in item if str(k).lower() in GENERIC_KEYS}
            for k in keys:
                property_count[k]=property_count.get(k,0)+1
            if keys&CODE_ROLES and keys&DESC_ROLES:
                plausible+=1
    return {
        "source_meanings_kind":kind,
        "source_meaning_entries_count":len(elements),
        "source_meaning_entry_structure_class_counts":types,
        "source_safe_generic_dictionary_property_key_counts":dict(sorted(property_count.items())),
        "source_entries_with_explicit_code_and_description_key_roles":plausible,
        "source_code_meaning_candidate_availability":plausible>0,
        "original_source_taxon_codes_and_descriptions_NOT_EXPORTED":True,
    }


def audit():
    source,digest,n=public_json(SOURCE_STRUCT)
    if not isinstance(source,(dict,list)):
        raise SourceStop("SOURCE_STOP_1027_PUBLISHER_STRUCTURE_NOT_OBJECT")
    records={}
    for field in FIELDS:
        direct=[obj for k,obj in objects_with_source_field(source) if k==field]
        if len(direct)!=1:
            raise SourceStop("SOURCE_STOP_PUBLISHER_SPECIES_ATTRIBUTE_IDENTITY_NOT_UNIQUE_"+field)
        attr=direct[0]
        has_meanings="meanings" in attr
        rec=anonymized_meanings(attr.get("meanings"))
        rec["author_published_exact_original_attribute_found"]=True
        rec["original_author_meanings_property_present"]=has_meanings
        records[field]=rec
    both=all(z.get("source_code_meaning_candidate_availability",False) for z in records.values())
    return {
      "schema":"structural.BELongDead24546_original_species_meanings_publisher_dictionary_sourceonly.v1",
      "source_original_dataset_ID":24546,
      "source_original_dataStructureId":1027,
      "source_publisher_structure_API":SOURCE_STRUCT,
      "original_publisher_structure_SHA256":digest,
      "original_publisher_structure_bytes":n,
      "source_exact_field_meanings_structure":records,
      "both_spec1_spec2_have_explicit_code_description_role_objects":both,
      "original_2012_deadwood_total_DWV_m3_30plots_validated_previously":True,
      "original_experimental_13host_vs_natural_13category_exact_text_overlap_ZERO_prior":True,
      "original_publisher_categories_still_not_mapped_to_experiment_tree_taxa":True,
      "no_original_observation_values_species_labels_coordinates_or_insect_data_read":True,
      "prior_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_results_frozen":True,
      "eBird_used":False,
      "status":"SOURCE_PUBLISHER_SPECIES_CODE_TO_DESCRIPTION_STRUCTURE_POSSIBLE_NEEDS_IDENTITY_VALIDATION"
         if both else "SOURCE_AUTHOR_SPECIES_CODE_MAPPING_NOT_PRESENT_OR_INCOMPLETE_IN_STRUCTURE",
    }


def synthetic():
    x={"label":"spec1","meanings":[{"code":"FA","description":"Fagus sylvatica"}]}
    got=anonymized_meanings(x["meanings"])
    assert got["source_meaning_entries_count"]==1
    assert got["source_entries_with_explicit_code_and_description_key_roles"]==1
    assert "Fagus" not in json.dumps(got)
    assert anonymized_meanings(None)["source_meaning_entries_count"]==0
    assert len(list(objects_with_source_field({"attributes":[x]})))==1
    print("SYNTHETIC_OFFICIAL_24546_ORIGINAL_SPECIES_CODEBOOK_MEANINGS_NO_TAXON_EXPORT_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out needed")
    try:r=audit()
    except SourceStop as e:
        r={
           "schema":"structural.BELongDead24546_original_species_meanings_publisher_dictionary_sourceonly.v1",
           "status":str(e),
           "source_STOP_not_ecological_null":True,
           "no_source_biological_scores_reopened":True,
        }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead24546_original_spec1_spec2_meanings_shape_only.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
