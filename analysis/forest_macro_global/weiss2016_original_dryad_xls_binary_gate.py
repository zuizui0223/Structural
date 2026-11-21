#!/usr/bin/env python3
"""Weiss 2016 own Dryad original legacy .xls: ONE file-byte check only.

Only original publisher-known file ID 33652. No workbook sheet/row/taxon/guild
data opened; no Gloor Carpathian matrix accessed. Never retry alternate URLs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

from franzen425_dryad_guild_sourceonly import NoRedirect

ORIGINAL_FILE_URL = "https://datadryad.org/api/v2/files/33652/download"
ORIGINAL_FILE_ID = 33652
ORIGINAL_NAME = "FITBeetleData_CzechRepublic_2007+2008.xls"
ORIGINAL_SIZE = 232_960
ORIGINAL_MD5 = "83f740353530b8f88b05260813704eab"
OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
PRESPEC = "docs/FOREST_MACRO_WEISS2016_ORIGINAL_DRYAD_XLS_BYTE_GATE_PRESPEC_20261118.md"


class SourceStop(RuntimeError):
    pass


def attest_binary(raw: bytes):
    if len(raw) != ORIGINAL_SIZE:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_LENGTH_CHANGED")
    if hashlib.md5(raw).hexdigest() != ORIGINAL_MD5:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_MD5_CHANGED")
    if not raw.startswith(OLE_MAGIC):
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_NOT_OLE_COMPOUND_FORMAT")
    return {
        "original_publisher_file_id": ORIGINAL_FILE_ID,
        "original_published_file_name": ORIGINAL_NAME,
        "original_publisher_file_bytes": len(raw),
        "publisher_MD5_verified": ORIGINAL_MD5,
        "newly_computed_original_file_SHA256": hashlib.sha256(raw).hexdigest(),
        "format_first_eight_bytes": "OLE2_compound_document",
        "source_original_Excel_sheets_READ": 0,
        "source_original_species_trophic_guild_VALUES_READ": 0,
        "source_original_file_body_opaque_except_first8": True,
        "old_Carpathian_species_abundance_NOT_opened": True,
        "file_original_author_same_Weiss2016_study_NOT_independent_replication": True,
    }


def get_exact_original_only():
    req = urllib.request.Request(ORIGINAL_FILE_URL, headers={
        "User-Agent": "Structural-Weiss2016-author-original-Dryad-XLS-sourceonly/1.0",
        "Accept": "application/vnd.ms-excel,application/octet-stream;q=0.8",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=45) as resp:
            if resp.status != 200:
                raise SourceStop("SOURCE_ORIGINAL_WEISS_DRYAD_FILE_NOT_HTTP200")
            raw = resp.read(ORIGINAL_SIZE + 1)
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code <= 399:
            raise SourceStop("SOURCE_ORIGINAL_WEISS_DRYAD_REDIRECT_STOP") from None
        raise SourceStop("SOURCE_ORIGINAL_WEISS_DRYAD_FILE_HTTP_" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_DRYAD_FILE_TRANSPORT_" + type(exc).__name__) from None
    if len(raw) > ORIGINAL_SIZE:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_OVERSIZE_STOP")
    return attest_binary(raw)


def known_truth():
    assert ORIGINAL_FILE_URL.endswith("/api/v2/files/33652/download")
    assert ORIGINAL_SIZE == 232960
    good_fake = OLE_MAGIC + b"\0" * (ORIGINAL_SIZE - 8)
    # Deliberately not valid original MD5: correctly rejects fake OLE fixture.
    try:
        attest_binary(good_fake)
        raise AssertionError("synthetic unpinned binary was accepted")
    except SourceStop as exc:
        assert str(exc) == "SOURCE_ORIGINAL_WEISS_XLS_MD5_CHANGED"
    for alternate in (
        b"PK\x03\x04" + b"\0" * 100,
        b"%PDF" + b"\0" * 100,
        b"<html>" + b"\0" * 100,
    ):
        try:
            attest_binary(alternate)
            raise AssertionError("wrong source file shape passed")
        except SourceStop:
            pass
    assert len(OLE_MAGIC) == 8
    print("SYNTHETIC_WEISS2016_ORIGINAL_DRYAD_XLS_BYTE_MD5_OLE_GUARD_PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    known_truth()
    if args.test:
        return
    if args.out is None:
        p.error("--out required")
    output = {
        "schema": "structural.Weiss2016_Dryad_own_XLS_original_binary_transport.v1",
        "precommit": PRESPEC,
        "original_author_data_DOI": "10.5061/dryad.39k32",
        "original_publisher_file_id": ORIGINAL_FILE_ID,
        "original_source_get_max_attempts": 1,
        "original_publisher_license_CC0_confirmed_prior_metadata_run": True,
        "original_Franzen425_Dryad_HTTP401_not_retried": True,
        "original_Weiss_species_and_guild_values_read": False,
        "original_Gloor_Carpathian_taxa_or_abundances_read": False,
        "new_ecological_effect_estimated": False,
        "earlier_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_effects_unchanged": True,
        "eBird_used": False,
        "TinyFish_used": False,
    }
    try:
        output["original_source_binary_attestation_ONLY"] = get_exact_original_only()
        output["status"] = "SOURCE_ORIGINAL_WEISS_XLS_232960_MD5_OLE_VERIFIED_ONLY"
    except SourceStop as exc:
        output["status"] = str(exc)
        output["source_transport_or_integrity_stop_not_ecological_null"] = True
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "Weiss2016_Dryad_original_XLS_transport_fingerprint_only.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("WEISS2016_DRYAD_OWN_XLS_BINARY_GATE", output["status"])
    print("SOURCE_ORIGINAL_SPECIES_GUILD_ROWS_UNOPENED_GLOOR_OUTCOMES_SEALED")


if __name__ == "__main__":
    main()
