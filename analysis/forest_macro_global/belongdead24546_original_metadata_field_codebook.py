#!/usr/bin/env python3
"""Publisher original CC BY4 BExIS24546 v1 metadata attribute/units SOURCE ONLY.

No original specimen/insect rows, wood volumes/tree identity rows or plot
coordinates downloaded. The BExIS metadata may not include a usable
variable-to-unit data structure. In that case record NOT VERIFIED and STOP.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from collections import Counter,defaultdict
from pathlib import Path

URI="https://www.bexis.uni-jena.de/api/metadata/24546?tag=1.0"
TARGET=("spec1","spec2","DWV","Vharv","PT","Tdir","PTNum","dc")
SYNONYMS={
  "tree_taxon":re.compile(r"(?i)\b(?:species|tree.?species|baumart|tree.?taxon|baumspezies|holzart)\b"),
  "deadwood_volume":re.compile(r"(?i)\b(?:deadwood.{0,12}volume|volume.{0,12}deadwood|totholzvolumen|deadwood amount|holzvolumen)\b"),
  "harvest_volume":re.compile(r"(?i)\b(?:harvest|logging|ernte|holznutzung|entnahme)\b"),
  "cubic_metre":re.compile(r"(?i)(?:m\^?3|m³|cubic meter|cubic metre|kubikmeter|m3/ha)"),
  "diameter":re.compile(r"(?i)\b(?:diameter|dbh|bhd|durchmesser)\b"),
}
UNIT_KEYS=("unit","unitname","unitid","dimension","measurementunit","measurementunitname","quantitykind")
class SourceStop(Exception):pass


def get_publisher_original_metadata():
    request=urllib.request.Request(URI,headers={
        "User-Agent":"Structural-original-published-BExIS24546-method-codebook/1.0",
        "Accept":"application/json"})
    try:
        with urllib.request.urlopen(request,timeout=40) as response:
            b=response.read(600001)
            status=response.status
            ctype=response.headers.get("Content-Type","")
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_ACCESS_STOP_PUBLISHER_24546_METHOD_HTTP_"+str(ex.code)) from ex
    except (urllib.error.URLError,TimeoutError,OSError) as ex:
        raise SourceStop("SOURCE_TRANSPORT_STOP_PUBLISHER_METHOD_"+type(ex).__name__) from ex
    if status!=200 or len(b)>600000 or "json" not in ctype.lower():
        raise SourceStop("SOURCE_STOP_ORIGINAL_METADATA_NOT_PUBLIC_JSON_BELOW_600K")
    try:data=json.loads(b.decode("utf-8"))
    except ValueError as ex:
        raise SourceStop("SOURCE_STOP_PUBLISHER_ORIGINAL_METADATA_NOT_JSON") from ex
    return data,hashlib.sha256(b).hexdigest(),len(b)


def walk_exact_field_context(node,depth=0):
    if depth>26:return
    if isinstance(node,dict):
        children=[(str(k),v) for k,v in node.items()]
        words=[str(v) for k,v in children if isinstance(v,str) and len(v)<=3000]
        keywords=[k for k,v in children if len(k)<150]
        text=" ".join(words)
        for field in TARGET:
            # Evidence is literal source code mentioned within a metadata object;
            # co-occurrence only is weak, not authoritative field meaning.
            exact=re.compile(r"(?<![A-Za-z0-9_])"+re.escape(field)+r"(?![A-Za-z0-9_])",re.I)
            direct_values=sum(bool(exact.fullmatch(v.strip())) for v in words)
            contextual_hits=sum(bool(exact.search(v)) for v in words)
            if direct_values or contextual_hits:
                sem={k:bool(p.search(text)) for k,p in SYNONYMS.items()}
                unit_roles=[k for k in keywords if re.search("unit|dimension",k,re.I)]
                # Do not export original source metadata string values.
                yield {"field":field,
                       "metadata_field_code_exact_value_occurrences_in_node":direct_values,
                       "metadata_code_text_occurrences_in_node":contextual_hits,
                       "semantic_description_keywords_in_same_node":sem,
                       "publisher_metadata_unit_property_names_only":unit_roles[:6],
                       "nonempty_unit_property_in_same_node":any(
                         bool(str(v).strip()) for k,v in children if k.lower() in UNIT_KEYS
                       ),
                       "publisher_codebook_node_keys_only":[k for k in keywords
                            if re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]{0,45}",k)][:30],
                       }
        for value in node.values():
            yield from walk_exact_field_context(value,depth+1)
    elif isinstance(node,list):
        for item in node[:3000]:
            yield from walk_exact_field_context(item,depth+1)


def audit():
    data,sha,n=get_publisher_original_metadata()
    entries=list(walk_exact_field_context(data))
    results={}
    for target in TARGET:
        observed=[x for x in entries if x["field"]==target]
        semkeys=list(SYNONYMS.keys())
        results[target]={
          "original_variable_label_present_in_publisher_metadata":bool(observed),
          "source_metadata_nodes_with_exact_original_field_code":sum(
              x["metadata_field_code_exact_value_occurrences_in_node"]>0 for x in observed),
          "source_metadata_nodes_with_any_code_reference":len(observed),
          "nonempty_unit_property_occurring_same_object_as_source_code":sum(
              x["nonempty_unit_property_in_same_node"] for x in observed),
          "field_semantic_keyword_cooccurrence_counts_NOT_proof":{
              k:sum(x["semantic_description_keywords_in_same_node"][k] for x in observed) for k in semkeys
          },
          "publisher_original_metadata_object_field_names_only":sorted({
               key for x in observed for key in x["publisher_codebook_node_keys_only"]
          })[:30],
        }
    author_mapped=all(results[v]["source_metadata_nodes_with_exact_original_field_code"]>0 and
                      results[v]["nonempty_unit_property_occurring_same_object_as_source_code"]>0
                      for v in ("spec1","spec2","DWV"))
    return {
      "schema":"structural.BELongDead24546_spec1_spec2_DWV_Vharv_original_source_codebook.v1",
      "original_dataset_BExIS_ID":24546,
      "publisher_original_tag":"1.0",
      "published_individual_source_license_CC_BY4_confirmed_prior_CI":True,
      "publisher_metadata_sha256":sha,
      "publisher_original_metadata_bytes":n,
      "source_specific_field_semantic_metadata_evidence":results,
      "source_exact_spec1_spec2_DWV_metadata_unit_properties_all_recovered":author_mapped,
      "source_tree_type_and_volume_units_not_inferred_from_abbreviations":True,
      "source_original_metadata_prose_and_individual_site_IDs_NOT_EXPORTED":True,
      "no_source_original_deadwood_item_tree_measurement_values_READ":True,
      "no_source_original_BELongDead_beetle_taxa_captures_or_traits_READ":True,
      "old_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_frozen":True,
      "eBird_used":False,
      "status":"SOURCE_FIELD_CODEBOOK_DIRECT_AUTHOR_FIELDS_AND_UNIT_PROPERTIES_PRESENT_REQUIRE_SEMANTIC_REVIEW"
        if author_mapped else "SOURCE_FIELD_CODEBOOK_NOT_YET_VERIFIED_NO_BIOLOGY"
    }

def synthetic():
    obj={"AttributeName":"DWV","UnitName":"m3","Description":"deadwood volume m3"}
    hits=list(walk_exact_field_context(obj))
    assert len(hits)==1 and hits[0]["field"]=="DWV"
    assert hits[0]["nonempty_unit_property_in_same_node"]
    assert hits[0]["semantic_description_keywords_in_same_node"]["deadwood_volume"]
    assert not list(walk_exact_field_context({"AttributeName":"unrelated"}))
    print("SYNTHETIC_PUBLISHER_METADATA_FIELD_DESCRIPTION_UNIT_LEXICAL_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out needed")
    try:r=audit()
    except SourceStop as ex:
        r={
          "schema":"structural.BELongDead24546_spec1_spec2_DWV_Vharv_original_source_codebook.v1",
          "status":str(ex),
          "scientific_source_STOP_not_organismal_non_support":True,
          "old_original_results_unmodified":True,
        }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BExIS24546_spec1_spec2_DWV_original_metadata_codebook_sourceonly.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
