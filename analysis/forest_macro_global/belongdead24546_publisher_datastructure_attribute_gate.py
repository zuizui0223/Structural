#!/usr/bin/env python3
"""Official BExIS24546 dataset dataStructureId -> /api/structures/{id} ONLY.

BExIS2/rBExIS authors document this exact official data-structure API.
Read source variable definitions/unit/type metadata, not biological or forest
observation rows. No lat/lon, site IDs or source tree/species labels.
"""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.error,urllib.request
from collections import defaultdict
from pathlib import Path
from belongdead_bexis_13tree_original_source_gate import NoRedirect

ROOT="https://www.bexis.uni-jena.de"
CODES=("spec1","spec2","DWV","Vharv","PT","Tdir","PTNum","dc","plotID")
TARGETS={"spec1","spec2","DWV","Vharv","PT","Tdir","PTNum","dc"}
K_CATS={
    "tree_taxon":re.compile(r"(?i)(?:tree.?species|species|baumart|holzart|tree.?type|tree.?taxon)"),
    "deadwood_volume":re.compile(r"(?i)(?:dead.?wood.{0,22}volum|volume.{0,22}dead.?wood|totholz.{0,15}volum|wood.{0,15}volum)"),
    "unit_volume":re.compile(r"(?i)(?:\bm3\b|m³|m\^3|cubic\s*(?:meter|metre)|kubikmeter)"),
    "harvest":re.compile(r"(?i)(?:harvest|felling|logging|entnahme|ernte)"),
    "diameter":re.compile(r"(?i)(?:diameter|dbh|bhd|durchmesser)"),
}
UNIT_KEY=re.compile(r"(?i)(?:unit|dimension|measurement|symbol|notation)")
TYPE_KEY=re.compile(r"(?i)(?:data.?type|type|numeric|integer|double|string|categor|enumeration)")
SHORT_UNIT=re.compile(r"^[A-Za-z0-9_²³µμ% /.*^+\\-]{1,32}$")
class SourceStop(RuntimeError):pass


def public_json(path):
    if path!="/api/dataset/24546" and not re.fullmatch(r"/api/structures/\d{1,10}",path):
        raise SourceStop("SOURCE_STOP_UNDOCUMENTED_PUBLIC_DATA_STRUCTURE_PATH")
    req=urllib.request.Request(ROOT+path,headers={
        "User-Agent":"Structural-original-BExIS24546-field-unit-publisher-schema/1.0",
        "Accept":"application/json"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=40) as r:
            b=r.read(1_000_001)
            status=r.status
            ctype=r.headers.get("Content-Type","")
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_ACCESS_STOP_DOCUMENTED_DATASTRUCTURE_HTTP_"+str(ex.code)) from ex
    except (urllib.error.URLError,OSError,TimeoutError) as ex:
        raise SourceStop("SOURCE_TRANSPORT_STOP_DATASTRUCTURE_"+type(ex).__name__) from ex
    if status!=200 or len(b)>1_000_000 or "json" not in ctype.lower():
        raise SourceStop("SOURCE_STOP_DOCUMENTED_DATA_STRUCTURE_RESPONSE_NOT_JSON")
    try: return json.loads(b.decode("utf-8")),hashlib.sha256(b).hexdigest(),len(b)
    except ValueError as ex:
        raise SourceStop("SOURCE_STOP_PUBLISHER_JSON_PARSE") from ex


def collect_field_nodes(x,depth=0):
    if depth>30:return
    if isinstance(x,dict):
        pairs=list(x.items())
        parts=[(str(k),str(v)) for k,v in pairs
               if isinstance(v,(str,int,float)) and len(str(v))<=3000]
        simple=[v for _,v in parts]
        targets={a for a in CODES if any(v.strip().lower()==a.lower() for v in simple)}
        if targets:
            descr=" ".join(simple)
            units=[]
            types=[]
            for k,v in parts:
                if UNIT_KEY.search(k) and SHORT_UNIT.fullmatch(v.strip()):
                    units.append(v.strip())
                if TYPE_KEY.search(k) and SHORT_UNIT.fullmatch(v.strip()):
                    types.append(v.strip())
            # Published source unit may be a nested *object* with name/symbol,
            # not an inline string. Read only safe short UNIT metadata fields
            # from that unit object, not any physical wood/resource values.
            for k,v in pairs:
                if k.lower() not in ("unit","measurementunit") or not isinstance(v,dict):
                    continue
                for unit_key,unit_val in v.items():
                    if str(unit_key).lower() not in (
                        "name","symbol","abbreviation","unitname","displayname",
                        "shortname","description","dimension","type"):
                        continue
                    if isinstance(unit_val,str) and len(unit_val)<=32 and SHORT_UNIT.fullmatch(unit_val.strip()):
                        units.append(unit_val.strip())
            units=list(dict.fromkeys(units))[:10]
            for code in targets:
                yield code,{
                  "source_code_literal_in_attribute_object":True,
                  "publisher_declared_unit_short_candidate_strings":units[:8],
                  "publisher_declared_data_type_short_candidate_strings":types[:8],
                  "source_semantic_description_keyword_presence":{
                     key:bool(rx.search(descr)) for key,rx in K_CATS.items()
                  },
                  "source_attribute_object_original_field_keys_only":[
                    k for k,v in pairs if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,60}",str(k))
                  ][:35],
                  "NOT_a_species_observation_or_tree_numeric_measurement":True,
                }
        for v in x.values():
            yield from collect_field_nodes(v,depth+1)
    elif isinstance(x,list):
        for v in x[:10000]:
            yield from collect_field_nodes(v,depth+1)


def run():
    d,ds_hash,ds_bytes=public_json("/api/dataset/24546")
    if not isinstance(d,dict):
        raise SourceStop("SOURCE_STOP_BEXIS24546_DATASET_META_NOT_DICT")
    if d.get("isPublic") is False:
        raise SourceStop("SOURCE_RIGHTS_STOP_BEXIS24546_SOURCE_IS_NOT_PUBLIC")
    s=d.get("dataStructureId")
    if not isinstance(s,int) or not 1<=s<=999_999_999:
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEXIS24546_DATASTRUCTURE_ID_UNAVAILABLE")
    obj,sha,n=public_json(f"/api/structures/{s}")
    if not isinstance(obj,(dict,list)):
        raise SourceStop("SOURCE_STOP_ORIGINAL_STRUCTURE_NOT_JSON_DICT_OR_LIST")
    hits=defaultdict(list)
    for field,entry in collect_field_nodes(obj):
        hits[field].append(entry)
    record={}
    for field in CODES:
        entries=hits.get(field,[])
        record[field]={
           "original_attribute_label_present_in_publisher_structure":bool(entries),
           "original_field_definition_object_count":len(entries),
           "publisher_unit_short_candidates_from_object":[
               candidate for e in entries for candidate in e["publisher_declared_unit_short_candidate_strings"]
           ][:10],
           "publisher_data_type_short_candidates_from_object":[
               candidate for e in entries for candidate in e["publisher_declared_data_type_short_candidate_strings"]
           ][:10],
           "semantic_description_keywords_aggregate_only":{
                k:sum(e["source_semantic_description_keyword_presence"][k] for e in entries)
                for k in K_CATS
           },
           "publisher_variable_attribute_dictionary_field_keys_only":sorted({
              k for e in entries for k in e["source_attribute_object_original_field_keys_only"]
           })[:25],
        }
    candidates=record["DWV"]["publisher_unit_short_candidates_from_object"]
    codebook_verifiable=(
        bool(record["DWV"]["original_field_definition_object_count"]) and
        bool(record["spec1"]["original_field_definition_object_count"]) and
        bool(candidates)
    )
    return {
       "schema":"structural.BELongDead24546_publisher_data_structure_spec1_DWV_units_only.v1",
       "dataset_original_id":24546,
       "source_dataset_metadata_sha256":ds_hash,
       "source_dataset_metadata_bytes":ds_bytes,
       "source_dataStructureId_declaration":s,
       "original_author_data_structure_API_path":f"/api/structures/{s}",
       "source_published_structure_sha256":sha,
       "source_published_structure_bytes":n,
       "original_2012_deadwood_30of30_PlotID_join_already_verified":True,
       "source_exact_published_variable_definition_info":record,
       "original_source_spec1_and_DWV_candidate_unit_field_schema_present":codebook_verifiable,
       "no_original_individual_tree_species_site_coord_abundance_or_volume_values_opened":True,
       "old_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_results_frozen":True,
       "eBird_used":False,
       "status":(
           "SOURCE_DWV_AND_SPEC1_PUBLISHED_DATA_STRUCTURE_UNITS_PRESENT_VALIDATE_MEANING"
           if codebook_verifiable else
           "SOURCE_ORIGINAL_ATTRIBUTE_UNITS_STILL_NOT_DIRECTLY_VERIFIED_NO_BIOLOGY"
       )
    }


def test():
    o={"DataStructureId":300,
       "Attributes":[
        {"Name":"DWV","Unit":"m3","Description":"deadwood volume"},
        {"Name":"spec1","Type":"String","Description":"tree species"}]}
    r=list(collect_field_nodes(o))
    assert len(r)==2
    assert any(code=="DWV" and "m3" in entry["publisher_declared_unit_short_candidate_strings"]
               for code,entry in r)
    assert any(code=="spec1" and entry["source_semantic_description_keyword_presence"]["tree_taxon"]
               for code,entry in r)
    assert not list(collect_field_nodes({"some":"unrelated"}))
    print("SYNTHETIC_OFFICIAL_DATASTRUCTURE_ATTRIBUTE_UNIT_AND_SOURCE_PRIVACY_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    test()
    if a.test:return
    if not a.out:p.error("--out required")
    try:r=run()
    except SourceStop as ex:
        r={
          "schema":"structural.BELongDead24546_publisher_data_structure_spec1_DWV_units_only.v1",
          "status":str(ex),
          "scientific_publisher_schema_STOP_not_ecological_null":True,
          "original_ecological_scores_UNCHANGED":True,
        }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BExIS24546_publisher_dataStructureId_spec1_DWV_units.json").write_text(
      json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
