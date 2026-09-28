"""Column-level firewall for mixed predictor/response CSV files."""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import json
from pathlib import Path


class MixedCSVFirewallError(RuntimeError):
    pass


@dataclass(frozen=True)
class MixedCSVColumnManifest:
    file_sha256: str
    header_sha256: str
    safe_pre_response_columns: tuple[str, ...]
    protected_response_columns: tuple[str, ...]


@dataclass(frozen=True)
class MixedCSVHeaderAudit:
    header: tuple[str, ...]
    safe_pre_response_columns: tuple[str, ...]
    protected_response_columns: tuple[str, ...]
    closed_unclassified_columns: tuple[str, ...]


@dataclass(frozen=True)
class MixedCSVHeaderFreezeAudit:
    """Header-only candidate used before any row-level semantic access."""

    file_sha256: str
    header_sha256: str
    header: tuple[str, ...]
    declared_safe_columns: tuple[str, ...]
    declared_protected_columns: tuple[str, ...]
    present_safe_columns: tuple[str, ...]
    missing_safe_columns: tuple[str, ...]
    present_protected_columns: tuple[str, ...]
    missing_protected_columns: tuple[str, ...]
    closed_unclassified_columns: tuple[str, ...]
    qualified_to_freeze_manifest: bool
    reasons: tuple[str, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def header_sha256(header: tuple[str, ...]) -> str:
    payload = json.dumps(
        list(header),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_header(path: Path) -> tuple[str, ...]:
    """Decode only the first physical CSV record.

    The complete file may be hashed opaquely elsewhere, but this function does
    not create a text decoder over the remaining data rows.
    """

    with path.open("rb") as handle:
        raw_header = handle.readline()
    if not raw_header:
        raise MixedCSVFirewallError("empty CSV")
    try:
        decoded = raw_header.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise MixedCSVFirewallError("CSV header is not valid UTF-8") from exc

    reader = csv.reader([decoded])
    try:
        return tuple(next(reader))
    except StopIteration as exc:
        raise MixedCSVFirewallError("empty CSV header") from exc


def inspect_mixed_csv_header_for_freeze(
    path: Path,
    *,
    expected_file_sha256: str,
    safe_pre_response_columns: tuple[str, ...],
    protected_response_columns: tuple[str, ...],
) -> MixedCSVHeaderFreezeAudit:
    """Verify exact bytes and inspect only the header before a manifest freeze.

    This is deliberately a pre-row operation. It hashes the complete file as
    opaque bytes, decodes only the first physical record, and classifies column
    names against declarations made before row values are semantically opened.
    Unknown columns remain closed.
    """

    observed_file_sha = sha256_file(path)
    if observed_file_sha != expected_file_sha256:
        raise MixedCSVFirewallError("mixed CSV file SHA mismatch")

    safe = tuple(safe_pre_response_columns)
    protected = tuple(protected_response_columns)
    if len(safe) != len(set(safe)):
        raise MixedCSVFirewallError("duplicate safe column declaration")
    if len(protected) != len(set(protected)):
        raise MixedCSVFirewallError("duplicate protected column declaration")
    overlap = sorted(set(safe) & set(protected))
    if overlap:
        raise MixedCSVFirewallError(
            "safe/protected column overlap: " + ", ".join(overlap)
        )

    header = read_header(path)
    header_set = set(header)
    safe_set = set(safe)
    protected_set = set(protected)

    present_safe = tuple(name for name in header if name in safe_set)
    present_protected = tuple(name for name in header if name in protected_set)
    missing_safe = tuple(sorted(safe_set - header_set))
    missing_protected = tuple(sorted(protected_set - header_set))
    closed = tuple(sorted(header_set - safe_set - protected_set))

    reasons: list[str] = []
    if missing_safe:
        reasons.append("missing_declared_safe_columns")
    if missing_protected:
        reasons.append("missing_declared_protected_columns")

    return MixedCSVHeaderFreezeAudit(
        file_sha256=observed_file_sha,
        header_sha256=header_sha256(header),
        header=header,
        declared_safe_columns=safe,
        declared_protected_columns=protected,
        present_safe_columns=present_safe,
        missing_safe_columns=missing_safe,
        present_protected_columns=present_protected,
        missing_protected_columns=missing_protected,
        closed_unclassified_columns=closed,
        qualified_to_freeze_manifest=not reasons,
        reasons=tuple(reasons),
    )


def manifest_from_header_freeze(
    audit: MixedCSVHeaderFreezeAudit,
) -> MixedCSVColumnManifest:
    """Create a projection manifest only from a fully qualified header audit."""

    if not audit.qualified_to_freeze_manifest:
        raise MixedCSVFirewallError(
            "header audit is not qualified to freeze manifest: "
            + ", ".join(audit.reasons)
        )
    return MixedCSVColumnManifest(
        file_sha256=audit.file_sha256,
        header_sha256=audit.header_sha256,
        safe_pre_response_columns=audit.declared_safe_columns,
        protected_response_columns=audit.declared_protected_columns,
    )


def audit_mixed_csv_header(
    path: Path,
    manifest: MixedCSVColumnManifest,
) -> MixedCSVHeaderAudit:
    """Verify SHA/header and compute the only columns allowed before response access."""

    if sha256_file(path) != manifest.file_sha256:
        raise MixedCSVFirewallError("mixed CSV file SHA mismatch")

    header = read_header(path)
    if header_sha256(header) != manifest.header_sha256:
        raise MixedCSVFirewallError("mixed CSV header SHA mismatch")

    header_set = set(header)
    safe = set(manifest.safe_pre_response_columns)
    protected = set(manifest.protected_response_columns)
    if safe & protected:
        raise MixedCSVFirewallError("safe/protected column overlap")
    missing_safe = sorted(safe - header_set)
    missing_protected = sorted(protected - header_set)
    if missing_safe:
        raise MixedCSVFirewallError(
            "missing safe columns: " + ", ".join(missing_safe)
        )
    if missing_protected:
        raise MixedCSVFirewallError(
            "missing protected columns: " + ", ".join(missing_protected)
        )

    closed = tuple(sorted(header_set - safe - protected))
    return MixedCSVHeaderAudit(
        header=header,
        safe_pre_response_columns=tuple(
            name for name in header if name in safe
        ),
        protected_response_columns=tuple(
            name for name in header if name in protected
        ),
        closed_unclassified_columns=closed,
    )


def project_safe_columns(
    path: Path,
    manifest: MixedCSVColumnManifest,
) -> tuple[dict[str, str], ...]:
    """Return only predeclared safe columns; protected values are never returned.

    The CSV parser must structurally tokenize each record, but the function never
    exposes, summarizes, branches on, or persists protected/unclassified values.
    """

    audit_mixed_csv_header(path, manifest)
    safe = tuple(manifest.safe_pre_response_columns)
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise MixedCSVFirewallError("missing CSV header")
        for row in reader:
            rows.append({name: row.get(name, "") for name in safe})
    return tuple(rows)
