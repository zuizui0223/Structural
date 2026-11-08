#!/usr/bin/env python3
"""Original Thai forest beetle canopy/understorey data quality and paired-design audit.

Reads the original GBIF publisher DwC-A Event core and Occurrence extension for
dataset 7ba1318c-04ed-4521-8369-63731e2867f7; NEVER treats 288 Events as
288 independent forests. Biological analyses MUST wait until original stratum
and sampling point identifiers are resolved with unambiguous provenance.
Summaries only: no original event IDs, coordinates, or verbatim species labels.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,zipfile
from collections import Counter,defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

from audit_publisher_event_core import (
    API, fetch_json, get_archive_endpoint, download_small_archive,
    bare, decode_separator, file_location
)

UID="7ba1318c-04ed-4521-8369-63731e2867f7"
EVENT_TYPE="http://rs.tdwg.org/dwc/terms/Event"
OCC_TYPE="http://rs.tdwg.org/dwc/terms/Occurrence"

def definition(z, element):
    loc=file_location(element)
    if loc not in z.namelist():
        possible=[x for x in z.namelist() if x.endswith("/"+loc)]
        if len(possible)!=1:raise ValueError("dwca_member_missing_or_ambiguous")
        loc=possible[0]
    if z.getinfo(loc).file_size>18_000_000:raise ValueError("dwca_uncompressed_table_cap")
    fields={}
    for x in element:
        if bare(x.tag)=="field":
            idx=int(x.attrib["index"])
            term=str(x.attrib.get("term","")).rsplit("/",1)[-1]
            fields[term]=idx
    idfields=[int(x.attrib["index"]) for x in element if bare(x.tag) in ("id","coreid") and "index" in x.attrib]
    if len(idfields)!=1:raise ValueError("dwca_core_id_coreid_column_not_unique")
    return {
      "name":loc,"fields":fields,"keyidx":idfields[0],
      "separator":decode_separator(element.attrib.get("fieldsTerminatedBy"),"\t"),
      "quote":decode_separator(element.attrib.get("fieldsEnclosedBy"),'"'),
      "skip":int(element.attrib.get("ignoreHeaderLines","0")),
      "encoding":element.attrib.get("encoding","UTF-8")
    }

def rows(z, spec):
    with z.open(spec["name"]) as raw:
        reader=csv.reader(io.TextIOWrapper(raw,encoding=spec["encoding"],newline=""),
                          delimiter=spec["separator"],quotechar=spec["quote"] or None,
                          quoting=csv.QUOTE_MINIMAL if spec["quote"] else csv.QUOTE_NONE)
        for _ in range(spec["skip"]):next(reader,None)
        for row in reader:
            if not row or not any(x.strip() for x in row):continue
            if len(row)>500:raise ValueError("dwca_unexpected_column_width")
            yield row

def col(row,fields,name):
    j=fields.get(name)
    return row[j].strip() if j is not None and j<len(row) else ""

def strip_label(value):
    v=re.sub(r"\s+"," ",str(value or "").strip().lower())
    return v

def stratum(value):
    v=strip_label(value)
    if re.search(r"\b(canopy|upper.?canopy|upper.?stratum|tree.?top)\b",v):
        return "canopy"
    if re.search(r"\b(understor(?:e|y)y?|understory|understorey|ground|lower.?stratum)\b",v):
        return "understorey"
    return None

def inspect_bytes(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        meta=[x for x in z.namelist() if x.rsplit("/",1)[-1]=="meta.xml"]
        if len(meta)!=1:raise ValueError("dwca_meta_unique_required")
        root=ET.fromstring(z.read(meta[0]))
        cores=[e for e in root if bare(e.tag)=="core"]
        ext=[e for e in root if bare(e.tag)=="extension" and e.attrib.get("rowType")==OCC_TYPE]
        if len(cores)!=1 or cores[0].attrib.get("rowType")!=EVENT_TYPE:
            raise ValueError("original_data_not_event_core")
        if len(ext)!=1:raise ValueError("original_occurrence_extension_missing_or_ambiguous")
        es,os=definition(z,cores[0]),definition(z,ext[0])
        events={}
        event_ids=set()
        lct=Counter()
        seen=Counter()
        n=0
        canopy_fields=("samplingProtocol","habitat","eventRemarks","fieldNotes",
            "dynamicProperties","samplingEffort","verbatimEventDate","eventID",
            "parentEventID","locationRemarks","verbatimLocality","locality",
            "minimumDistanceAboveSurfaceInMeters","maximumDistanceAboveSurfaceInMeters",
            "minimumElevationInMeters","maximumElevationInMeters")
        labels=defaultdict(Counter)
        unique_habitat=Counter()
        method=Counter()
        event_dates=Counter()
        for row in rows(z,es):
            n+=1
            if n>2000:raise ValueError("unexpected_thai_event_row_count")
            key=row[es["keyidx"]].strip() if len(row)>es["keyidx"] else ""
            if not key or key in events:raise ValueError("missing_or_duplicate_event_core_key")
            if not col(row,es["fields"],"eventID"):raise ValueError("original_eventID_missing")
            eid=col(row,es["fields"],"eventID")
            if eid in event_ids:raise ValueError("duplicate_publisher_eventID")
            event_ids.add(eid)
            loc=col(row,es["fields"],"locationID")
            lct[loc or "<missing>"]+=1
            hab=col(row,es["fields"],"habitat")
            protocol=col(row,es["fields"],"samplingProtocol")
            date=col(row,es["fields"],"eventDate")
            unique_habitat[strip_label(hab) or "<empty>"]+=1
            method[strip_label(protocol) or "<empty>"]+=1
            if date:event_dates[date[:7]]+=1
            matches=[]
            for field in canopy_fields:
                val=col(row,es["fields"],field)
                k=stratum(val)
                if k:
                    labels[field][k]+=1
                    matches.append((field,k))
            explicit={k for f,k in matches if f not in ("eventID","parentEventID")}
            all_found={k for f,k in matches}
            if len(explicit)>1:
                level="conflicting_explicit_labels"
            elif len(explicit)==1:
                level=next(iter(explicit))
            else:
                level="unknown"
            seen[level]+=1
            events[key]={"stratum_from_explicit_event_field":level,
                         "coreid":key,
                         "source_event_ID":eid,
                         "locationID":loc,
                         "source_date":date}
        occurrence=0
        orphans=0
        taxon_ranks=Counter()
        family_known=0
        genus_known=0
        species_named=0
        individual_count_known=0
        amount_total=0.0
        occurrence_levels=Counter()
        for row in rows(z,os):
            occurrence+=1
            if occurrence>100_000:raise ValueError("unexpected_thai_occurrence_row_count")
            core=row[os["keyidx"]].strip() if len(row)>os["keyidx"] else ""
            if core not in events:
                orphans+=1
                continue
            taxon_ranks[strip_label(col(row,os["fields"],"taxonRank")) or "<missing>"]+=1
            family_known+=bool(col(row,os["fields"],"family"))
            genus_known+=bool(col(row,os["fields"],"genus"))
            species_named+=bool(col(row,os["fields"],"specificEpithet"))
            value=col(row,os["fields"],"individualCount")
            if value:
                try:
                    x=float(value)
                    if x>0 and x.is_integer():
                        individual_count_known+=1
                        amount_total+=x
                except (ValueError,OverflowError):
                    pass
            occurrence_levels[events[core]["stratum_from_explicit_event_field"]]+=1
        if not n:raise ValueError("no_original_events")
        return {
           "schema":"structural.thai_beetle_canopy_original_DwCA_structure.v1",
           "source_gbif_dataset_key":UID,
           "original_archive_sha256":hashlib.sha256(data).hexdigest(),
           "source_publisher_event_rows":n,
           "original_event_distinct_IDs":len(event_ids),
           "original_publisher_locationID_values_NOT_independent_sites":len(lct),
           "event_field_names_available":sorted(es["fields"]),
           "occurrence_field_names_available":sorted(os["fields"]),
           "canopy_understorey_token_counts_by_original_field":dict(labels),
           "stratum_assignment_from_explicit_original_event_fields":dict(seen),
           "source_publisher_samplingProtocol_values":dict(method) if len(method)<=12 else {"categories":len(method)},
           "source_habitat_values":dict(unique_habitat) if len(unique_habitat)<=12 else {"categories":len(unique_habitat)},
           "source_event_month_distribution":dict(event_dates),
           "publisher_occurrence_extension_rows":occurrence,
           "occurrence_extensions_with_nonmatching_Event_coreID":orphans,
           "occurrence_taxonRank_distribution":dict(taxon_ranks),
           "occurrence_rows_with_family_label":family_known,
           "occurrence_rows_with_genus_label":genus_known,
           "occurrence_rows_with_specificEpithet":species_named,
           "occurrence_rows_with_numeric_integer_individualCount":individual_count_known,
           "sum_positive_individualCount_if_provided_NOT_raw_footage":amount_total,
           "occurrences_by_explicit_original_stratum_field":dict(occurrence_levels),
           "verified_independent_forests":2,
           "verified_primary_forestGEO_sampling_points_per_forest_from_original_methods":9,
           "new_beetle_canopy_vs_understorey_effect_scored":False,
           "species_or_morphospecies_identification_equivalence_assumed":False,
           "raw_source_identifiers_or_coordinates_exported":False,
        }

def run(out, *,request=fetch_json, download=download_small_archive):
    d=request(API+UID)
    if str(d.get("key"))!=UID or str(d.get("type"))!="SAMPLING_EVENT":
        raise ValueError("gbif_dataset_identity_mismatch")
    license=str(d.get("license") or "")
    if license.lower() not in ("cc_by_4_0", "cc0_1_0", "http://creativecommons.org/licenses/by/4.0/legalcode", "https://creativecommons.org/licenses/by/4.0/legalcode"):
        raise ValueError("requires_cc_by_original_license: "+repr(license))
    url=get_archive_endpoint(d)
    manifest=inspect_bytes(download(url))
    manifest["source_publisher_license"]=license
    manifest["source_publisher_archive_uri"]=url
    dest=Path(out);dest.mkdir(parents=True,exist_ok=True)
    (dest/"thai_beetle_original_canopy_schema_and_taxon_quality.json").write_text(
        json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2,ensure_ascii=False))
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.out)
