#!/usr/bin/env python3
"""Published Piccini 2026 full-layer beetles: original METHOD COLUMNS ONLY.
Official source row text is streamed but biological cells are never selected,
summed, scored, or exported. No protected Structural scores are re-opened.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

from piccini2026_gro_three_strata_source_only_gate import (
    HOST,HEADERS,get_public_json,datacite_only,gro_only,SourceStop
)
from piccini2026_gro_original_header_only_gate import (
    DOI,CATEGORIES,normalized,summarized_header,legitimate_first_line
)

MAX_FILE=4_000_000
SEMICOLON_HEADER_COLUMNS=17
TAB_HEADER_COLUMNS=3
ROLE_KEYS=("physical_site","vertical_layer","sample_year","method_effort")
class MethodStop(RuntimeError):pass

def metadata_source_files():
    dc_status,dc=get_public_json("https://api.datacite.org/dois/"+DOI)
    api=HOST+"/api/datasets/:persistentId/?"+urllib.parse.urlencode({"persistentId":"doi:"+DOI})
    ds_status,ds=get_public_json(api)
    if dc is None or ds is None:
        raise MethodStop("SOURCE_STOP_PUBLISHER_METADATA_UNAVAILABLE")
    try:
        x=datacite_only(DOI,dc);y=gro_only(DOI,ds)
    except SourceStop as e:
        raise MethodStop("SOURCE_STOP_PUBLISHER_METADATA_SCHEMA") from e
    if not all(x.get(k,False) for k in (
        "published_DOI_exact_match","publisher_metadata_present",
        "title_metadata_present","published_publication_year_metadata_present")):
        raise MethodStop("SOURCE_STOP_DATACITE_NOT_VERIFIED")
    if not y["source_DOI_exact_match"] or not y["published_version_exists"]:
        raise MethodStop("SOURCE_STOP_GRO_SOURCE_IDENTITY_NOT_VERIFIED")
    if y["metadata_file_record_count"]!=2 or y["metadata_restricted_file_count"]!=0:
        raise MethodStop("SOURCE_STOP_SOURCE_FILE_COUNT_RIGHTS_DRIFT")
    files=ds["data"]["latestVersion"]["files"]
    result=[]
    for f in files:
        d=f.get("dataFile") or {}
        fid=d.get("id");size=d.get("filesize")
        mime=str(d.get("contentType","")).lower()
        if not (isinstance(fid,int) and fid>0 and isinstance(size,int)
                and 0<size<=MAX_FILE and mime.startswith("text/")
                and not f.get("restricted",False)):
            raise MethodStop("SOURCE_STOP_SOURCE_FILE_METADATA_NOT_ELIGIBLE")
        result.append({"file_id":fid,"expected_size":size,
                       "published_checksum":d.get("checksum")})
    return result

def head_shape(fid):
    r=legitimate_first_line(fid)
    if r.get("status")!="FIRST_LINE_READ_SCHEMA_ONLY":
        raise MethodStop("SOURCE_STOP_ORIGINAL_FILE_HEADER_UNREADABLE")
    return r

def get_one_original_publisher_file(file_id,expected_size):
    """Single regular GET, no retries/alternate URLs; bytes remain private."""
    req=urllib.request.Request(HOST+"/api/access/datafile/"+str(file_id),
                               headers=HEADERS,method="GET")
    try:
        with urllib.request.urlopen(req,timeout=34) as response:
            data=response.read(MAX_FILE+1)
            if response.status!=200:
                raise MethodStop("SOURCE_STOP_OFFICIAL_DATAFILE_NON200")
    except urllib.error.HTTPError as e:
        raise MethodStop("SOURCE_ACCESS_STOP_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise MethodStop("SOURCE_TRANSPORT_STOP_"+type(e).__name__) from e
    if len(data)!=expected_size or len(data)>MAX_FILE:
        raise MethodStop("SOURCE_STOP_ORIGINAL_FILE_BYTE_SIZE_DRIFT")
    return data

def field_roles(header:list[str]):
    # Whitelist only; no raw source field names exported.
    return {kind:[i for i,h in enumerate(header)
                  if normalized(h) in CATEGORIES[kind]] for kind in ROLE_KEYS}

def anonymous_method_grain(raw:bytes,source_checksum:dict|None):
    try:
        body=raw.decode("utf-8-sig")
    except UnicodeError as e:
        raise MethodStop("SOURCE_STOP_METHOD_TEXT_NOT_UTF8") from e
    reader=csv.reader(io.StringIO(body,newline=""),delimiter=";",strict=True)
    try:header=next(reader)
    except (StopIteration,csv.Error) as e:
        raise MethodStop("SOURCE_STOP_CSV_FIRST_HEADER") from e
    if len(header)!=SEMICOLON_HEADER_COLUMNS:
        raise MethodStop("SOURCE_STOP_17FIELD_AUTHOR_HEADER_DRIFT")
    roles=field_roles(header)
    if not roles["physical_site"] or not roles["vertical_layer"]:
        raise MethodStop("SOURCE_METHOD_HIERARCHY_NOT_IDENTIFIABLE_NO_SITE_LAYER")
    selected=[i for kind in ROLE_KEYS for i in roles[kind]]
    if len(selected)!=len(set(selected)):
        raise MethodStop("SOURCE_STOP_SOURCE_METHOD_FIELD_COLLISION")
    if len(selected)>12:
        raise MethodStop("SOURCE_STOP_EXCESSIVE_GENERIC_METHOD_COLUMNS")
    distinct_by_col={i:set() for i in selected}
    missing_by_col={i:0 for i in selected}
    contexts=set()
    site_layer=set()
    site_year=set()
    site_set=set()
    layer_set=set()
    layer_by_site=defaultdict(set)
    row_count=0
    try:
        for row in reader:
            row_count+=1
            if len(row)!=SEMICOLON_HEADER_COLUMNS:
                raise MethodStop("SOURCE_STOP_ORIGINAL_17COLUMN_ROW_SHAPE_DRIFT")
            # STRICTLY select method columns. Taxon/trait/count/resource column
            # values are never referenced in this method-only estimator.
            vals={i:row[i].strip() for i in selected}
            for i,v in vals.items():
                if v:distinct_by_col[i].add(v)
                else:missing_by_col[i]+=1
            contexts.add(tuple(vals[i] for i in sorted(selected)))
            s=tuple(vals[i] for i in roles["physical_site"])
            layer=tuple(vals[i] for i in roles["vertical_layer"])
            years=tuple(vals[i] for i in roles["sample_year"])
            if all(s):
                site_set.add(s)
                if all(layer):
                    site_layer.add((s,layer))
                    layer_by_site[s].add(layer)
                if years and all(years):
                    site_year.add((s,years))
            if all(layer): layer_set.add(layer)
            if row_count>100000:
                raise MethodStop("SOURCE_STOP_ORIGINAL_RECORD_COUNT_OVER100K")
    except csv.Error as e:
        raise MethodStop("SOURCE_STOP_AUTHOR_CSV_PARSER") from e
    if row_count==0:
        raise MethodStop("SOURCE_STOP_ORIGINAL_EMPTY_RECORDS")
    # Verify publisher checksum only if exposed in the file metadata.
    checksum_status="PUBLISHER_CHECKSUM_NOT_ADVERTISED"
    if isinstance(source_checksum,dict) and source_checksum.get("type","").lower()=="md5":
        value=str(source_checksum.get("value","")).lower()
        if hashlib.md5(raw).hexdigest()!=value:
            raise MethodStop("SOURCE_STOP_PUBLISHER_MD5_ORIGINAL_FILE_DRIFT")
        checksum_status="PUBLISHER_MD5_MATCH"
    role_distinct={
       role:sorted(len(distinct_by_col[i]) for i in roles[role])
       for role in ROLE_KEYS
    }
    role_missing={
       role:sorted(missing_by_col[i] for i in roles[role])
       for role in ROLE_KEYS
    }
    return {
       "status":"SOURCE_METHOD_CANDIDATE_COUNTS_ONLY_NO_AUTHOR_HIERARCHY_ASSERTED",
       "original_method_scanned_source_rows":row_count,
       "original_17source_columns_reproduced":True,
       "generic_field_count_by_role":{k:len(v) for k,v in roles.items()},
       "generic_field_distinct_label_counts_by_role":role_distinct,
       "generic_field_missing_cell_counts_by_role":role_missing,
       "unique_all_generic_method_contexts_NOT_independent_sample_units":len(contexts),
       "unique_generic_site_key_combinations_NOT_independent_sites":len(site_set),
       "unique_site_by_layer_candidate_combinations":len(site_layer),
       "unique_site_by_year_candidate_combinations":len(site_year),
       "unique_vertical_layer_value_combinations":len(layer_set),
       "candidate_site_keys_with_at_least_three_distinct_layer_labels":
            sum(len(x)>=3 for x in layer_by_site.values()),
       "source_checksum_status":checksum_status,
       "NO_species_names_guild_values_abundances_environment_extracted_or_scored":True,
       "NO_original_18_or_more_sites_inferred_from_nonindependent_traps":True,
       "original_all_method_key_strings_PRIVATE_NOT_EXPORTED":True,
    }

def single_author_method_pass():
    result={
      "source_original_DOI":DOI,
      "status":"SOURCE_NOT_SCORED",
      "source_original_2024_canopy_file_UNREAD":True,
      "source_beetle_species_and_guild_measurements_UNSCORED":True,
    }
    try:
        files=metadata_source_files()
        candidate=[]
        for f in files:
            h=head_shape(f["file_id"])
            candidate.append((f,h))
        main=[f for f,h in candidate if h["header_column_count"]==17
              and h["header_delimiter_category"]=="semicolon"]
        other=[f for f,h in candidate if h["header_column_count"]==3
              and h["header_delimiter_category"]=="tab"]
        if len(main)!=1 or len(other)!=1:
            raise MethodStop("SOURCE_STOP_ORIGINAL_TWO_FILE_HEADER_ARCHITECTURE_DRIFT")
        mainfile=main[0]
        # FULL regular 2026 author file is read into private RAM ONLY here,
        # method columns selected in parser; taxon/count columns not accessed.
        raw=get_one_original_publisher_file(mainfile["file_id"],mainfile["expected_size"])
        result["original_author_method_only"]=anonymous_method_grain(
            raw,mainfile["published_checksum"])
        result["status"]="ORIGINAL_METHOD_FIELDS_SCANNED_SOURCE_SITE_GRAIN_STILL_NOT_AUTHORIZED"
    except MethodStop as e:
        result["status"]=str(e)
        result["source_STOP_not_biological_null"]=True
    return result

def known_truth():
    header="PlotID;Layer;Year;TrapID;Species;Abundance;FeedingGuild;X;Y;Z;A;B;C;D;E;F;G"
    rows=[
      "P1;canopy;2019;T1;Aaaa;14;pred;;0;;;;;;;;",
      "P1;floor;2019;T2;Bbbb;21;herb;;0;;;;;;;;",
      "P2;floor;2019;T3;Cccc;0;pred;;0;;;;;;;;",
    ]
    txt=(header+"\n"+"\n".join(rows)+"\n").encode()
    # Synthetic rows above have 17 fields ONLY if final delimiters are right.
    parsed=list(csv.reader(io.StringIO(txt.decode()),delimiter=";"))
    assert len(parsed[0])==17
    for row in parsed[1:]:
        assert len(row)==17, (len(row),"synthetic")
    a=anonymous_method_grain(txt,None)
    assert a["original_method_scanned_source_rows"]==3
    assert a["unique_generic_site_key_combinations_NOT_independent_sites"]==2
    assert a["unique_site_by_layer_candidate_combinations"]==3
    assert a["generic_field_count_by_role"]=={
       "physical_site":1,"vertical_layer":1,"sample_year":1,"method_effort":1}
    assert "Bbbb" not in json.dumps(a) and "14" not in json.dumps(a)
    print("SYNTHETIC_METHOD_COLUMNS_SOURCE_ONLY_SITE_LAYER_YEAR_GRAIN_AND_REDACTION_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:ap.error("--out needed")
    r={"schema":"structural.Piccini2026_original_GRO_method_fields_sourceonly.v1",
       "protocol":"docs/FOREST_BEETLE_PICCINI2026_METHOD_COLUMNS_SOURCE_ONLY_PRESPEC_20261116.md",
       "result":single_author_method_pass(),
       "source_publication_prior_art_DOI":"10.1111/1365-2664.70472",
       "prior_Thai_Finland_PREDICTS_NEON_BALA_GEB_SCORES_UNCHANGED":True,
       "no_species_community_estimator_computed":True,
       "eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Piccini2026_original_GRO_method_fields_sourceonly.json").write_text(
       json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
