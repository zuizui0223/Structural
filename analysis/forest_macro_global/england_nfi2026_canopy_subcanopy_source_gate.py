#!/usr/bin/env python3
"""UK Forestry Commission NFI 2023-26 canopy/subcanopy original ZIP source gate.

Read ZIP directory and CSV/TSV FIRST HEADER LINES ONLY. Never open field
species/OTU records, plot rows, location values or original sample response.
The result is source-readiness metadata, NOT vertical niche effects.
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
import tempfile
import urllib.error
import urllib.request
import zipfile

PRESPEC = "docs/FOREST_NFI_ENGLAND_2026_CANOPY_SUBCANOPY_ORIGINAL_SOURCE_GATE_PRESPEC_20261118.md"
SOURCE_UUID = "2b8a8f17-3745-43d1-bb32-0d509230f158"
SOURCE_URL = (
    "https://environment.data.gov.uk/api/file/download"
    "?fileDataSetId=e0405f9f-9b5a-4162-b7f7-ac06938c69ac"
    "&fileName=eDNA+Woodland+Canopy+Subcanopy+Data+2023-26.zip"
)
MAX_COMPRESSED = 1536 * 1024 * 1024
MAX_FIRST_HEADER = 8 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10000
MAX_DELIMITED_MEMBERS_TO_INSPECT = 60
BAD_EXPORTED_FIELDS = ("original_species", "original_plot_id", "individual_sample_name")
FAMILIES = {
    "source_sample_identity_candidate": re.compile(r"(?i)(sample|specimen|replicat|trap.?id|event.?id)"),
    "source_plot_identity_candidate": re.compile(r"(?i)(plot.?id|site.?id|location.?id|woodland.?id)"),
    "delocalisation_candidate_NOT_site": re.compile(r"(?i)(deloc|grid.?id|polygon.?id|centroid)"),
    "layer_or_trap_method_candidate": re.compile(r"(?i)(canopy|sub.?canopy|strat|layer|lindgren|malaise|trap.?type|method)"),
    "tree_identity_or_forest_class_candidate": re.compile(r"(?i)(tree.?species|woodland.?type|forest.?type|dominant.?tree|habitat)"),
    "sampling_time_or_effort_candidate": re.compile(r"(?i)(date|year|month|period|effort|duration|hour|deploy)"),
    "taxonomic_or_otu_candidate": re.compile(r"(?i)(otu|species|family|genus|taxon|sequence|read.?count)"),
    "coordinate_candidate_MASKED": re.compile(r"(?i)(lat|lon|easting|northing|grid.?east|grid.?north)"),
    "microclimate_candidate_UNVERIFIED": re.compile(r"(?i)(microclimat|humidity|temperature|temp.?c|logger)"),
    "deadwood_candidate_UNVERIFIED": re.compile(r"(?i)(dead.?wood|snag|log.?volume|wood.?resource)"),
}
class SourceStop(Exception):
    pass

def retrieve_original(tmp_path: Path) -> tuple[int, str, str]:
    """Only one original publisher URL; copy bytes to temporary runner filesystem."""
    req = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "Structural-source-only-forest-macro/1.0",
                 "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.2"},
        method="GET",
    )
    digest = hashlib.sha256()
    n = 0
    with urllib.request.urlopen(req, timeout=90) as resp:
        final_scheme = urllib.parse.urlsplit(resp.geturl()).scheme
        if final_scheme != "https":
            raise SourceStop("SOURCE_NFI_2026_PUBLISHER_NON_HTTPS_REDIRECT_STOP")
        declared = resp.headers.get("Content-Length")
        if declared:
            try:
                if int(declared) > MAX_COMPRESSED:
                    raise SourceStop("SOURCE_NFI_2026_ORIGINAL_ZIP_BIGGER_THAN_1536MiB")
            except ValueError:
                pass
        typ = (resp.headers.get("Content-Type") or "").lower()
        if "text/html" in typ or "application/json" in typ:
            raise SourceStop("SOURCE_NFI_2026_ORIGINAL_ARCHIVE_HTTP_NOT_ZIP")
        with tmp_path.open("wb") as out:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                n += len(chunk)
                if n > MAX_COMPRESSED:
                    raise SourceStop("SOURCE_NFI_2026_ORIGINAL_DOWNLOAD_SIZE_LIMIT_STOP")
                out.write(chunk)
                digest.update(chunk)
    if n < 100:
        raise SourceStop("SOURCE_NFI_2026_ORIGINAL_ARCHIVE_TOO_SMALL")
    return n, digest.hexdigest(), "original_publisher_https"

def safe_extension(name: str) -> str:
    s = name.lower().rsplit("/", 1)[-1]
    ext = "." + s.rsplit(".", 1)[-1] if "." in s else "<none>"
    return ext if len(ext) <= 12 else "<other>"

def header_first_line_only(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict:
    # Only the first line, no biological/site rows. Values and headers not exported.
    with zf.open(info, "r") as fp:
        raw = fp.readline(MAX_FIRST_HEADER + 1)
    if len(raw) > MAX_FIRST_HEADER or b"\n" not in raw:
        raise SourceStop("SOURCE_NFI_2026_FIRST_HEADER_TOO_LONG_OR_NOT_LINE_TERMINATED")
    try:
        text = raw.decode("utf-8-sig").strip("\r\n")
    except UnicodeDecodeError as exc:
        raise SourceStop("SOURCE_NFI_2026_FIRST_HEADER_UTF8_STOP") from exc
    # Some publisher tables are wide; sniff delimiter without learning any values.
    sep = max((",", ";", "\t"), key=lambda x: text.count(x))
    if text.count(sep) == 0:
        raise SourceStop("SOURCE_NFI_2026_DELIMITED_HEADER_UNPARSABLE")
    try:
        cols = next(csv.reader([text], delimiter=sep, strict=True))
    except (csv.Error, StopIteration) as exc:
        raise SourceStop("SOURCE_NFI_2026_DELIMITED_HEADER_CSV_PARSE_STOP") from exc
    if len(cols) < 2:
        raise SourceStop("SOURCE_NFI_2026_DELIMITED_HEADER_TOO_FEW_FIELDS")
    # Aggregate flags only; no raw names, sample IDs, OTU names or taxa leaked.
    return {
        "source_first_header_field_count": len(cols),
        "header_has_field_family": {
            k: any(pattern.search(c or "") for c in cols) for k, pattern in FAMILIES.items()
        },
        "first_header_line_only_data_rows_read": 0,
    }

def inspect_zip(source_file: Path) -> dict:
    try:
        with zipfile.ZipFile(source_file, "r") as zf:
            members = [x for x in zf.infolist() if not x.is_dir()]
            if not members or len(members) > MAX_ARCHIVE_MEMBERS:
                raise SourceStop("SOURCE_NFI_2026_ARCHIVE_MEMBER_COUNT_STOP")
            endings = Counter(safe_extension(x.filename) for x in members)
            candidates = [x for x in members if safe_extension(x.filename) in (".csv", ".tsv")]
            headers = []
            for info in candidates[:MAX_DELIMITED_MEMBERS_TO_INSPECT]:
                try:
                    inspected = header_first_line_only(zf, info)
                    inspected["source_table_type_only"] = safe_extension(info.filename)
                    headers.append(inspected)
                except SourceStop:
                    continue
            if not headers:
                raise SourceStop("SOURCE_NFI_ENGLAND_2026_SCHEMA_STOP_NO_DELIMITED_SOURCE_HEADERS")
            return {
                "source_zip_files_count": len(members),
                "source_zip_extensions_count": dict(sorted(endings.items())),
                "source_zip_total_uncompressed_bytes": sum(x.file_size for x in members),
                "source_zip_total_compressed_member_bytes": sum(x.compress_size for x in members),
                "candidate_csv_tsv_members": len(candidates),
                "candidate_csv_tsv_members_inspected_limit": MAX_DELIMITED_MEMBERS_TO_INSPECT,
                "candidate_header_valid_n": len(headers),
                "table_first_header_family_anonymous": headers,
                "source_original_archive_member_filenames_NOT_EXPORTED": True,
                "source_OTU_and_species_rows_READ": 0,
                "source_sample_ID_or_delocation_values_READ": 0,
                "source_site_geography_or_coordinates_READ": 0,
                "source_arthropod_individual_abundance_estimated": False,
                "source_layer_vs_method_CONFOUNDED": True,
                "source_NFI_pseudogeographic_delocation_not_independent_plot": True,
            }
    except zipfile.BadZipFile as exc:
        raise SourceStop("SOURCE_NFI_2026_ORIGINAL_ZIP_INVALID") from exc

def synthetic_test() -> None:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "synthetic.zip"
        with zipfile.ZipFile(p, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("data/metadata.csv",
                       "SampleID,DelocationID,ForestType,TrapType,Date,Species\n"
                       "sensitive_sample_01,confidential_plot_01,Oak,Lindgren,2024-06-01,Aaa bbb\n")
        got = inspect_zip(p)
        assert got["source_zip_files_count"] == 1
        assert got["candidate_header_valid_n"] == 1
        assert got["source_OTU_and_species_rows_READ"] == 0
        f = got["table_first_header_family_anonymous"][0]["header_has_field_family"]
        assert f["source_sample_identity_candidate"]
        assert f["delocalisation_candidate_NOT_site"]
        assert f["layer_or_trap_method_candidate"]
        assert f["tree_identity_or_forest_class_candidate"]
        assert f["taxonomic_or_otu_candidate"]
        assert "sensitive_sample_01" not in json.dumps(got)
        assert "confidential_plot_01" not in json.dumps(got)
        assert "Aaa bbb" not in json.dumps(got)
        for k in BAD_EXPORTED_FIELDS:
            assert k not in got
    print("SYNTHETIC_NFI_ZIP_HEADERS_ONLY_WITH_ZERO_BIOLOGY_PASS")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    synthetic_test()
    if args.test:
        return
    if args.out is None:
        ap.error("--out required")
    result = {
        "schema": "structural.england_nfi2026_canopy_subcanopy_original_source_gate.v1",
        "precommit": PRESPEC,
        "source_official_dataset_uuid": SOURCE_UUID,
        "original_source_package": "eDNA Woodland Canopy Subcanopy Data 2023-26.zip",
        "official_rev_date": "2026-09-08",
        "source_publisher": "UK Forestry Commission NCEA",
        "source_zip_biological_rows_READ": 0,
        "new_ecological_effect_estimated": False,
        "original_biological_data_or_original_site_ids_EXPORTED": False,
        "source_explicit_Lindgren_canopy_Malaise_subcanopy_method_confound": True,
        "previous_Finland_Carpathian_PREDICTS_Thai_NEON_BALA_GEB_scores_UNCHANGED": True,
        "eBird_used": False,
        "TinyFish_used": False,
    }
    with tempfile.TemporaryDirectory() as d:
        archive = Path(d) / "publisher_original.zip"
        try:
            n, digest, transport = retrieve_original(archive)
            result["publisher_original_archive_byte_size"] = n
            result["publisher_original_archive_sha256"] = digest
            result["publisher_transport"] = transport
            result["original_source_zip_directory_and_first_headers_ONLY"] = inspect_zip(archive)
            result["status"] = "SOURCE_NFI_ENGLAND_2026_ARCHIVE_AND_HEADERS_ONLY_PASS"
        except (SourceStop, urllib.error.URLError, TimeoutError, OSError) as exc:
            if isinstance(exc, SourceStop):
                result["status"] = str(exc)
            else:
                result["status"] = "SOURCE_NFI_ENGLAND_2026_TRANSPORT_STOP"
            result["no_site_denominator_or_biological_response_eligible"] = True
    args.out.mkdir(parents=True, exist_ok=True)
    dest = args.out / "England_NFI2026_official_archive_header_source_only.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ENGLAND_NFI2026_ORIGINAL_SOURCE_GATE", result["status"])
    print("NO_ORIGINAL_OTU_OR_PLOT_ROWS_OR_ECOLOGICAL_RESPONSE_OPENED")

if __name__ == "__main__":
    main()
