#!/usr/bin/env python3
"""BETA-FOR11 original publisher METADATA only; no site, treatment or OTU rows.

Precommitted protocol: docs/FOREST_MACRO_BETAFOR11_2025_ORIGINAL_METHOD_PREINTAKE_PRESPEC_20261119.md
"""
from __future__ import annotations
import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://zenodo.org/api/records/15371332"
RECORD = 15371332
DOI = "10.5281/zenodo.15371332"
FILES = {
    "BETAFOR_information.csv": "873f5d424904d1eed00e079b945dd5dc",
    "calibration_points.csv": "6c9a9dedc5ec0958ae4964b30a7b0433",
    "com_singletons.csv": "81e2c1269bff49fafdf497f03f5922b2",
    "insects_rainford_adapted.tre": "491b4d81ec65e94a1b6213bf92959ef5",
    "OTUArtenlisteGesamt.csv": "517999cb19112a261e73aed8c2e42282",
    "otus_new.fasta": "307730de9089bef66855e13162cbceed",
}

class SourceStop(Exception):
    pass


def parse_publisher_only(doc):
    if not isinstance(doc, dict):
        raise SourceStop("PUBLISHER_METADATA_NOT_OBJECT")
    md = doc.get("metadata", {})
    if not isinstance(md, dict):
        raise SourceStop("PUBLISHER_METADATA_MISSING")
    if doc.get("id") != RECORD or doc.get("doi", md.get("doi")) != DOI:
        raise SourceStop("PUBLISHER_RECORD_OR_DOI_DRIFT")
    if doc.get("status") not in ("published",):  # fail closed
        raise SourceStop("PUBLISHER_PUBLICATION_STATUS_DRIFT")
    license_meta = md.get("license", {})
    lid = license_meta.get("id", "") if isinstance(license_meta, dict) else license_meta
    if not isinstance(lid, str) or lid.casefold() != "cc-by-sa-4.0":
        raise SourceStop("PUBLISHER_LICENSE_DRIFT")
    version = md.get("version")
    if version != "v1":
        raise SourceStop("PUBLISHER_VERSION_NOT_V1")
    entries = doc.get("files")
    if not isinstance(entries, list) or len(entries) != len(FILES):
        raise SourceStop("PUBLISHER_FILE_COUNT_DRIFT")
    seen = {}
    for f in entries:
        if not isinstance(f, dict):
            raise SourceStop("PUBLISHER_FILE_DESCRIPTOR_INVALID")
        key, chk, size = f.get("key"), f.get("checksum"), f.get("size")
        if key not in FILES or key in seen:
            raise SourceStop("PUBLISHER_FILENAME_ADDED_OR_DUPLICATE")
        if chk != "md5:" + FILES[key] or type(size) is not int or size <= 0:
            raise SourceStop("PUBLISHER_MD5_OR_LENGTH_DRIFT")
        seen[key] = int(size)
    if set(seen) != set(FILES):
        raise SourceStop("PUBLISHER_FILE_SET_DRIFT")
    return {
        "status": "ORIGINAL_PUBLISHER_SIX_FILE_METADATA_ONLY_PASS",
        "record_id": RECORD,
        "doi": DOI,
        "publisher_version": version,
        "license": lid,
        "file_count": len(seen),
        "publisher_reported_original_files": [
            {"filename": key, "published_md5": FILES[key],
             "publisher_reported_bytes": seen[key]}
            for key in sorted(seen)
        ],
        "no_original_files_downloaded": True,
        "no_original_headers_or_sample_IDs_read": True,
        "no_original_site_or_treatment_rows_read": True,
        "no_original_OTU_abundance_or_sequence_read": True,
        "new_biological_effects_estimated": 0,
        "scientific_eligibility_held_pending_source_method_crosswalk": True,
    }


def get_official_metadata_only():
    req = urllib.request.Request(
        URL, headers={"Accept": "application/json",
                      "User-Agent": "Structural-BETAFOR11-Original-Publisher-Index-Only/1.0"},
    )
    # No redirects to non-official file host, no download of any original source member.
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            if response.status != 200 or response.url != URL:
                raise SourceStop("PUBLISHER_METADATA_NON200_OR_REDIRECT")
            data = response.read(1024 * 1024 + 1)
    except urllib.error.HTTPError as e:
        raise SourceStop("PUBLISHER_METADATA_HTTP_" + str(e.code)) from None
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise SourceStop("PUBLISHER_METADATA_TRANSPORT_" + type(e).__name__) from None
    if len(data) > 1024*1024:
        raise SourceStop("PUBLISHER_METADATA_TOO_LARGE")
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise SourceStop("PUBLISHER_METADATA_INVALID_JSON") from None


def synthetic_tests():
    fake = {
        "id": RECORD, "doi": DOI, "status": "published",
        "metadata": {"doi": DOI, "license": {"id": "cc-by-sa-4.0"}, "version": "v1"},
        "files": [{"key": k, "checksum": "md5:" + v, "size": 1024}
                  for k, v in FILES.items()],
    }
    assert parse_publisher_only(fake)["file_count"] == 6
    for changed in (
        lambda d: d.update(doi="10.5281/zenodo.1"),
        lambda d: d["metadata"].update(version="v2"),
        lambda d: d["metadata"].update(license={"id": "all-rights-reserved"}),
        lambda d: d["files"][0].update(checksum="md5:"+"0"*32),
        lambda d: d["files"].pop(),
    ):
        obj = json.loads(json.dumps(fake))
        changed(obj)
        try:
            parse_publisher_only(obj)
        except SourceStop:
            pass
        else:
            raise AssertionError("A changed original source metadata passed")
    print("SYNTHETIC_BETAFOR11_ORIGINAL_PUBLISHER_METADATA_FIREWALL_PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    synthetic_tests()
    if args.test:
        return
    if args.out is None:
        p.error("--out required")
    obj = {
        "schema": "structural.BETAFOR11_original_zenodo_publisher_metadata_preintake.v1",
        "record_requested": URL,
        "protocol": "docs/FOREST_MACRO_BETAFOR11_2025_ORIGINAL_METHOD_PREINTAKE_PRESPEC_20261119.md",
        "source_original_data_members_GET": 0,
        "original_organism_or_site_rows_read": 0,
        "new_field_effects_tested": 0,
        "no_prior_outcomes_reopened": True,
        "not_a_biological_null_if_halted": True,
    }
    try:
        obj["publisher"] = parse_publisher_only(get_official_metadata_only())
        obj["status"] = obj["publisher"]["status"]
    except SourceStop as e:
        obj["status"] = "SOURCE_METADATA_HOLD_" + str(e)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("BETAFOR11_METADATA_ONLY", obj["status"])
    print("ZERO_BIOLOGICAL_ROWS; ZERO_ORIGINAL_DATA_MEMBER_GET; NO_EFFECT")


if __name__ == "__main__":
    main()
