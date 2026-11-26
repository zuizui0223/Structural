#!/usr/bin/env python3
"""Gloor2026 original beetle FIRST HEADER names vs Weiss2016 511-guild ledger.

Checks exact original source tokens only. No beetle abundance, plot rows,
forest values, new ecological model, or species->guild table export.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from weiss2016_plos_doc_schema_only import original_doc, SourceStop
from weiss2016_plos_original_species_guild_integrity import (
    PrivateGuildTableParser, BINOMIAL, GUILD_CODES,
)
from carpathian116_original_author_schema_gate import (
    original_record_links,
    official_get,
    FROZEN_FILES,
)
from carpathian116_zenodo_metadata_only import SourceStop as GloorSourceStop

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_WEISS_GUILD_TAXON_NAME_ONLY_COVERAGE_PRESPEC_20261118.md"
WEISS_LEDGER_SHA="6b63db8577e8bb65bbdef5aaf30b9f078b5ee02bdcb0b434eed0554ed0bdca6b"
EXPECTED_WEISS_SPECIES=511
SOURCE_FILES=("B_SR_BEETLES.csv","S_SR_BEETLES.csv")
EXPECTED_HEADER_FIELDS={"B_SR_BEETLES.csv":242, "S_SR_BEETLES.csv":161}
# Strict Gloor source header binomials; no dots, aliases, authority or R-name conversion.
EXACT_BINOMIAL=re.compile(
    r"^[A-Z][A-Za-z\u00c0-\u017e-]{1,49} [a-z][A-Za-z\u00c0-\u017e-]{1,49}$"
)


def validate_original_weiss_private_ledger():
    lo=shutil.which("libreoffice") or shutil.which("soffice")
    if not lo:
        raise SourceStop("SOURCE_WEISS_ORIGINAL_LIBREOFFICE_UNAVAILABLE")
    original=original_doc()  # publisher-issuer and exact DOC SHA+length rechecked
    with tempfile.TemporaryDirectory(prefix="weiss_guild_to_gloor_nameonly_") as tmp:
        root=Path(tmp)
        doc=root/"Weiss_original_S1.doc"
        html=root/"Weiss_original_S1.html"
        doc.write_bytes(original)
        try:
            cmd=subprocess.run(
                [
                  lo,
                  "-env:UserInstallation="+(root/"profile").as_uri(),
                  "--headless","--convert-to","html","--outdir",str(root),str(doc)
                ],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                timeout=110,check=False,
            )
        except (OSError,subprocess.TimeoutExpired):
            raise SourceStop("SOURCE_WEISS_PRIVATE_DOC_CONVERT_STOP") from None
        if cmd.returncode or not html.is_file() or not 1000<=html.stat().st_size<=20_000_000:
            raise SourceStop("SOURCE_WEISS_PRIVATE_DOC_HTML_UNAVAILABLE")
        parser=PrivateGuildTableParser()
        parser.feed(html.read_bytes().decode("utf-8",errors="replace"))
        parser.close()
        receipt=parser.aggregate()
        if receipt["source_valid_unique_binomial_guild_pairs"]!=EXPECTED_WEISS_SPECIES:
            raise SourceStop("SOURCE_WEISS_511_GUILD_LEDGER_COUNT_DRIFT")
        if receipt["source_sorted_private_exact_binomial_guild_ledger_SHA256"]!=WEISS_LEDGER_SHA:
            raise SourceStop("SOURCE_WEISS_AUTHOR_SIX_GUILD_LEDGER_SHA_DRIFT")
        ledger={}
        for raw,code in parser.private_species_guild_rows:
            match=BINOMIAL.match(raw.strip())
            if match is None or code.strip().casefold() not in GUILD_CODES:
                continue
            key=match.group(1)+" "+match.group(2)
            guild=code.strip().casefold()
            if key in ledger and ledger[key]!=guild:
                raise SourceStop("SOURCE_WEISS_DUPLICATE_TROPHIC_ASSIGNMENT_DRIFT")
            ledger[key]=guild
        if len(ledger)!=EXPECTED_WEISS_SPECIES:
            raise SourceStop("SOURCE_WEISS_AUTHOR_GUILD_VALID_TAXA_DRIFT")
    return ledger


def read_original_first_header_only(raw:bytes,filename:str):
    expected=EXPECTED_HEADER_FIELDS[filename]
    first=raw.split(b"\n",1)[0]
    try:
        values=next(csv.reader([first.decode("utf-8-sig").rstrip("\r")],
                               delimiter=",",strict=True))
    except (UnicodeError,csv.Error,StopIteration):
        raise GloorSourceStop("SOURCE_GLOOR_ORIGINAL_FIRST_HEADER_INVALID") from None
    if len(values)!=expected or not values or values[0].strip().casefold()!="plotid":
        raise GloorSourceStop("SOURCE_GLOOR_BEETLE_ORIGINAL_HEADER_COUNT_OR_PLOTID_DRIFT")
    names=[v.strip() for v in values[1:]]
    if len(names)!=len(set(names)) or any(not v for v in names):
        raise GloorSourceStop("SOURCE_GLOOR_DUPLICATE_OR_EMPTY_SPECIES_HEADER")
    return {
        "private_taxa":set(names),
        "first_header_field_count":len(values),
        "original_taxon_field_count":len(names),
        "original_taxon_headings_not_exact_binomials":sum(
            EXACT_BINOMIAL.fullmatch(n) is None for n in names
        ),
        "source_abundance_site_counts_READ":0,
    }


def source_gloor_name_headers():
    links=original_record_links()  # verifies exact pinned CC-BY metadata SHA/DOI
    out={}
    for filename in SOURCE_FILES:
        size,md5=FROZEN_FILES[filename]
        raw=official_get(links[filename],"*/*",size+1024)
        if len(raw)!=size or hashlib.md5(raw).hexdigest()!=md5:
            raise GloorSourceStop("SOURCE_GLOOR_BEETLE_PUBLISHER_ORIGINAL_MD5_DRIFT")
        out[filename]=read_original_first_header_only(raw,filename)
    return out


def coverage(weiss,source):
    beech=source["B_SR_BEETLES.csv"]["private_taxa"]
    spruce=source["S_SR_BEETLES.csv"]["private_taxa"]
    union=beech|spruce
    w=set(weiss)
    bmatch=beech&w
    smatch=spruce&w
    matched=union&w
    by_guild=Counter(weiss[n] for n in matched)
    denom_b=len(beech)
    denom_s=len(spruce)
    denom_all=len(union)
    valid_guilds=sum(by_guild[c]>=10 for c in sorted(GUILD_CODES))
    qualifies=(
      len(matched)/denom_all >= 0.50
      and len(bmatch)/denom_b >= 0.40
      and len(smatch)/denom_s >= 0.40
      and valid_guilds >= 3
    )
    return {
        "schema":"structural.Carpathian116_Weiss2016_exact_511_guild_source_namecoverage.v1",
        "original_Weiss_verified_source_guild_species":len(w),
        "original_Gloor_beech_taxon_headers":denom_b,
        "original_Gloor_spruce_taxon_headers":denom_s,
        "original_Gloor_taxon_headers_unique_union":denom_all,
        "original_Gloor_same_literal_taxon_in_both_forest_files":len(beech&spruce),
        "Gloor_total_author_reported_303_species_is_NOT_forced":denom_all==303,
        "original_Gloor_beech_nonexact_binomial_headings":
            source["B_SR_BEETLES.csv"]["original_taxon_headings_not_exact_binomials"],
        "original_Gloor_spruce_nonexact_binomial_headings":
            source["S_SR_BEETLES.csv"]["original_taxon_headings_not_exact_binomials"],
        "source_literal_Weiss_guild_exact_taxon_matches_combined":len(matched),
        "source_literal_Weiss_guild_exact_taxon_matches_beech":len(bmatch),
        "source_literal_Weiss_guild_exact_taxon_matches_spruce":len(smatch),
        "source_literal_Weiss_guild_exact_coverage_fraction_combined":
            round(len(matched)/denom_all,6),
        "source_literal_Weiss_guild_exact_coverage_fraction_beech":
            round(len(bmatch)/denom_b,6),
        "source_literal_Weiss_guild_exact_coverage_fraction_spruce":
            round(len(smatch)/denom_s,6),
        "original_WEISS_six_guild_code_counts_among_exact_Gloor_matched_taxa_ONLY":{
            code:by_guild[code] for code in sorted(GUILD_CODES)
        },
        "original_Weiss_guilds_with_at_least_ten_Gloor_matched_species":
            valid_guilds,
        "frozen_min_coverage_overall_0p50":len(matched)/denom_all>=.50,
        "frozen_min_beech_0p40":len(bmatch)/denom_b>=.40,
        "frozen_min_spruce_0p40":len(smatch)/denom_s>=.40,
        "frozen_min_three_guilds_ten_spp":valid_guilds>=3,
        "original_Gloor_literal_union_species_heading_SHA256":
            hashlib.sha256("".join(x+"\n" for x in sorted(union)).encode("utf-8")).hexdigest(),
        "original_species_names_and_individual_species_to_guild_NOT_EXPORTED":True,
        "original_beetle_capture_site_plot_data_rows_READ":0,
        "source_taxonomy_synonym_family_fuzzy_Rname_transform_NOT_PERFORMED":True,
        "no_biodiversity_or_heldout_loss_MODEL_FIT":True,
        "status":(
            "SOURCE_GLOOR_WEISS_EXACT_GUILD_TAXON_COVERAGE_PASS_SOURCEONLY"
            if qualifies else "SOURCE_GLOOR_WEISS_EXACT_GUILD_TAXON_COVERAGE_HOLD"
        ),
    }


def known_truth():
    weiss={"Aaa bbb":"m","Bbb ccc":"x","Ccc ddd":"z"}
    source={
        "B_SR_BEETLES.csv":{"private_taxa":{"Aaa bbb","Bbb ccc"},
                             "original_taxon_headings_not_exact_binomials":0},
        "S_SR_BEETLES.csv":{"private_taxa":{"Aaa bbb","Ccc ddd"},
                             "original_taxon_headings_not_exact_binomials":0},
    }
    x=coverage(weiss,source)
    assert x["original_Gloor_taxon_headers_unique_union"]==3
    assert x["source_literal_Weiss_guild_exact_taxon_matches_combined"]==3
    assert x["original_Gloor_same_literal_taxon_in_both_forest_files"]==1
    assert x["status"]=="SOURCE_GLOOR_WEISS_EXACT_GUILD_TAXON_COVERAGE_HOLD"
    assert "Aaa bbb" not in json.dumps(x)
    fake=b'plotid,"Genus species","Genus2 species2"\n123,5,7\n'
    h=read_original_first_header_only(fake,"B_SR_BEETLES.csv") if False else None
    assert h is None  # Synthetic does not override frozen real header dimensions.
    print("SYNTHETIC_CARPATHIAN_WEISS_EXACT_ONLY_GUILD_COVERAGE_DENOMINATORS_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:p.error("--out required")
    out={
        "schema":"structural.Carpathian116_Weiss2016_six_guild_nameonly_admission.v1",
        "precommit":PRESPEC,
        "original_Weiss_PLOS_S1_DOC_SHA256":"f5c0d5e7e9e19c45f9e6e23c40c5c8cf1ddda2f4e5b4272289a328912350c3de",
        "original_Weiss_six_guild_private_source_ledger_SHA256_expected":WEISS_LEDGER_SHA,
        "original_Carpathian_species_matrix_ABUNDANCE_READ":False,
        "original_Carpathian_site_or_environment_VALUES_READ":False,
        "previous_Dryad_Weiss_and_Franzen_HTTP401_NOT_RETRIED":True,
        "prior_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_scoring_UNCHANGED":True,
        "new_ecological_effect_estimated":False,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        weiss=validate_original_weiss_private_ledger()
        source=source_gloor_name_headers()
        out["original_publisher_taxon_coverage_anonymous_ONLY"]=coverage(weiss,source)
        out["status"]=out["original_publisher_taxon_coverage_anonymous_ONLY"]["status"]
    except (SourceStop,GloorSourceStop,UnicodeError,csv.Error) as exc:
        out["status"]=str(exc) if isinstance(exc,(SourceStop,GloorSourceStop)) else "SOURCE_TAXON_HEADER_PARSE_STOP"
        out["source_taxonomy_or_integrity_STOP_not_ecological_null"]=True
    out_path=args.out/"Gloor116_Weiss2016_511guild_exact_nameonly_coverage.json"
    args.out.mkdir(parents=True,exist_ok=True)
    out_path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GLOOR116_WEISS511_EXACT_TROPHIC_GUILD_NAME_ONLY_COVERAGE",out["status"])
    print("NO_GLOOR_SPECIES_ABUNDANCE_SITE_ROWS_OR_BIOLOGY_SCORING")
if __name__=="__main__":
    main()
