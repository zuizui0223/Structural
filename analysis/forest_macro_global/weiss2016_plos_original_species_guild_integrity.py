#!/usr/bin/env python3
"""Weiss 2016 original PLOS S1 513x9: privately validate 6-guild taxonomy.

Only original Species and Trophic guild columns are read for source integrity.
No original species names/guild mappings exported or committed. Gloor unaccessed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from weiss2016_plos_doc_schema_only import original_doc, SourceStop

PRESPEC = "docs/FOREST_MACRO_WEISS2016_S1_FIXED_AUTHOR_SPECIES_GUILD_COLUMNS_PRESPEC_20261118.md"
SOURCE_SHA = "f5c0d5e7e9e19c45f9e6e23c40c5c8cf1ddda2f4e5b4272289a328912350c3de"
EXPECTED_TABLE_ROWS = 513
EXPECTED_TABLE_COLS = 9
GUILD_CODES = set("mnpsxz")
# A binomial is only two taxonomic name words, not a claimed synonym resolution.
BINOMIAL = re.compile(
    r"^([A-Z][A-Za-z\u00c0-\u017e-]{1,49})"
    r"\s+([a-z][A-Za-z\u00c0-\u017e-]{1,49})(?=\b|$)"
)


def header_tokens(value: str):
    return set(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


class PrivateGuildTableParser(HTMLParser):
    """Captures all header texts, then ONLY the two named biological columns.

    Never stores / reads data from site abundance or other seven source columns.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.num_tables = 0
        self.in_table = False
        self.rows_seen = 0
        self.cells_this_row = 0
        self.current_cell_index = -1
        self.in_cell = False
        self.capture_cell = False
        self.parts = []
        self.header = []
        self.species_col = None
        self.guild_col = None
        self.selected_row = {}
        self.private_species_guild_rows = []
        self.any_span = False
        self.invalid_shape = False

    def handle_starttag(self, tag, attrs):
        tag = tag.casefold()
        if tag == "table":
            self.num_tables += 1
            if self.in_table:
                self.invalid_shape = True
            self.in_table = True
        elif tag == "tr" and self.in_table:
            self.cells_this_row = 0
            self.current_cell_index = -1
            self.selected_row = {}
        elif tag in ("td", "th") and self.in_table:
            for label, value in attrs:
                if label.casefold() in ("rowspan", "colspan") and str(value).strip() not in ("", "1"):
                    self.any_span = True
            self.current_cell_index += 1
            self.cells_this_row += 1
            self.in_cell = True
            self.capture_cell = (
                self.rows_seen == 0
                or self.current_cell_index in (self.species_col, self.guild_col)
            )
            self.parts = []

    def handle_data(self, data):
        if self.in_table and self.in_cell and self.capture_cell:
            self.parts.append(data)

    def handle_endtag(self, tag):
        tag = tag.casefold()
        if tag in ("td", "th") and self.in_table:
            if self.in_cell and self.capture_cell:
                val = re.sub(r"\s+", " ", " ".join(self.parts)).strip()
                if self.rows_seen == 0:
                    self.header.append(val)
                else:
                    self.selected_row[self.current_cell_index] = val
            self.in_cell = False
            self.capture_cell = False
            self.parts = []
        elif tag == "tr" and self.in_table:
            if self.cells_this_row != EXPECTED_TABLE_COLS:
                self.invalid_shape = True
            if self.rows_seen == 0:
                self._select_author_columns()
            else:
                self.private_species_guild_rows.append(
                    (self.selected_row.get(self.species_col, ""),
                     self.selected_row.get(self.guild_col, ""))
                )
            self.rows_seen += 1
        elif tag == "table" and self.in_table:
            self.in_table = False

    def _select_author_columns(self):
        if len(self.header) != EXPECTED_TABLE_COLS:
            raise SourceStop("SOURCE_ORIGINAL_AUTHOR_HEADER_NINE_CELLS_MISSING")
        # FIXED from a separately precommitted, response-unopened header-only
        # source result. Both first and ninth headers mention "species";
        # using a generic token selector would be scientifically ambiguous.
        species_header = header_tokens(self.header[0])
        guild_header = header_tokens(self.header[6])
        last_header = header_tokens(self.header[8])
        if (
            "species" not in species_header
            or not {"trophic", "guild"}.issubset(guild_header)
            or "species" not in last_header
        ):
            raise SourceStop("SOURCE_WEISS_AUTHOR_PREDECLARED_COL1_COL7_HEADER_DRIFT")
        self.species_col, self.guild_col = 0, 6

    def aggregate(self):
        if (
            self.num_tables != 1 or self.any_span or self.invalid_shape
            or self.rows_seen != EXPECTED_TABLE_ROWS
            or len(self.private_species_guild_rows) != EXPECTED_TABLE_ROWS - 1
        ):
            raise SourceStop("SOURCE_ORIGINAL_WEISS_513_BY_NINE_TABLE_SHAPE_CHANGED")
        seen = {}
        malformed_names = 0
        invalid_guild = 0
        duplicate_same = 0
        duplicate_conflicts = 0
        for raw_species, raw_code in self.private_species_guild_rows:
            match = BINOMIAL.match(raw_species.strip())
            if match is None:
                malformed_names += 1
                continue
            name = match.group(1) + " " + match.group(2)
            code = raw_code.strip().casefold()
            if code not in GUILD_CODES:
                invalid_guild += 1
                continue
            if name in seen:
                if seen[name] != code:
                    duplicate_conflicts += 1
                else:
                    duplicate_same += 1
            else:
                seen[name] = code
        if duplicate_conflicts:
            raise SourceStop("SOURCE_WEISS_ORIGINAL_DUPLICATE_SPECIES_CONFLICTING_GUILD")
        counts = Counter(seen.values())
        ledger = "".join(
            name + "\t" + seen[name] + "\n"
            for name in sorted(seen)
        ).encode("utf-8")
        return {
            "original_published_table_total_rows": self.rows_seen,
            "original_published_table_header_cols": len(self.header),
            "original_published_table_data_rows": len(self.private_species_guild_rows),
            "author_species_column_index_1based": self.species_col + 1,
            "author_trophic_guild_column_index_1based": self.guild_col + 1,
            "source_valid_unique_binomial_guild_pairs": len(seen),
            "source_missing_or_invalid_original_binomial_rows": malformed_names,
            "source_invalid_or_missing_original_sixcode_rows": invalid_guild,
            "source_duplicate_same_guild_species_rows": duplicate_same,
            "source_duplicate_conflicting_guild_species_rows": duplicate_conflicts,
            "source_valid_guild_frequency_by_original_author_code": {
                x: counts[x] for x in sorted(GUILD_CODES)
            },
            "original_unique_genera_with_valid_guild": len({
                name.split(" ", 1)[0] for name in seen
            }),
            "source_sorted_private_exact_binomial_guild_ledger_SHA256": hashlib.sha256(ledger).hexdigest(),
            "original_published_six_guild_codes_remain_uncollapsed": True,
            "original_per_species_name_code_pairs_OUTPUT": False,
            "original_other_7_source_columns_TEXT_INSPECTED": False,
            "Gloor_species_names_or_abundances_READ": False,
            "anonymous_source_ontology_status": "SOURCE_WEISS2016_ORIGINAL_SIX_GUILD_ONTOLOGY_ANONYMOUS_VALIDATED",
        }


def extract_private_author_table(raw: bytes):
    libreoffice = shutil.which("libreoffice") or shutil.which("soffice")
    if not libreoffice:
        raise SourceStop("SOURCE_LIBREOFFICE_NOT_INSTALLED")
    with tempfile.TemporaryDirectory(prefix="weiss2016_private_ontology_") as folder:
        root = Path(folder)
        original = root / "Weiss_author_S1.doc"
        private_html = root / "Weiss_author_S1.html"
        original.write_bytes(raw)
        try:
            cmd = subprocess.run(
                [
                    libreoffice,
                    "-env:UserInstallation=" + (root / "lo_profile").as_uri(),
                    "--headless", "--convert-to", "html",
                    "--outdir", str(root), str(original),
                ],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=110, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise SourceStop("SOURCE_PRIVATE_DOCUMENT_HTML_CONVERSION_FAILED") from None
        if cmd.returncode != 0 or not private_html.exists():
            raise SourceStop("SOURCE_PRIVATE_ORIGINAL_DOC_HTML_NOT_CREATED")
        if not 1_000 <= private_html.stat().st_size <= 20_000_000:
            raise SourceStop("SOURCE_PRIVATE_ORIGINAL_HTML_SIZE_CHANGED")
        try:
            parser = PrivateGuildTableParser()
            parser.feed(private_html.read_bytes().decode("utf-8", errors="replace"))
            parser.close()
            results = parser.aggregate()
        except (UnicodeError, ValueError):
            raise SourceStop("SOURCE_PRIVATE_ORIGINAL_HTML_TABLE_PARSE_FAILED") from None
    # original source temp and the private taxon/guild pairs are destroyed here.
    results["source_original_word_binary_sha256_preverified"] = SOURCE_SHA
    results["original_DOC_HTML_and_private_ledger_NOT_ARCHIVED"] = True
    return results


def known_truth():
    source = """
    <table>
      <tr><th>Species</th><th>Family</th><th>Lowland</th><th>Mountains</th>
      <th>Saproxylic</th><th>Forest status</th><th>Trophic guild</th><th>RL</th><th>Indicator species</th></tr>
      <tr><td><i>Testa speciesa</i></td><td>FamilyA</td><td>1</td><td>2</td>
      <td>1</td><td>old</td><td>x</td><td>NT</td><td>Y</td></tr>
      <tr><td>Testb speciesb</td><td>FamilyB</td><td>4</td><td>2</td>
      <td>1</td><td>young</td><td>m</td><td>LC</td><td>N</td></tr>
    </table>
    """
    p = PrivateGuildTableParser()
    # Override only synthetic table row-count requirement for parser behavioral tests.
    p.feed(source)
    assert p.num_tables == 1 and p.rows_seen == 3
    assert p.species_col == 0 and p.guild_col == 6
    assert p.private_species_guild_rows == [
        ("Testa speciesa", "x"), ("Testb speciesb", "m")
    ]
    assert all("FamilyA" not in row for row in p.private_species_guild_rows)
    assert BINOMIAL.match("Testa speciesa") is not None
    # Never export a synthetic private mapping as if observed original.
    print("SYNTHETIC_WEISS_S1_PRIVATE_SOURCE_HEADER_AND_GUILD_COLUMN_ONLY_PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    known_truth()
    if args.test:
        return
    if args.out is None:
        ap.error("--out required")
    out = {
        "schema": "structural.Weiss2016_original_PLOS_S1_six_guild_taxonomy_integrity.v1",
        "precommit": PRESPEC,
        "original_source_DOI": "10.1371/journal.pone.0149506.s001",
        "source_original_DOC_SHA256": SOURCE_SHA,
        "original_Dryad_Weiss_XLS_HTTP401_not_retried": True,
        "original_Dryad_Franzen425_HTTP401_not_retried": True,
        "original_Gloor_species_names_catches_or_guild_outcomes_READ": False,
        "previous_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_results_unchanged": True,
        "new_ecological_effect_calculated": False,
        "eBird_used": False,
        "TinyFish_used": False,
    }
    try:
        out["original_private_species_guild_integrity_summary_ONLY"] = (
            extract_private_author_table(original_doc())
        )
        out["status"] = out["original_private_species_guild_integrity_summary_ONLY"][
            "anonymous_source_ontology_status"
        ]
    except SourceStop as exc:
        out["status"] = str(exc)
        out["source_integrity_or_method_STOP_not_ecological_null"] = True
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "Weiss2016_six_guild_source_original_anonymous_integrity_only.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("WEISS2016_ORIGINAL_SIX_GUILD_SOURCE_TAXONOMY_INTEGRITY", out["status"])
    print("NO_SOURCE_SPECIES_GUILD_LABELS_OR_CARPATHIAN_OUTCOMES_EXPORTED")


if __name__ == "__main__":
    main()
