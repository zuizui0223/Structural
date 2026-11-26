#!/usr/bin/env python3
"""Original Weiss2016 PLOS S1 OLE DOC: private LibreOffice HTML structural tags.

Never exports HTML, MS Word text, species names or guilds. No taxonomic
crosswalk, no Gloor species/abundance opening, no ecology fitted.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from weiss2016_plos_doc_schema_only import original_doc, SourceStop

PRESPEC = "docs/FOREST_MACRO_WEISS2016_PLOS_OLE_HTML_TABLE_STRUCTURE_PRESPEC_20261118.md"
EXPECTED_ORIGINAL_SHA256 = "f5c0d5e7e9e19c45f9e6e23c40c5c8cf1ddda2f4e5b4272289a328912350c3de"


class TableShapeParser(HTMLParser):
    """Only count HTML table tags. Character data, links, attrs are ignored."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.stack = []
        self.maximum_nested_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            entry = {"row_cell_counts": [], "active_row_cell_count": None}
            self.tables.append(entry)
            self.stack.append(entry)
            self.maximum_nested_depth = max(self.maximum_nested_depth, len(self.stack))
        elif tag == "tr" and self.stack:
            current = self.stack[-1]
            if current["active_row_cell_count"] is not None:
                # Structurally malformed HTML; keep row count conservative.
                current["row_cell_counts"].append(current["active_row_cell_count"])
            current["active_row_cell_count"] = 0
        elif tag in ("td", "th") and self.stack:
            current = self.stack[-1]
            if current["active_row_cell_count"] is not None:
                current["active_row_cell_count"] += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "tr" and self.stack:
            current = self.stack[-1]
            if current["active_row_cell_count"] is not None:
                current["row_cell_counts"].append(current["active_row_cell_count"])
                current["active_row_cell_count"] = None
        elif tag == "table" and self.stack:
            current = self.stack.pop()
            if current["active_row_cell_count"] is not None:
                current["row_cell_counts"].append(current["active_row_cell_count"])
                current["active_row_cell_count"] = None

    def handle_data(self, data):
        # Important: original author specimen names, guilds and table cells
        # are intentionally never materialized or stored here.
        pass

    def summary(self):
        row_counts = [len(t["row_cell_counts"]) for t in self.tables]
        all_cells = [n for t in self.tables for n in t["row_cell_counts"]]
        cell_hist = Counter(all_cells)
        return {
            "original_HTML_table_tag_count": len(self.tables),
            "original_HTML_table_row_counts_sorted_desc": sorted(row_counts, reverse=True)[:30],
            "original_HTML_total_table_row_count": sum(row_counts),
            "original_HTML_total_table_cell_count": sum(all_cells),
            "original_HTML_maximum_table_nesting_depth": self.maximum_nested_depth,
            "original_HTML_table_row_cell_count_histogram": {
                str(i): cell_hist[i] for i in sorted(cell_hist)[:30]
            },
            "any_original_HTML_table_with_at_least_two_cells_and_100_rows":
                any(sum(v >= 2 for v in t["row_cell_counts"]) >= 100 for t in self.tables),
            "original_HTML_text_nodes_NOT_READ_OR_RETAINED": True,
            "original_species_family_guild_values_NOT_EXPORTED": True,
            "original_source_species_guild_row_pairs_NOT_RECONSTRUCTED": True,
        }


def html_structure_only(original: bytes):
    # original_doc() has already strictly checked original issuer URL digest,
    # source file byte size, SHA256 and OLE signature. Nothing else is fetched.
    libreoffice = shutil.which("libreoffice") or shutil.which("soffice")
    if not libreoffice:
        raise SourceStop("SOURCE_LIBREOFFICE_NOT_INSTALLED")
    with tempfile.TemporaryDirectory(prefix="weiss2016_LO_structure_only_") as td:
        root = Path(td)
        infile = root / "Original_Weiss2016_S1.doc"
        outfile = root / "Original_Weiss2016_S1.html"
        infile.write_bytes(original)
        try:
            converted = subprocess.run(
                [
                    libreoffice,
                    "-env:UserInstallation=" + (root / "isolated_libreoffice_profile").as_uri(),
                    "--headless",
                    "--convert-to", "html",
                    "--outdir", str(root),
                    str(infile),
                ],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=110, check=False,
            )
        except (subprocess.TimeoutExpired, OSError):
            raise SourceStop("SOURCE_LIBREOFFICE_PRIVATE_CONVERSION_FAILED") from None
        if converted.returncode != 0 or not outfile.is_file():
            raise SourceStop("SOURCE_LIBREOFFICE_PRIVATE_HTML_UNAVAILABLE")
        n = outfile.stat().st_size
        if not 100 <= n <= 20_000_000:
            raise SourceStop("SOURCE_PRIVATE_HTML_SIZE_OUTSIDE_FROZEN_LIMIT")
        try:
            doc = outfile.read_bytes().decode("utf-8", errors="replace")
            parser = TableShapeParser()
            parser.feed(doc)
            parser.close()
        except (UnicodeError, ValueError):
            raise SourceStop("SOURCE_ORIGINAL_PRIVATE_HTML_MARKUP_PARSE_STOP") from None
        summary = parser.summary()
        summary["original_privately_converted_HTML_byte_count"] = n
        summary["original_word_DOC_SHA256_preverified"] = EXPECTED_ORIGINAL_SHA256
        summary["original_source_private_HTML_NEVER_EXPORTED"] = True
        summary["publisher_original_DOC_and_html_removed_after_scope"] = True
        summary["gloor_original_taxa_or_abundance_rows_READ"] = 0
        summary["status"] = (
            "SOURCE_ORIGINAL_DOC_HTML_TABLE_ROW_STRUCTURE_PRESENT_METHOD_ONLY"
            if summary["any_original_HTML_table_with_at_least_two_cells_and_100_rows"]
            else "SOURCE_CONVERTED_DOC_TABLE_STRUCTURE_ABSENT_HOLD"
        )
    return summary


def known_truth():
    html = """<html><table><tr><th>Species</th><th>Guild</th></tr>
    <tr><td>Some rare beetle species</td><td>x</td></tr>
    <tr><td><span>Another protected taxon</span></td><td>m</td></tr></table></html>"""
    parser = TableShapeParser()
    parser.feed(html)
    q = parser.summary()
    assert q["original_HTML_table_tag_count"] == 1
    assert q["original_HTML_total_table_row_count"] == 3
    assert q["original_HTML_total_table_cell_count"] == 6
    assert q["original_HTML_table_row_cell_count_histogram"]["2"] == 3
    assert all(w not in json.dumps(q) for w in (
        "Some rare beetle species", "Another protected taxon", "Species", "Guild"
    ))
    parser2 = TableShapeParser()
    parser2.feed("<table><tr><td><table><tr><td>a</td></tr></table></td></tr></table>")
    assert parser2.summary()["original_HTML_maximum_table_nesting_depth"] == 2
    print("SYNTHETIC_WEISS2016_PRIVATE_HTML_TABLE_TAG_STRUCTURE_REDACTION_PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    known_truth()
    if args.test:
        return
    if args.out is None:
        parser.error("--out required")
    result = {
        "schema": "structural.Weiss2016_PLOS_original_OLE_private_HTML_table_structure.v1",
        "precommit": PRESPEC,
        "original_document_DOI": "10.1371/journal.pone.0149506.s001",
        "original_document_pinned_SHA256": EXPECTED_ORIGINAL_SHA256,
        "original_Weiss_data_Dryad_XLS_33652_HTTP401_not_retried": True,
        "source_original_author_species_guild_pairs_PARSED": False,
        "original_Gloor_taxa_or_abundance_READ": False,
        "original_six_guild_codes_NOT_remapped": True,
        "previous_Finland_German_PREDICTS_NEON_BALA_GEB_scoring_unchanged": True,
        "new_biodiversity_effect_estimated": False,
        "eBird_used": False, "TinyFish_used": False,
    }
    try:
        result["private_only_source_table_shape"] = html_structure_only(original_doc())
        result["status"] = result["private_only_source_table_shape"]["status"]
    except SourceStop as exc:
        result["status"] = str(exc)
        result["format_or_source_STOP_not_ecological_null"] = True
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "Weiss2016_original_PLOS_DOC_private_HTML_tables_counts_only.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("WEISS2016_PRIVATE_DOCUMENT_TABLE_STRUCTURAL_GATE", result["status"])
    print("NO_AUTHOR_GUILD_VALUES_OR_GLOOR_BIOLOGY_READ")


if __name__ == "__main__":
    main()
