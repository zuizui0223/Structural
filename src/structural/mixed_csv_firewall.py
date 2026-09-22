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
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return tuple(next(reader))
        except StopIteration as exc:
            raise MixedCSVFirewallError("empty CSV") from exc


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
