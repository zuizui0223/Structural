from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from structural.mixed_csv_firewall import (
    MixedCSVColumnManifest,
    MixedCSVFirewallError,
    audit_mixed_csv_header,
    header_sha256,
    project_safe_columns,
    sha256_file,
)


def write_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["site", "year", "UTMe", "UTMn", "species", "obs1"])
        writer.writerow(["A", "2012", "100", "200", "RACA", "1"])
        writer.writerow(["B", "2012", "110", "210", "AMMA", "0"])


def manifest(path: Path) -> MixedCSVColumnManifest:
    header = ("site", "year", "UTMe", "UTMn", "species", "obs1")
    return MixedCSVColumnManifest(
        file_sha256=sha256_file(path),
        header_sha256=header_sha256(header),
        safe_pre_response_columns=("site", "year", "UTMe", "UTMn"),
        protected_response_columns=("species", "obs1"),
    )


def test_mixed_header_opens_only_declared_safe_columns(tmp_path: Path):
    path = tmp_path / "mixed.csv"
    write_csv(path)
    audit = audit_mixed_csv_header(path, manifest(path))
    assert audit.safe_pre_response_columns == ("site", "year", "UTMe", "UTMn")
    assert audit.protected_response_columns == ("species", "obs1")
    assert audit.closed_unclassified_columns == ()


def test_safe_projection_never_returns_response_columns(tmp_path: Path):
    path = tmp_path / "mixed.csv"
    write_csv(path)
    rows = project_safe_columns(path, manifest(path))
    assert rows == (
        {"site": "A", "year": "2012", "UTMe": "100", "UTMn": "200"},
        {"site": "B", "year": "2012", "UTMe": "110", "UTMn": "210"},
    )
    assert all("species" not in row and "obs1" not in row for row in rows)


def test_unclassified_columns_remain_closed(tmp_path: Path):
    path = tmp_path / "mixed.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["site", "year", "mystery", "species"])
        writer.writerow(["A", "2012", "x", "RACA"])
    m = MixedCSVColumnManifest(
        file_sha256=sha256_file(path),
        header_sha256=header_sha256(("site", "year", "mystery", "species")),
        safe_pre_response_columns=("site", "year"),
        protected_response_columns=("species",),
    )
    audit = audit_mixed_csv_header(path, m)
    assert audit.closed_unclassified_columns == ("mystery",)
    assert "mystery" not in project_safe_columns(path, m)[0]


def test_sha_mismatch_fails_closed(tmp_path: Path):
    path = tmp_path / "mixed.csv"
    write_csv(path)
    m = manifest(path)
    broken = MixedCSVColumnManifest(
        file_sha256="0" * 64,
        header_sha256=m.header_sha256,
        safe_pre_response_columns=m.safe_pre_response_columns,
        protected_response_columns=m.protected_response_columns,
    )
    with pytest.raises(MixedCSVFirewallError, match="SHA mismatch"):
        audit_mixed_csv_header(path, broken)


def test_safe_and_protected_overlap_fails(tmp_path: Path):
    path = tmp_path / "mixed.csv"
    write_csv(path)
    h = ("site", "year", "UTMe", "UTMn", "species", "obs1")
    m = MixedCSVColumnManifest(
        file_sha256=sha256_file(path),
        header_sha256=header_sha256(h),
        safe_pre_response_columns=("site", "species"),
        protected_response_columns=("species", "obs1"),
    )
    with pytest.raises(MixedCSVFirewallError, match="overlap"):
        audit_mixed_csv_header(path, m)
