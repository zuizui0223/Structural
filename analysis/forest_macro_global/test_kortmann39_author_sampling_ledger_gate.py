"""Offline synthetic original-method-shaped author ledger test suite.

No original source member, biological values or author site IDs are accessed.
"""
from __future__ import annotations
import csv
from datetime import date, timedelta
import io
import json
from pathlib import Path
import tempfile
import unittest

from kortmann39_author_sampling_ledger_gate import (
    COLUMNS, GateHold, codebook_from_text, ledger_rows_from_text, evaluate, main
)

ROLES = {"A": "undisturbed", "B": "disturbed_unmanaged", "C": "cleared_salvage"}
CODEBOOK = {
    "dataset_versioned_doi": "10.5281/zenodo.17775805",
    "mapping_basis": "author_provided_record_key",
    "treatment_code_to_role": ROLES,
    "offset_units_and_transform": "Synthetic original-unit description; not a real author statement.",
    "sampling_time_definition": "Synthetic collection window convention for unit testing only.",
}


def make_fixture(full=True):
    rows = []
    missing_twelve = set()
    for t, sites in (("A", range(1, 5)), ("B", range(5, 9)), ("C", range(9, 13))):
        for site in sites:
            missing_twelve.add((site, t, 6))
    for site in range(1, 41):
        for treat in ("A", "B", "C"):
            for rnd in range(1, 7):
                missing = (site == 40 and treat == "C") or (
                    (site, treat, rnd) in missing_twelve)
                if missing and not full:
                    continue
                d = date(2022, 5, 1) + timedelta(days=14*(rnd-1))
                rows.append({
                    "triplet_id": f"SYNTH_SITE_{site}",
                    "plot_id": f"SYNTH_PATCH_{treat}",
                    "treatment_code": treat,
                    "round_index": str(rnd),
                    "collection_start": d.isoformat() if not missing else "",
                    "collection_end": (d+timedelta(days=12)).isoformat() if not missing else "",
                    "trap_status": "missing" if missing else "observed",
                    "otu_column_id": "" if missing else f"SYNTH_OTU_SAMPLE_{site}_{treat}_{rnd}",
                    "method_record_id": "" if missing else f"SYNTH_AUTHOR_RECORD_{site}_{treat}_{rnd}",
                    "offset": "" if missing else "2.48490665",
                })
    return rows


def csv_text(rows):
    sio = io.StringIO()
    w = csv.DictWriter(sio, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(rows)
    return sio.getvalue()


class ResponseFreeAuthorLedgerTests(unittest.TestCase):
    def test_full_720_planned_event_source_shape_is_consistent_but_not_authenticated(self):
        x = evaluate(make_fixture(full=True), CODEBOOK)
        m=x["anonymous_counts_only"]
        self.assertEqual(x["status"], "AUTHOR_LEDGER_SHAPE_PASS_NOT_SOURCE_AUTHENTICATED")
        self.assertEqual(x["strength"], "COMPLETE_720_OPPORTUNITY_FRAME")
        self.assertEqual(m["sampled_collections"],702)
        self.assertEqual(m["declared_missing_opportunities"],18)
        self.assertEqual(m["retained_observed_collections"],690)
        self.assertEqual(m["retained_collections_per_state_sorted"],[230,230,230])
        self.assertEqual(m["retained_sampled_patches"],117)
        self.assertEqual(m["observed_patch_candidates"],119)
        self.assertEqual(m["triplet_rounds_with_overlapping_collection_dates"],
                         m["fully_observed_triplet_rounds"])
        self.assertTrue(x["original_publisher_OTU_column_IDs_NOT_INDEPENDENTLY_MATCHED"])
        self.assertNotIn("SYNTH_",json.dumps(x))
        self.assertNotIn("2022-05",json.dumps(x))

    def test_702_observed_only_is_weak_admission(self):
        x = evaluate(make_fixture(full=False),CODEBOOK)
        self.assertEqual(x["strength"],"OBSERVED_ONLY_702_NO_MISSING_EXPOSURE_LEDGER")
        self.assertEqual(x["anonymous_counts_only"]["declared_missing_opportunities"],0)

    def test_row_position_is_not_an_author_sample_identifier_even_when_permuted(self):
        rows=make_fixture()
        observed=[r for r in rows if r["trap_status"]=="observed"]
        for i,row in enumerate(observed):
            row["otu_column_id"]=str(702-i)
        with self.assertRaisesRegex(GateHold,"POSITIONAL_ROW_ORDER"):
            evaluate(rows,CODEBOOK)

    def test_repeated_sample_or_method_keys_are_rejected(self):
        for field in ("otu_column_id","method_record_id"):
            rows=make_fixture()
            actual=[r for r in rows if r["trap_status"]=="observed"]
            actual[1][field]=actual[0][field]
            with self.subTest(field=field),self.assertRaisesRegex(GateHold,"NONUNIQUE"):
                evaluate(rows,CODEBOOK)

    def test_uncollected_traps_are_never_coded_as_zero_detected_organisms(self):
        rows=make_fixture()
        unobserved=next(r for r in rows if r["trap_status"]=="missing")
        unobserved["otu_column_id"]="SYNTH_FALSE_ZERO_SAMPLE"
        with self.assertRaisesRegex(GateHold,"MISSING_TRAP"):
            evaluate(rows,CODEBOOK)

    def test_original_sampled_denominator_and_source_patch_structure_are_fixed(self):
        rows=make_fixture()
        rows.pop()
        with self.assertRaises(GateHold):
            evaluate(rows,CODEBOOK)
        rows=make_fixture()
        rows[0]["plot_id"]="SYNTH_EXTRA_PATCH"
        with self.assertRaises(GateHold):
            evaluate(rows,CODEBOOK)

    def test_no_response_or_taxon_columns_admitted(self):
        rows=make_fixture()
        text=csv_text(rows)
        self.assertEqual(len(ledger_rows_from_text(text)),720)
        with self.assertRaisesRegex(GateHold,"UNEXPECTED_OR_RESPONSE_COLUMN"):
            ledger_rows_from_text(text.replace("triplet_id,plot_id","species_count,triplet_id,plot_id",1))

    def test_offset_and_calendar_windows_require_author_codebook(self):
        bad=json.loads(json.dumps(CODEBOOK))
        bad["mapping_basis"]="row_order"
        with self.assertRaisesRegex(GateHold,"MAPPING_BASIS"):
            codebook_from_text(json.dumps(bad))
        bad=json.loads(json.dumps(CODEBOOK))
        bad["treatment_code_to_role"]["C"]="undisturbed"
        with self.assertRaisesRegex(GateHold,"CODEBOOK_TREATMENT"):
            codebook_from_text(json.dumps(bad))
        rows=make_fixture()
        rows[0]["collection_end"]="2022-01-01"
        with self.assertRaisesRegex(GateHold,"COLLECTION_DATE"):
            evaluate(rows,CODEBOOK)
        rows=make_fixture()
        rows[0]["offset"]="nan"
        with self.assertRaisesRegex(GateHold,"OFFSET_NOT_FINITE"):
            evaluate(rows,CODEBOOK)

    def test_cli_receipt_is_anonymous_and_does_not_touch_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            ledger=p/"ledger.csv"
            codebook=p/"codebook.json"
            out=p/"receipt.json"
            ledger.write_text(csv_text(make_fixture()),encoding="utf8")
            codebook.write_text(json.dumps(CODEBOOK),encoding="utf8")
            # Call via subprocess, exercising the exact parser / JSON boundary.
            import subprocess,sys
            q=subprocess.run([
                sys.executable,
                str(Path(__file__).with_name("kortmann39_author_sampling_ledger_gate.py")),
                "--ledger",str(ledger),"--codebook",str(codebook),"--out",str(out),
            ],capture_output=True,text=True,check=False,timeout=8)
            self.assertEqual(q.returncode,0,q.stderr)
            result=json.loads(out.read_text())
            self.assertEqual(result["status"],"AUTHOR_LEDGER_SHAPE_PASS_NOT_SOURCE_AUTHENTICATED")
            self.assertTrue(result["no_original_RData_or_OTU_requested"])
            self.assertEqual(result["biological_effects_fitted"],0)
            self.assertNotIn("SYNTH_",q.stdout+out.read_text())
            self.assertNotIn("2022-05",q.stdout+out.read_text())


if __name__ == "__main__":
    unittest.main()
