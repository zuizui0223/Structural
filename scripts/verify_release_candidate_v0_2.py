#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "build/structural_submission_v2"
PREFLIGHT = ROOT / "manuscript/submission/release_preflight_v0_1_0.json"
AUTHOR_METADATA = ROOT / "manuscript/submission/author_metadata.template.json"
SUBMISSION_MANIFEST = ROOT / "manuscript/submission/submission_manifest.json"
AVAILABILITY = ROOT / "manuscript/submission/data_code_availability.md"


class ReleaseCandidateError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseCandidateError(f"cannot read JSON {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseCandidateError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseCandidateError("cannot resolve git HEAD") from exc


def _package_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if match is None:
        raise ReleaseCandidateError("cannot resolve package version from pyproject.toml")
    return match.group(1)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contains_placeholder(value: object) -> bool:
    if isinstance(value, str):
        return "<" in value and ">" in value
    if isinstance(value, list):
        return any(_contains_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_placeholder(item) for item in value.values())
    return False


def _human_policy_blockers(metadata: dict) -> list[str]:
    blockers: list[str] = []

    if _contains_placeholder(metadata.get("authors")):
        blockers.append("author_list_or_roles_incomplete")
    if _contains_placeholder(metadata.get("affiliations")):
        blockers.append("affiliations_incomplete")
    if _contains_placeholder(metadata.get("corresponding_author")):
        blockers.append("corresponding_author_incomplete")
    if _contains_placeholder(metadata.get("funding")):
        blockers.append("funding_statement_incomplete")

    competing = metadata.get("competing_interests", {})
    if competing.get("confirmed_by_all_authors") is not True:
        blockers.append("competing_interests_not_approved")
    if _contains_placeholder(competing.get("statement")):
        blockers.append("competing_interests_statement_incomplete")

    ethics = metadata.get("ethics_and_permits", {})
    if ethics.get("review_completed") is not True:
        blockers.append("ethics_permit_review_incomplete")
    if _contains_placeholder(ethics.get("statement")):
        blockers.append("ethics_permit_statement_incomplete")

    originality = metadata.get("originality_and_submission", {})
    if originality.get("approved_by_all_authors") is not True:
        blockers.append("originality_submission_not_approved")
    if originality.get("not_published_previously_confirmed") is not True:
        blockers.append("prior_publication_not_confirmed")
    if originality.get("not_under_consideration_elsewhere_confirmed") is not True:
        blockers.append("simultaneous_submission_not_confirmed")

    ai = metadata.get("generative_ai_disclosure", {})
    if ai.get("reviewed_by_all_authors") is not True:
        blockers.append("generative_ai_disclosure_not_approved")
    if ai.get("journal_specific_guide_checked") is not True:
        blockers.append("journal_specific_guide_not_checked")
    if ai.get("live_journal_policy_checked") is not True:
        blockers.append("live_journal_policy_gate_not_cleared")
    if _contains_placeholder(ai.get("final_statement")):
        blockers.append("generative_ai_statement_incomplete")

    release = metadata.get("release_metadata", {})
    if release.get("creator_order_confirmed") is not True:
        blockers.append("creator_order_not_confirmed")
    if release.get("software_citation_metadata_approved") is not True:
        blockers.append("software_citation_metadata_not_approved")

    return blockers


def _identifier_state(preflight: dict) -> tuple[bool, list[str]]:
    text = AVAILABILITY.read_text(encoding="utf-8")
    unresolved = [
        token
        for token in preflight.get(
            "identifier_placeholders_must_remain_until_release_gate_clears", []
        )
        if isinstance(token, str) and token in text
    ]
    return (not unresolved, unresolved)


def _validate_package(
    package_dir: Path,
    *,
    head: str,
    submission_manifest: dict,
) -> dict[str, object]:
    manifest_path = package_dir / "submission_package_manifest_v2.json"
    if not manifest_path.is_file():
        raise ReleaseCandidateError(
            f"missing submission package manifest: {manifest_path}"
        )
    package = _load(manifest_path)

    if package.get("source_commit") != head:
        raise ReleaseCandidateError(
            "submission package source_commit does not equal git HEAD"
        )
    if package.get("eog_wf_empirical_denominator_included") is not False:
        raise ReleaseCandidateError(
            "submission package must exclude EOG-WF empirical denominator"
        )

    frozen = submission_manifest.get("frozen_evidence", {})
    if (
        package.get("aislands_strong_reference_result_fingerprint")
        != frozen.get("aislands_strong_reference_result_fingerprint")
    ):
        raise ReleaseCandidateError("A-Islands fingerprint mismatch in package")
    if (
        package.get("tanzania_result_fingerprint")
        != frozen.get("tanzania_result_fingerprint")
    ):
        raise ReleaseCandidateError("Tanzania fingerprint mismatch in package")

    canonical = package.get("canonical_submission_figures")
    if not isinstance(canonical, dict) or not canonical:
        raise ReleaseCandidateError("canonical submission figures missing from package")
    for label, relative in canonical.items():
        if not isinstance(relative, str) or not (package_dir / relative).is_file():
            raise ReleaseCandidateError(f"missing packaged canonical figure: {label}")

    return {
        "manifest_path": str(manifest_path.relative_to(ROOT)),
        "manifest_sha256": _sha256(manifest_path),
        "source_commit": package["source_commit"],
        "file_count": len(package.get("files", {})),
    }


def evaluate(package_dir: Path | None) -> dict[str, object]:
    preflight = _load(PREFLIGHT)
    metadata = _load(AUTHOR_METADATA)
    submission = _load(SUBMISSION_MANIFEST)

    version = _package_version()
    candidate_tag = f"v{version}"
    if preflight.get("package_version") != version:
        raise ReleaseCandidateError("preflight package version mismatch")
    if preflight.get("candidate_tag") != candidate_tag:
        raise ReleaseCandidateError("preflight candidate tag mismatch")
    if preflight.get("science_frozen") is not True:
        raise ReleaseCandidateError("science must remain frozen")
    if preflight.get("presentation_frozen") is not True:
        raise ReleaseCandidateError("presentation must remain frozen")

    head = _git_head()
    human_blockers = _human_policy_blockers(metadata)
    identifiers_resolved, unresolved_identifiers = _identifier_state(preflight)

    if human_blockers:
        stage = "HOLD_HUMAN_POLICY_GATES"
    elif not identifiers_resolved:
        stage = "READY_FOR_IDENTIFIER_RESERVATION_AND_IDENTIFIER_ONLY_PR"
    else:
        stage = "READY_FOR_RELEASE_CANDIDATE_RECEIPT"

    package_receipt = None
    if package_dir is not None:
        package_receipt = _validate_package(
            package_dir.resolve(),
            head=head,
            submission_manifest=submission,
        )

    return {
        "schema": "structural.release_candidate_verifier.v0_2",
        "stage": stage,
        "git_head": head,
        "package_version": version,
        "candidate_tag": candidate_tag,
        "human_policy_blockers": human_blockers,
        "unresolved_identifier_placeholders": unresolved_identifiers,
        "package_verified": package_receipt is not None,
        "package": package_receipt,
        "release_actions_authorized": False,
        "scientific_state_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=DEFAULT_PACKAGE,
        help="Built submission package directory to verify.",
    )
    parser.add_argument(
        "--allow-hold",
        action="store_true",
        help="Exit zero when verification is internally consistent but human/policy gates still hold.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        receipt = evaluate(args.package_dir)
    except ReleaseCandidateError as exc:
        print(f"release candidate verification failed: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")

    if receipt["stage"] == "HOLD_HUMAN_POLICY_GATES" and not args.allow_hold:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
