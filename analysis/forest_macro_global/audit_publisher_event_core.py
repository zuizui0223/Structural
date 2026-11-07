#!/usr/bin/env python3
"""Audit publisher-original DwC-A EVENT cores for a fixed seven-source cohort.

This is input ascertainment, NOT a forest-plot census or biodiversity analysis.
A distinct locationID is a candidate spatial identifier, never automatically
an independent field plot. Occurrence extensions and species values are not read.
Only dataset-level counts and provenance are exported (no coordinates or IDs).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

API = "https://api.gbif.org/v1/dataset/"
MAX_ARCHIVE_BYTES = 75 * 1024 * 1024
MAX_EVENT_ROWS = 400_000
MAX_EVENT_MEMBER_BYTES = 120 * 1024 * 1024
HEADERS = {"User-Agent": "Structural-Global-Forest-Event-Core-Only/1.0"}
EVENT_ROW_TYPE = "http://rs.tdwg.org/dwc/terms/Event"


def safe_string(value):
    return str(value or "").strip()


def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=35) as fd:
        data = fd.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError("metadata_response_size_stop")
    return json.loads(data)


def get_archive_endpoint(dataset):
    endpoints = dataset.get("endpoints") or []
    urls = []
    for endpoint in endpoints:
        kind = safe_string(endpoint.get("type")).upper()
        url = safe_string(endpoint.get("url"))
        if "DWC" in kind and "ARCHIVE" in kind:
            p = urllib.parse.urlsplit(url)
            if p.scheme == "https" and p.hostname and p.hostname.lower() not in ("localhost",):
                urls.append(url)
    if len(set(urls)) != 1:
        raise ValueError("unambiguous_https_publisher_dwca_endpoint_not_found")
    return urls[0]


def download_small_archive(url, cap=MAX_ARCHIVE_BYTES):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as fd:
        declared = fd.headers.get("Content-Length")
        if declared and int(declared) > cap:
            raise ValueError("publisher_archive_exceeds_bounded_download_cap")
        buf = io.BytesIO()
        total = 0
        while True:
            chunk = fd.read(min(1024 * 1024, cap - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > cap:
                raise ValueError("publisher_archive_exceeds_bounded_download_cap")
            buf.write(chunk)
    data = buf.getvalue()
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise ValueError("publisher_archive_not_dwca_zip")
    return data


def bare(tag):
    return tag.rsplit("}", 1)[-1]


def file_location(core):
    files = next((e for e in core if bare(e.tag) == "files"), None)
    if files is None:
        raise ValueError("core_files_missing")
    locations = [safe_string(e.text) for e in files if bare(e.tag) == "location"]
    if len(locations) != 1 or not locations[0]:
        raise ValueError("event_core_file_location_ambiguous")
    return locations[0]


def decode_separator(value, fallback):
    if value is None:
        return fallback
    if value == "":
        return ""
    s = value.replace(r"\t", "\t").replace(r"\n", "\n").replace(r"\r", "\r")
    if len(s) > 1:
        raise ValueError("unsupported_multichar_delimiter")
    return s


def event_schema(z):
    members = z.namelist()
    meta_names = [name for name in members if name.rsplit("/", 1)[-1] == "meta.xml"]
    if len(meta_names) != 1:
        raise ValueError("archive_requires_single_meta_xml")
    root = ET.fromstring(z.read(meta_names[0]))
    cores = [e for e in root if bare(e.tag) == "core"]
    if len(cores) != 1 or cores[0].attrib.get("rowType") != EVENT_ROW_TYPE:
        raise ValueError("archive_core_is_not_darwin_core_Event")
    core = cores[0]
    loc = file_location(core)
    if loc not in members:
        candidates = [x for x in members if x.endswith("/" + loc)]
        if len(candidates) != 1:
            raise ValueError("publisher_event_core_member_missing_or_ambiguous")
        loc = candidates[0]
    if z.getinfo(loc).file_size > MAX_EVENT_MEMBER_BYTES:
        raise ValueError("uncompressed_event_core_exceeds_cap")
    names = {}
    for e in core:
        if bare(e.tag) == "field":
            idx = int(e.attrib["index"])
            term = safe_string(e.attrib.get("term"))
            names[term.rsplit("/", 1)[-1]] = idx
    delim = decode_separator(core.attrib.get("fieldsTerminatedBy"), "\t")
    quote = decode_separator(core.attrib.get("fieldsEnclosedBy"), '"')
    if delim not in ("\t", ",", ";", "|"):
        raise ValueError("unexpected_event_core_delimiter")
    return loc, names, delim, quote, int(core.attrib.get("ignoreHeaderLines", "0")), core.attrib.get("encoding", "UTF-8")


def summarize_event_core(data):
    archive_sha256 = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        loc, col, delim, quote, skip, encoding = event_schema(z)
        if not {"eventID", "locationID"}.issubset(col):
            raise ValueError("event_or_location_id_missing_in_original_core")
        event_ids, location_ids = set(), set()
        event_count = 0
        missing_event_id = missing_location_id = 0
        repeated_event_ids = 0
        parents = set()
        forest_label_rows = 0
        method_rows = 0
        coord_complete = 0
        uncertainty_rows = 0
        dates_2019_2026 = 0
        all_coord_keys = defaultdict(set)
        with z.open(loc) as raw:
            txt = io.TextIOWrapper(raw, encoding=encoding, errors="strict", newline="")
            reader = csv.reader(txt, delimiter=delim, quotechar=quote or None,
                                quoting=csv.QUOTE_MINIMAL if quote else csv.QUOTE_NONE)
            for _ in range(skip):
                next(reader, None)
            for record in reader:
                if not record or not any(safe_string(v) for v in record):
                    continue
                event_count += 1
                if event_count > MAX_EVENT_ROWS:
                    raise ValueError("event_core_exceeds_row_cap")
                def field(name):
                    idx = col.get(name)
                    return safe_string(record[idx]) if idx is not None and idx < len(record) else ""
                eid, lid = field("eventID"), field("locationID")
                if not eid:
                    missing_event_id += 1
                elif eid in event_ids:
                    repeated_event_ids += 1
                else:
                    event_ids.add(eid)
                if not lid:
                    missing_location_id += 1
                else:
                    location_ids.add(lid)
                parent = field("parentEventID")
                if parent:
                    parents.add(parent)
                if field("habitat"):
                    forest_label_rows += 1
                if field("samplingProtocol"):
                    method_rows += 1
                if re.search(r"(?:^|[^0-9])20(?:19|2[0-6])(?:[^0-9]|$)", field("eventDate")):
                    dates_2019_2026 += 1
                lat, lon = field("decimalLatitude"), field("decimalLongitude")
                try:
                    latf, lonf = float(lat), float(lon)
                    if math.isfinite(latf) and math.isfinite(lonf) and abs(latf) <= 90 and abs(lonf) <= 180:
                        coord_complete += 1
                        if lid:
                            all_coord_keys[lid].add((round(latf, 5), round(lonf, 5)))
                except ValueError:
                    pass
                try:
                    unc = float(field("coordinateUncertaintyInMeters"))
                    if math.isfinite(unc) and unc >= 0:
                        uncertainty_rows += 1
                except ValueError:
                    pass
    if not event_count:
        raise ValueError("empty_original_event_core")
    return {
        "original_event_core_rows": event_count,
        "distinct_original_eventID_values": len(event_ids),
        "duplicate_eventID_rows": repeated_event_ids,
        "missing_eventID_rows": missing_event_id,
        "original_distinct_locationID_candidates_NOT_independent_plots": len(location_ids),
        "missing_locationID_rows": missing_location_id,
        "distinct_parentEventID_references": len(parents),
        "parentEventID_references_unresolved_in_core": len(parents - event_ids),
        "locationID_values_with_multiple_distinct_5dp_coordinate_pairs": sum(len(v)>1 for v in all_coord_keys.values()),
        "rows_with_samplingProtocol": method_rows,
        "rows_with_habitat": forest_label_rows,
        "rows_with_valid_coordinates": coord_complete,
        "rows_with_coordinateUncertaintyInMeters": uncertainty_rows,
        "rows_with_eventDate_in_2019_2026": dates_2019_2026,
        "publisher_archive_sha256": archive_sha256,
        "event_core_member": loc,
        "source_original_occurrence_extension_rows_read": 0,
        "species_or_abundance_values_read_or_stored": 0,
        "verified_independent_forest_plots": 0,
        "forest_plot_protocol_review_still_required": True,
    }


def audit_one(src, get_json=fetch_json, download=download_small_archive):
    uid = safe_string(src["dataset_uuid"])
    row = {
        "dataset_uuid": uid,
        "source_network_role": src["predefined_source_role_NOT_geography_proven"],
        "sample_country_facet": safe_string(src.get("actual_occurrence_country_facet_top5")),
        "indexed_recent_occurrences_NOT_sites": safe_string(src.get("indexed_occurrence_count_2019_2026_NOT_sites")),
        "status": "NOT_YET_VERIFIED",
        "original_independent_plot_count_verified": 0,
    }
    try:
        meta = get_json(API + uid)
        if safe_string(meta.get("key")) != uid or safe_string(meta.get("type")).upper() != "SAMPLING_EVENT":
            raise ValueError("dataset_uuid_or_sampling_event_type_mismatch")
        row["dataset_title"] = safe_string(meta.get("title"))
        row["license"] = safe_string(meta.get("license"))
        row["publisher_source_url"] = get_archive_endpoint(meta)
        row.update(summarize_event_core(download(row["publisher_source_url"])))
        row["status"] = "PUBLISHER_ORIGINAL_EVENT_CORE_VERIFIED_NOT_PLOT_VERIFIED"
    except Exception as e:
        row["status"] = "ORIGINAL_SOURCE_GATE_STOP"
        row["stop_class"] = type(e).__name__
        row["stop_reason"] = str(e)[:180]
    return row


def run(source, out, get_json=fetch_json, download=download_small_archive):
    rows = list(csv.DictReader(Path(source).open(encoding="utf-8", newline="")))
    selected = [r for r in rows if r.get("source_2020_canopy_alignment_status") ==
                "RECENT_OCCURRENCE_CANDIDATE_NOT_SITE_VERIFIED"]
    if len(selected) != 7 or len({r["dataset_uuid"] for r in selected}) != 7:
        raise ValueError("upstream_predefined_seven_source_cohort_drift")
    if any("ebird" in (r.get("title") or "").lower() for r in selected):
        raise ValueError("eBird forbidden")
    summaries = [audit_one(r, get_json, download) for r in selected]
    dest = Path(out)
    dest.mkdir(parents=True, exist_ok=True)
    cols = list(dict.fromkeys(k for d in summaries for k in d))
    with (dest / "original_event_core_network_counts_NOT_plot_counts.csv").open("w",newline="",encoding="utf-8") as fd:
        w = csv.DictWriter(fd, fieldnames=cols)
        w.writeheader()
        w.writerows(summaries)
    counts = Counter(x["status"] for x in summaries)
    manifest = {
        "schema": "structural.forest_macro_publisher_original_event_core_audit.v1",
        "fixed_networks": len(summaries),
        "original_event_core_verified_networks": counts.get("PUBLISHER_ORIGINAL_EVENT_CORE_VERIFIED_NOT_PLOT_VERIFIED", 0),
        "original_source_gate_stops": counts.get("ORIGINAL_SOURCE_GATE_STOP", 0),
        "verbatim_original_occurrence_extensions_opened": 0,
        "species_names_or_abundances_exported": 0,
        "verified_independent_forest_plots": 0,
        "plot_and_event_deduplication_require_original_methods": True,
        "biome_generalization_or_canopy_effect_computed": False,
        "eBird_used": False,
    }
    (dest / "original_event_core_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    run(args.source, args.out)
