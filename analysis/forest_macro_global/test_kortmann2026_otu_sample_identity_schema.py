"""Offline sample-identity receipt and exposure regression tests."""
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
import zipfile
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import kortmann2026_otu_sample_identity_schema as gate


READY = "SOURCE_OTU_702_KEY_MATCH_690_RETAINED_READY_NO_COUNTS"
HOLD = "SOURCE_OTU_SAMPLE_LINK_HOLD"
SCHEMA_HOLD = "SOURCE_OTU_OBJECT_SCHEMA_HOLD"
OUTPUT = """KORTMANN_OTU_ID_SCHEMA_V1
OBJECT	1	matrix	21	702	0	702
METRIC	loaded_otu_object_count	1
METRIC	method_id_eligible_fields	1
METRIC	method_candidate_distinct_vectors	1
METRIC	exact_702_named_axis_matches	1
METRIC	max_unique_source_sample_label_overlap	702
METRIC	matched_39_retained_sample_keys	690
METRIC	matched_12_excluded_sample_keys	12
STATUS	SOURCE_OTU_702_KEY_MATCH_690_RETAINED_READY_NO_COUNTS
ORIGINAL_OTU_NUMERIC_CELLS_ACCESSED	0
ORIGINAL_TAXON_OR_SAMPLE_ID_EXPORTED	0
BIOLOGICAL_EFFECTS_FITTED	0
OTU_RESPONSE_OBJECT_DESERIALIZED_SCHEMA_ONLY	1
"""
METHOD = "METHOD_VALIDATED_BEFORE_OTU_LOAD\n"
START = METHOD + "OTU_LOAD_STARTED\n"
COMPLETE = START + "OTU_DESERIALIZED_SCHEMA_ONLY\n"
UNKNOWN = "ATTEMPTED_STATE_UNCONFIRMED"


class ReportTests(unittest.TestCase):
    def test_schema_hold_suppresses_retained_counts_when_another_object_is_unsupported(self):
        output = OUTPUT.replace(READY, SCHEMA_HOLD).replace("\t690\n", "\t0\n").replace("\t12\n", "\t0\n")
        output = output.replace("object_count\t1", "object_count\t2")
        output += "OBJECT\t2\tlist\t0\t0\t0\t0\n"
        self.assertEqual(gate.parse_r_output(output)["status"], SCHEMA_HOLD)
        for invalid in (
            output.replace("object_count\t2", "object_count\t1"),
            output.replace("list\t0\t0\t0\t0", "list\t2\t3\t0\t0"),
            output.replace("list\t0\t0\t0\t0", "matrix\t702\t702\t702\t0"),
        ):
            with self.subTest(), self.assertRaises(gate.SourceStop):
                gate.parse_r_output(invalid)

    def test_schema_hold_can_omit_unrepresentable_objects(self):
        output = OUTPUT.replace(READY, SCHEMA_HOLD)
        output = output.replace("OBJECT\t1\tmatrix\t21\t702\t0\t702\n", "")
        output = output.replace("matches\t1", "matches\t0").replace("overlap\t702", "overlap\t0")
        output = output.replace("keys\t690", "keys\t0").replace("keys\t12", "keys\t0")
        for loaded in (0, 1, 13):
            with self.subTest(loaded=loaded):
                result = gate.parse_r_output(output.replace("object_count\t1", f"object_count\t{loaded}"))
                self.assertEqual(result["anonymous_original_OTU_RData_object_shapes"], [])
                counts = result["source_method_to_OTU_sample_ID_overlap_COUNTS_ONLY"]
                self.assertEqual(counts["loaded_otu_object_count"], loaded)
        with self.assertRaises(gate.SourceStop):
            gate.parse_r_output(output.replace(SCHEMA_HOLD, HOLD))

    def test_preopen_failure_produces_anonymous_stop_receipt(self):
        for error, suffix in (
            (gate.SourceStop("PRIVATE_SOURCE_NAME"), "PUBLISHER_ARCHIVE_VERIFICATION_STOP"),
            (gate.SourceStop("SOURCE_PUBLISHER_HTTP_403"), "PUBLISHER_METADATA_HTTP_STOP"),
            (gate.SourceStop("SOURCE_ZIP_DOWNLOAD_TRANSPORT_TimeoutError"), "PUBLISHER_ZIP_TRANSPORT_STOP"),
            (ValueError("PRIVATE_SOURCE_NAME"), "UNEXPECTED_EXECUTION_FAILURE"),
        ):
            token = "SYNTHETIC_KORTMANN_OTU_SAMPLE_ID_ONLY_NO_COUNTS_PASS\n"
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "receipt.json"
                console = io.StringIO()
                with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, OUTPUT + token)), \
                        patch.object(gate, "original_file_metadata", side_effect=error), redirect_stdout(console):
                    code = gate.main(["--out", str(out)])
                receipt = json.loads(out.read_text())
                self.assertEqual(code, 1)
                self.assertEqual(receipt["first_semantic_OTU_RData_opening_result"], "NOT_REACHED")
                self.assertTrue(receipt["status"].endswith(suffix))
                self.assertNotIn("PRIVATE_SOURCE_NAME", out.read_text() + console.getvalue())

    def test_contradictions_and_raw_labels_blocked(self):
        for output in (
            OUTPUT.replace(READY, HOLD),
            OUTPUT.replace("METRIC\tloaded_otu_object_count\t1\n", ""),
            OUTPUT.replace("object_count\t1", "object_count\t2"),
            OUTPUT.replace("object_count\t1", "object_count\t13"),
            OUTPUT.replace("distinct_vectors\t1", "distinct_vectors\t0"),
            OUTPUT.replace("matrix\t21\t702\t0\t702", "matrix\t21\t702\t0\t0"),
            OUTPUT.replace("matrix\t21\t702\t0\t702", "matrix\t21\t702\t21\t702"),
            OUTPUT + "PRIVATE_TAXON\n",
        ):
            with self.subTest(), self.assertRaises(gate.SourceStop):
                gate.parse_r_output(output)

    def test_actual_synthetic_wire_uses_same_parser(self):
        token = "SYNTHETIC_KORTMANN_OTU_SAMPLE_ID_ONLY_NO_COUNTS_PASS\n"
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, OUTPUT + token)):
            gate.synthetic()
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, token)):
            with self.assertRaises(gate.SourceStop):
                gate.synthetic()

    def test_postload_output_failure_preserves_completed_exposure_in_saved_receipt(self):
        method = "data_public/diversity_satellite.rda"
        otu = "data_public/otu_matrix.rda"
        members = {method: b"fake method fixture", otu: b"fake matrix fixture"}
        declarations = {name: {"size": len(data), "sha": hashlib.sha256(data).hexdigest()}
                        for name, data in members.items()}
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as z:
            for name, data in members.items():
                z.writestr(name, data)
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as env:
            out = Path(tmp) / "receipt.json"
            def fake_r(args, **kwargs):
                if args[-1] == "--synthetic":
                    token = "SYNTHETIC_KORTMANN_OTU_SAMPLE_ID_ONLY_NO_COUNTS_PASS\n"
                    return subprocess.CompletedProcess(args, 0, OUTPUT + token)
                self.assertEqual(json.loads(out.read_text())[gate.OPENING], UNKNOWN)
                self.assertEqual(Path(args[-3]).read_bytes(), members[method])
                self.assertEqual(Path(args[-2]).read_bytes(), members[otu])
                Path(args[-1]).write_text(COMPLETE, encoding="ascii")
                return subprocess.CompletedProcess(args, 0, "PRIVATE_SOURCE_NAME")

            env.enter_context(patch.dict(gate.SOURCES, declarations, clear=True))
            env.enter_context(patch.object(gate, "original_file_metadata", return_value="fixture"))
            env.enter_context(patch.object(gate, "official_get_one_zip", return_value=archive.getvalue()))
            env.enter_context(patch.object(subprocess, "run", side_effect=fake_r))
            console = env.enter_context(redirect_stdout(io.StringIO()))
            self.assertEqual(gate.main(["--out", str(out)]), 1)
            receipt = json.loads(out.read_text())
            self.assertEqual(receipt[gate.OPENING], "DESERIALIZED_SCHEMA_ONLY")
            self.assertTrue(receipt["status"].endswith("R_OUTPUT_MAGIC_DRIFT"))
            self.assertNotIn("source", receipt)
            self.assertNotIn("PRIVATE_SOURCE_NAME", out.read_text() + console.getvalue())

    def test_original_errors_preserve_opening_stage(self):
        for stage, result, expected, reason in (
            ("", "oserror", UNKNOWN, "RSCRIPT_NOT_AVAILABLE"),
            (METHOD, "exit", "NOT_REACHED", "GUARD_STOP"),
            (START, "timeout", UNKNOWN, "TIMEOUT"),
            (COMPLETE, "timeout", "DESERIALIZED_SCHEMA_ONLY", "TIMEOUT"),
            (COMPLETE, "invalid stdout", "DESERIALIZED_SCHEMA_ONLY", "MAGIC_DRIFT"),
            ("PRIVATE_SOURCE_NAME\n", "success", UNKNOWN, "EXPOSURE_UNCONFIRMED"),
            ("", "success", UNKNOWN, "EXPOSURE_UNCONFIRMED"),
        ):
            with self.subTest(stage=stage, result=result), tempfile.TemporaryDirectory() as tmp:
                checkpoints = []
                def run_process(args, **kwargs):
                    self.assertEqual(checkpoints, [UNKNOWN])
                    if stage:
                        Path(args[-1]).write_text(stage, encoding="ascii")
                    if result == "timeout":
                        raise subprocess.TimeoutExpired(args, 90)
                    if result == "oserror":
                        raise FileNotFoundError("PRIVATE_SOURCE_NAME")
                    stdout = "PRIVATE_SOURCE_NAME" if result == "invalid stdout" else OUTPUT
                    return subprocess.CompletedProcess(args, int(result == "exit"), stdout)
                with patch.object(subprocess, "run", side_effect=run_process):
                    with self.assertRaisesRegex(gate.SourceStop, reason):
                        gate.run_original_r(["method", "otu"], Path(tmp) / "stage", checkpoints.append)
                self.assertEqual(checkpoints[-1], expected)


if __name__ == "__main__":
    unittest.main()
