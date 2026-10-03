#!/usr/bin/env python3
"""Build a review-only anonymized reproducibility bundle from frozen artifacts.

This tool never accesses a biological response source. It neutralizes public-
repository-specific code/provenance identifiers while preserving scientific
logic, frozen numeric payloads, and stable data-source DOIs.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

ORIGINAL_MAGIC = b"STRUCTURAL_MAMMAL_PRED_V1\n"
REVIEW_MAGIC = b"REVIEW_MAMMAL_PRED_V1\n"

DROP_JSON_KEYS = {
    "source_execution", "workflow_run_id", "workflow_head_sha", "workflow_job_id",
    "artifact_id", "artifact_name", "artifact_digest", "expires_at",
    "pull_request", "parent_main_commit", "repository", "repository_id",
    "head_repository_id", "head_branch", "active_priority",
}
DROP_JSON_KEYS_PREFIX = ("github_",)
COMMIT_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")
VERSION_TOKEN_RE = re.compile(r"v\d+[_\.]\d+(?:[_\.]\d+)?")

SCRIPT_MAP = {
    "scripts/freeze_global_mammals_exploratory_preconfirmatory_v1_72.py": "analysis/01_fit_predict.py",
    "scripts/score_global_mammals_exploratory_v1_74.py": "analysis/02_score_heldout.py",
    "scripts/run_global_mammals_exploratory_diagnostics_v1_77.py": "analysis/03_geographic_diagnostics.py",
    "scripts/run_global_mammals_species_breadth_diagnostics_v1_81.py": "analysis/04_species_breadth.py",
    "scripts/run_global_mammals_prediction_behavior_v1_84.py": "analysis/05_prediction_behavior.py",
    "scripts/audit_global_mammals_isolation_empty_support_v1_87.py": "analysis/06_isolation_empty_support.py",
    "scripts/build_macro_figures_v1_83.py": "analysis/07_main_figures.py",
    "scripts/build_prediction_behavior_figure_v1_86.py": "analysis/08_prediction_behavior_figure.py",
}

CONTRACT_MAP = {
    "development/global_mammals_macro_model_contract_v1_67.json": "contracts/model.json",
    "development/global_mammals_exploratory_preconfirmatory_contract_v1_72.json": "contracts/preconfirmatory.json",
    "development/global_mammals_exploratory_scoring_contract_v1_74.json": "contracts/scoring.json",
    "development/macro_source_feature_empty_support_contract_v1_56.json": "contracts/empty_source.json",
    "development/global_mammals_exploratory_diagnostics_contract_v1_77.json": "contracts/geographic_diagnostics.json",
    "development/global_mammals_species_breadth_diagnostics_contract_v1_81.json": "contracts/species_breadth.json",
    "development/global_mammals_prediction_behavior_contract_v1_84.json": "contracts/prediction_behavior.json",
    "development/global_mammals_isolation_empty_support_audit_contract_v1_87.json": "contracts/isolation_empty_support.json",
}

RESULT_JSON_MAP = {
    "heldout_score/exploratory_result.json": "results/primary_result.json",
    "geographic_diagnostics/diagnostics_result.json": "results/geographic_diagnostics.json",
    "species_breadth/species_breadth_result.json": "results/species_breadth.json",
    "prediction_behavior/prediction_behavior_result.json": "results/prediction_behavior.json",
    "isolation_empty_support/isolation_empty_support_result.json": "results/isolation_empty_support.json",
    "pilot/exploratory_pilot_receipt.json": "results/pilot_receipt.json",
    "reference/reference_receipt.json": "results/reference_receipt.json",
    "routing/routing_receipt.json": "results/routing_receipt.json",
    "preconfirmatory/model_receipt.json": "results/model_receipt.json",
    "heldout_score/exploratory_confirmatory_response_receipt.json": "results/heldout_response_receipt.json",
}

CSV_BINARY_MAP = {
    "pilot/exploratory_pilot_species_universe.csv": "inputs/pilot_species_universe.csv",
    "pilot/exploratory_pilot_matrix.csv": "inputs/pilot_matrix.csv",
    "reference/state_reference.csv": "inputs/state_reference.csv",
    "reference/source_graph_edges.csv": "inputs/source_graph_edges.csv",
    "safe/appendix2_safe_rows.csv": "inputs/response_independent_island_metadata.csv",
    "routing/pilot_ids.csv": "inputs/pilot_routing.csv",
    "routing/confirmatory_ids.csv": "inputs/heldout_routing.csv",
    "preconfirmatory/confirmatory_entity_order.csv": "outputs/heldout_entity_order.csv",
    "heldout_score/exploratory_confirmatory_matrix.csv": "outputs/heldout_focal_response_matrix.csv",
    "heldout_score/block_scores.csv": "outputs/primary_block_scores.csv",
    "geographic_diagnostics/block_context.csv": "outputs/block_context.csv",
    "geographic_diagnostics/bioregion_summary.csv": "outputs/bioregion_summary.csv",
    "species_breadth/species_effects.csv": "outputs/species_effects.csv",
    "species_breadth/breadth_quartiles.csv": "outputs/species_breadth_groups.csv",
    "prediction_behavior/block_prediction_behavior.csv": "outputs/block_prediction_behavior.csv",
}

FIGURE_MAP = {
    "figures/main/fig1_bioregion_effects.png": "figures/Figure_1.png",
    "figures/main/fig1_bioregion_effects.svg": "figures/Figure_1.svg",
    "figures/main/fig2_external_isolation_attenuation.png": "figures/Figure_2.png",
    "figures/main/fig2_external_isolation_attenuation.svg": "figures/Figure_2.svg",
    "figures/main/fig3_species_breadth_attenuation.png": "figures/Figure_3.png",
    "figures/main/fig3_species_breadth_attenuation.svg": "figures/Figure_3.svg",
    "figures/main/figS1_gift_endpoint_attrition.png": "figures/Figure_S1.png",
    "figures/main/figS1_gift_endpoint_attrition.svg": "figures/Figure_S1.svg",
    "figures/prediction_behavior/figS2_prediction_behavior.png": "figures/Figure_S2.png",
    "figures/prediction_behavior/figS2_prediction_behavior.svg": "figures/Figure_S2.svg",
}

PATH_REPLACEMENTS = {
    "development/global_mammals_macro_model_contract_v1_67.json": "contracts/model.json",
    "development/global_mammals_exploratory_preconfirmatory_contract_v1_72.json": "contracts/preconfirmatory.json",
    "development/global_mammals_exploratory_scoring_contract_v1_74.json": "contracts/scoring.json",
    "development/macro_source_feature_empty_support_contract_v1_56.json": "contracts/empty_source.json",
    "development/global_mammals_exploratory_diagnostics_contract_v1_77.json": "contracts/geographic_diagnostics.json",
    "development/global_mammals_species_breadth_diagnostics_contract_v1_81.json": "contracts/species_breadth.json",
    "development/global_mammals_prediction_behavior_contract_v1_84.json": "contracts/prediction_behavior.json",
    "development/global_mammals_isolation_empty_support_audit_contract_v1_87.json": "contracts/isolation_empty_support.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def clean_string(value: str, prediction_sha_old: str | None = None, prediction_sha_new: str | None = None) -> str:
    s = value
    for old, new in PATH_REPLACEMENTS.items():
        s = s.replace(old, new)
    s = s.replace("structural.", "review.")
    s = s.replace("global_island_native_mammals_barreto_2024", "global_island_mammals")
    s = s.replace("global_mammals_", "island_mammal_")
    s = s.replace("separate_nonconfirmatory_exploratory_macro_lineage", "nonconfirmatory_exploratory_macro")
    s = s.replace("STRUCTURAL_MAMMAL_PRED_V1", "REVIEW_MAMMAL_PRED_V1")
    s = s.replace("zuizui0223", "anonymous")
    s = re.sub(r"https?://github\.com/[^\s\"']+", "<public-development-url-redacted>", s)
    s = re.sub(r"\.github/workflows/[^\s\"']+", "<workflow-redacted>", s)
    s = COMMIT_RE.sub("<commit-redacted>", s)
    s = VERSION_TOKEN_RE.sub("review", s)
    if prediction_sha_old and prediction_sha_new:
        s = s.replace(prediction_sha_old, prediction_sha_new)
    return s


def sanitize_json_value(obj, prediction_sha_old: str | None = None, prediction_sha_new: str | None = None):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in DROP_JSON_KEYS or any(k.startswith(p) for p in DROP_JSON_KEYS_PREFIX):
                continue
            if k == "parents":
                continue
            out[clean_string(str(k), prediction_sha_old, prediction_sha_new)] = sanitize_json_value(
                v, prediction_sha_old, prediction_sha_new
            )
        return out
    if isinstance(obj, list):
        return [sanitize_json_value(v, prediction_sha_old, prediction_sha_new) for v in obj]
    if isinstance(obj, str):
        return clean_string(obj, prediction_sha_old, prediction_sha_new)
    return obj


class NeutralizePython(ast.NodeTransformer):
    def __init__(self, prediction_sha_old: str | None, prediction_sha_new: str | None):
        self.prediction_sha_old = prediction_sha_old
        self.prediction_sha_new = prediction_sha_new

    @staticmethod
    def _strip_docstring(node):
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            node.body = body[1:]

    def visit_Module(self, node):
        self._strip_docstring(node)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        self._strip_docstring(node)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        self._strip_docstring(node)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        self._strip_docstring(node)
        self.generic_visit(node)
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            return ast.copy_location(
                ast.Constant(clean_string(node.value, self.prediction_sha_old, self.prediction_sha_new)),
                node,
            )
        if isinstance(node.value, bytes) and node.value == ORIGINAL_MAGIC:
            return ast.copy_location(ast.Constant(REVIEW_MAGIC), node)
        return node


def neutralize_python(src: Path, dst: Path, prediction_sha_old: str | None, prediction_sha_new: str | None):
    tree = ast.parse(src.read_text(encoding="utf-8"))
    tree = NeutralizePython(prediction_sha_old, prediction_sha_new).visit(tree)
    ast.fix_missing_locations(tree)
    text = "# Review-only neutralized source snapshot\n" + ast.unparse(tree) + "\n"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def copy_sanitized_json(src: Path, dst: Path, prediction_sha_old: str | None, prediction_sha_new: str | None):
    data = json.loads(src.read_text(encoding="utf-8"))
    data = sanitize_json_value(data, prediction_sha_old, prediction_sha_new)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    repo = args.repo_root.resolve()
    source = args.source_root.resolve()
    out = args.output_dir.resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    original_pred = source / "preconfirmatory" / "confirmatory_predictions.f64le"
    raw = original_pred.read_bytes()
    if not raw.startswith(ORIGINAL_MAGIC):
        raise SystemExit("prediction binary magic drift")
    neutral_raw = REVIEW_MAGIC + raw[len(ORIGINAL_MAGIC):]
    pred_dst = out / "outputs" / "heldout_predictions.f64le"
    pred_dst.parent.mkdir(parents=True, exist_ok=True)
    pred_dst.write_bytes(neutral_raw)
    old_pred_sha = sha256(original_pred)
    new_pred_sha = sha256(pred_dst)

    # Neutralized contracts.
    for src_rel, dst_rel in CONTRACT_MAP.items():
        copy_sanitized_json(repo / src_rel, out / dst_rel, old_pred_sha, new_pred_sha)

    # Neutralized analysis code.
    for src_rel, dst_rel in SCRIPT_MAP.items():
        neutralize_python(repo / src_rel, out / dst_rel, old_pred_sha, new_pred_sha)

    # Frozen result receipts/summaries.
    for src_rel, dst_rel in RESULT_JSON_MAP.items():
        copy_sanitized_json(source / src_rel, out / dst_rel, old_pred_sha, new_pred_sha)

    # CSV and binary support, excluding raw source response.
    for src_rel, dst_rel in CSV_BINARY_MAP.items():
        src = source / src_rel
        dst = out / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # Figures.
    for src_rel, dst_rel in FIGURE_MAP.items():
        src = source / src_rel
        dst = out / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # Figure captions only; no public-repository references.
    captions = (repo / "manuscript/submission/macro_v1_89/figure_captions.md").read_text(encoding="utf-8")
    captions = clean_string(captions, old_pred_sha, new_pred_sha)
    (out / "FIGURE_CAPTIONS.md").write_text(captions, encoding="utf-8")

    readme = f"""# Anonymous peer-review reproducibility bundle

This review-only bundle contains the frozen inputs, prediction surface, held-out focal response matrix, diagnostics and figures supporting a blinded macroecology manuscript.

## Evidence status

The global mammal analysis is explicitly **nonconfirmatory exploratory**. The bundle preserves the frozen analysis population, species universe, reference hierarchy and held-out scoring surface; it does not authorize redefinition of the primary analysis.

## Data sources

Raw biological response bytes are **not redistributed** in this bundle.

- Global island mammal source: Dryad DOI 10.5061/dryad.hmgqnk9j2, version 6.
- Response-independent island reference geography: DOI 10.21942/uva.22788464.v5.
- Plant context: GIFT database version 3.2.

The included `inputs/pilot_matrix.csv` and `outputs/heldout_focal_response_matrix.csv` are the frozen focal analysis surfaces needed to reproduce the reported analysis without reopening the raw source file.

## Review-neutralized code

Python files under `analysis/` are mechanically neutralized review copies: comments/docstrings and public-development identifiers were removed, filenames were generalized, and the binary prediction magic label was replaced by an equivalently sized review label. Numerical prediction payloads are unchanged.

Original prediction SHA-256: {old_pred_sha}
Review prediction SHA-256: {new_pred_sha}

The scientific algorithms, model definitions, numerical constants and frozen result values are unchanged.

## Environment

Core reproduction environment:

- Python 3.11
- NumPy 2.3.3 for the model/prediction freeze
- Matplotlib 3.8+ for figures

Use `python analysis/<script>.py --help` for script-specific interfaces.

## Bundle integrity

`SHA256SUMS.txt` records every included file. The bundle contains no raw Dryad response file, GitHub workflow identifiers, public repository URL, author names, affiliations, funding information or acknowledgements.
"""
    (out / "README.md").write_text(readme, encoding="utf-8")

    provenance = {
        "schema": "review.anonymous_bundle_provenance",
        "status": "review_neutralized_frozen_outputs",
        "data_source_dois": ["10.5061/dryad.hmgqnk9j2", "10.21942/uva.22788464.v5"],
        "population_islands": 5401,
        "pilot_islands": 1275,
        "heldout_islands": 4126,
        "focal_species": 79,
        "heldout_blocks": 168,
        "original_prediction_payload_sha256": hashlib.sha256(raw[len(ORIGINAL_MAGIC):]).hexdigest(),
        "review_prediction_payload_sha256": hashlib.sha256(neutral_raw[len(REVIEW_MAGIC):]).hexdigest(),
        "payloads_identical": raw[len(ORIGINAL_MAGIC):] == neutral_raw[len(REVIEW_MAGIC):],
        "raw_biological_response_included": False,
        "public_repository_identifiers_included": False,
    }
    (out / "ANONYMIZED_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # Reject direct or indirect public-repository identifiers in text.
    forbidden_literals = [
        "github.com", "zuizui0223", "workflow_run_id", "workflow_head_sha",
        "workflow_job_id", "artifact_id", "artifact_name", ".github/workflows",
        "structural.", "global_mammals_", "global_island_native_mammals_barreto_2024",
    ]
    text_suffixes = {".md", ".txt", ".json", ".py", ".csv", ".svg"}
    problems = []
    for path in out.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        low = text.casefold()
        for lit in forbidden_literals:
            if lit.casefold() in low:
                problems.append((str(path.relative_to(out)), lit))
        if COMMIT_RE.search(text):
            problems.append((str(path.relative_to(out)), "40-hex-commit-like-token"))
    if problems:
        raise SystemExit(f"review anonymization failure: {problems[:30]}")

    # File checksums.
    files = sorted(p for p in out.rglob("*") if p.is_file())
    with (out / "SHA256SUMS.txt").open("w", encoding="utf-8") as h:
        for p in files:
            h.write(f"{sha256(p)}  {p.relative_to(out).as_posix()}\n")

    result = {
        "schema": "review.anonymous_bundle_build_result",
        "status": "ANONYMIZED_REVIEW_BUNDLE_READY",
        "file_count": len(files) + 1,
        "prediction_payload_identical": provenance["payloads_identical"],
        "raw_biological_response_included": False,
        "public_repository_identifiers_included": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
