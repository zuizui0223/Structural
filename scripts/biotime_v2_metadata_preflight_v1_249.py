#!/usr/bin/env python3
"""Response-opaque BioTIME 2.0 (15 April 2025) metadata-only source intake.

Never downloads, opens or makes biological-response queries to BioTIME RDS/SQL.
Only the author-published, version-locked metadata CSV is eligible.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

VERSION = "15222193"
FILENAME = "biotime_v2_metadata_15April25.csv"
EXPECTED_MD5 = "3daed71ed554888309f9f2443a847bea"
SOURCE_DOI = "10.5281/zenodo.15222193"
URLS = (
    f"https://zenodo.org/records/{VERSION}/files/{FILENAME}?download=1",
    f"https://zenodo.org/api/records/{VERSION}/files/{FILENAME}/content",
)
MAX_BYTES = 8_000_000

class SourceStop(Exception):
    pass


def source_bytes(opener=None):
    opener = opener or urllib.request.urlopen
    failures = []
    for url in URLS:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Structural-source-audit/1.0 (research; metadata only)",
            "Accept": "text/csv,application/octet-stream,*/*",
        })
        try:
            with opener(req, timeout=45) as response:
                raw = response.read(MAX_BYTES + 1)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            failures.append({"route":url.split("/api/")[0].split("?")[0] if "api/" not in url else "zenodo-api", "error_type":type(e).__name__, "reason":str(e)[:180]})
            continue
        if len(raw) > MAX_BYTES:
            raise SourceStop("Publisher metadata file exceeds frozen 8 MB maximum")
        actual = hashlib.md5(raw).hexdigest()
        if actual != EXPECTED_MD5:
            raise SourceStop(f"Exact published metadata MD5 mismatch: expected {EXPECTED_MD5}, got {actual}; do not read")
        return raw, url, failures
    raise SourceStop("All two exact publisher metadata routes failed: " + json.dumps(failures))


def _simple_numeric_year(value):
    s=(value or "").strip()
    if not s:
        return None
    if not re.fullmatch(r"(?:18|19|20)\d{2}(?:\.0+)?", s):
        return None
    return int(float(s))



def _integer_metadata(value):
    s=(value or "").strip()
    if not re.fullmatch(r"\d+(?:\.0+)?",s):
        return None
    return int(float(s))


def spatial_temporal_study_screen(records):
    """Pre-outcome potential, NEVER proof of same-plot temporal replication."""
    required=("STUDY_ID","START_YEAR","END_YEAR","NUMBER_LAT_LONG","NUMBER_OF_SAMPLES","NUMBER_OF_SPECIES","REALM")
    if not all(k in records[0] for k in required):
        return {"status":"MISSING_REQUIRED_FIELD","required_fields":list(required)}
    universe=set()
    counts=Counter()
    realms={}
    by_realm=Counter()
    for row in records:
        sid=str(row.get("STUDY_ID","")).strip()
        if not sid or sid in universe:
            raise SourceStop("Duplicate/missing BioTIME study ID; cannot count independent study units")
        universe.add(sid)
        start=_simple_numeric_year(row.get("START_YEAR"))
        end=_simple_numeric_year(row.get("END_YEAR"))
        nsites=_integer_metadata(row.get("NUMBER_LAT_LONG"))
        nsamples=_integer_metadata(row.get("NUMBER_OF_SAMPLES"))
        nspecies=_integer_metadata(row.get("NUMBER_OF_SPECIES"))
        realm=str(row.get("REALM","")).strip()
        if (start is None or end is None or nsites is None or nsamples is None or nspecies is None or end<start):
            counts["incomplete_or_inconsistent"]+=1
            continue
        years=end-start+1  # span, not number of actual sampled years
        counts["complete_metadata"]+=1
        by_realm[realm]+=1
        if years>=3 and nsites>=5:
            counts["span3_sites5"]+=1
        if years>=5 and nsites>=10:
            counts["span5_sites10"]+=1
        if years>=5 and nsites>=10 and nsamples>=100 and nspecies>=10:
            counts["span5_sites10_samples100_species10"]+=1
            counts["strong_candidate_"+realm]+=1
        if years>=8 and nsites>=20 and nsamples>=1000 and nspecies>=20:
            counts["span8_sites20_samples1000_species20"]+=1
    return {
        "status":"POTENTIAL_BY_METADATA_NOT_RESPONSE_APPROVED",
        "source_studies_seen":len(universe),
        "numerical_metadata_screen_counts":dict(counts),
        "complete_metadata_by_realm":dict(by_realm),
        "screen_basis":"Observed calendar span and number of georeferenced locations, sample events, taxa at study level",
        "not_yet_verified":[
            "the same location was surveyed in at least two or three separate years",
            "matched season and sampling method/effort across years",
            "a complete enumerated sample frame for species-by-site non-detections",
            "absence detection probability, island boundary and spatial network",
            "source-to-recipient dispersal, colonization or demographic rescue"
        ],
    }


def study_summary(raw:bytes):
    try:
        text=raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text=raw.decode("latin-1")
    reader=csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames or any(x is None or not x.strip() for x in reader.fieldnames):
        raise SourceStop("Invalid metadata header")
    fields=[str(x).strip() for x in reader.fieldnames]
    if len(set(x.casefold() for x in fields)) != len(fields):
        raise SourceStop("Non-unique metadata field names")
    name_map={x.casefold():x for x in fields}
    records=list(reader)
    if not 200<=len(records)<=10_000:
        raise SourceStop(f"Unexpected metadata rows: {len(records)}; do not assume one row is one study")
    nonempty={field:sum(bool((row.get(field) or "").strip()) for row in records) for field in fields}
    study_cols=[field for field in fields if re.fullmatch(r"(?:study[_\s-]?id|dataset[_\s-]?id)", field, flags=re.I)]
    unique_studies=None
    if study_cols:
        unique_studies=len({str(r.get(study_cols[0],"")).strip() for r in records if str(r.get(study_cols[0],"")).strip()})
    year_cols=[f for f in fields if re.search(r"year|^start_|^end_|duration", f,flags=re.I)]
    time_columns={}
    for col in year_cols:
        yr=[_simple_numeric_year(r.get(col)) for r in records]
        yrs=[x for x in yr if x is not None]
        time_columns[col]={"yearlike_rows":len(yrs),"min":min(yrs) if yrs else None, "max":max(yrs) if yrs else None}
    site_cols=[f for f in fields if re.search(r"(?:site|plot|location|latitud|longitud|sampling|replicate|method|realm|biome|island|country|taxa|taxon)", f,flags=re.I)]
    relevant_levels={}
    for col in fields:
        if col.upper() in ("REALM","BIOME_MAP","TAXA","ABUNDANCE_TYPE","BIOMASS_TYPE"):
            vals=[str(row.get(col,"")).strip() for row in records]
            counts=Counter(v for v in vals if v)
            relevant_levels[col]={"distinct":len(counts),"top_counts":[[key,count] for key,count in counts.most_common(10)]}
    return {
        "metadata_source_level_study_screen":spatial_temporal_study_screen(records),
        "metadata_rows":len(records),
        "metadata_columns":fields,
        "study_identifier_column":study_cols[0] if study_cols else None,
        "unique_study_identifiers":unique_studies,
        "yearlike_fields":time_columns,
        "candidate_spatial_and_sampling_fields":site_cols,
        "candidate_field_nonempty_counts":{x:nonempty[x] for x in site_cols},
        "reference_qualitative_categories":relevant_levels,
        "has_site_year_abundance_response":False,
        "has_verified_same_site_repeat_survey_denominator":False,
        "has_verified_source_recipient_movement":False,
        "has_verified_0_to_1_colonization":False,
        "data_read": "Zenodo metadata CSV only; no RDS/SQL response rows",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    record={
        "schema":"structural.biotime2_metadata_preflight.v1_249",
        "source_doi":SOURCE_DOI,
        "source_filename":FILENAME,
        "expected_publisher_md5":EXPECTED_MD5,
        "evidence_class":"METADATA_ONLY_NO_SPECIES_RESPONSE",
        "main_GEB_HOLD":True,
        "original_mammal_holdout_accesses":0,
        "new_confirmatory_admissions":0,
        "eBird_used":False,
    }
    try:
        data,url,failures=source_bytes()
        record.update({
            "status":"METADATA_RETRIEVED_AND_EXACT_PUBLISHER_MD5_CONFIRMED",
            "metadata_bytes":len(data),
            "source_url":url,
            "successful_metadata_md5":hashlib.md5(data).hexdigest(),
            "earlier_transport_failures":failures,
            "metadata_audit":study_summary(data),
        })
    except SourceStop as e:
        record.update({"status":"SOURCE_STOP_NO_DESIGN_ADMISSION","stop_reason":str(e)})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:record.get(k) for k in ("schema","status","metadata_bytes","source_doi","stop_reason")},sort_keys=True))
    if record["status"]!="METADATA_RETRIEVED_AND_EXACT_PUBLISHER_MD5_CONFIRMED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
