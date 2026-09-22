"""Safe-schema table audit after the v0.12 file-role firewall."""
from __future__ import annotations

from contextlib import contextmanager
import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from zipfile import ZipFile

from .file_inventory import inventory_source, to_mapping
from .file_roles import (
    FileRole,
    FileRoleFirewallError,
    apply_file_role_firewall,
    assignments_from_mapping,
)


class SafeSchemaAuditError(RuntimeError):
    pass


@dataclass(frozen=True)
class SafeSchemaRequest:
    relative_path: str
    id_columns: tuple[str, ...] = ()
    time_columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class SafeSchemaEntry:
    relative_path: str
    header: tuple[str, ...]
    row_count: int
    unique_nonblank_counts: tuple[tuple[str, int], ...]
    repeated_time_structure: bool


def _inventory_map(inventory: dict) -> dict[str, tuple[int, str]]:
    entries = inventory.get("entries")
    if not isinstance(entries, list):
        raise SafeSchemaAuditError("inventory entries must be a list")
    out: dict[str, tuple[int, str]] = {}
    for row in entries:
        path = row.get("relative_path")
        size = row.get("size_bytes")
        digest = row.get("sha256")
        if not isinstance(path, str) or not isinstance(size, int) or not isinstance(digest, str):
            raise SafeSchemaAuditError("invalid inventory entry")
        out[path] = (size, digest)
    return out


def verify_source_matches_inventory(source: Path, inventory: dict) -> None:
    current = to_mapping(inventory_source(source))
    frozen = _inventory_map(inventory)
    observed = _inventory_map(current)
    if frozen != observed:
        raise SafeSchemaAuditError("physical source does not match frozen v0.11 inventory")


@contextmanager
def _open_text(source: Path, relative_path: str) -> Iterator[io.TextIOBase]:
    source = source.resolve()
    if source.is_dir():
        path = (source / relative_path).resolve()
        try:
            path.relative_to(source)
        except ValueError as exc:
            raise SafeSchemaAuditError("requested path escapes source directory") from exc
        if not path.is_file():
            raise SafeSchemaAuditError(f"missing requested safe-schema file: {relative_path}")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            yield handle
        return

    if source.is_file() and source.suffix.lower() == ".zip":
        with ZipFile(source) as archive:
            try:
                raw = archive.open(relative_path, "r")
            except KeyError as exc:
                raise SafeSchemaAuditError(
                    f"missing requested safe-schema file in ZIP: {relative_path}"
                ) from exc
            with raw:
                with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as handle:
                    yield handle
        return

    raise SafeSchemaAuditError("source must be a directory or .zip archive")


def audit_safe_schema(
    source: Path,
    inventory: dict,
    role_manifest: dict,
    requests: tuple[SafeSchemaRequest, ...],
) -> tuple[SafeSchemaEntry, ...]:
    """Open only files explicitly assigned SAFE_SCHEMA and report schema summaries."""

    verify_source_matches_inventory(source, inventory)

    try:
        assignments = assignments_from_mapping(role_manifest)
        apply_file_role_firewall(inventory, assignments)
    except (ValueError, FileRoleFirewallError) as exc:
        raise SafeSchemaAuditError(str(exc)) from exc

    role_map = {assignment.relative_path: assignment.role for assignment in assignments}
    if len({request.relative_path for request in requests}) != len(requests):
        raise SafeSchemaAuditError("duplicate safe-schema request")

    results: list[SafeSchemaEntry] = []
    for request in requests:
        role = role_map.get(request.relative_path)
        if role is not FileRole.SAFE_SCHEMA:
            raise SafeSchemaAuditError(
                f"semantic open denied by file-role firewall: {request.relative_path}"
            )

        suffix = Path(request.relative_path).suffix.lower()
        if suffix not in {".csv", ".tsv"}:
            raise SafeSchemaAuditError(
                f"unsupported safe-schema table type: {request.relative_path}"
            )
        delimiter = "\t" if suffix == ".tsv" else ","

        with _open_text(source, request.relative_path) as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            if reader.fieldnames is None:
                raise SafeSchemaAuditError(
                    f"missing table header: {request.relative_path}"
                )
            header = tuple(reader.fieldnames)
            required = tuple(dict.fromkeys(request.id_columns + request.time_columns))
            missing = [name for name in required if name not in header]
            if missing:
                raise SafeSchemaAuditError(
                    f"missing requested schema columns in {request.relative_path}: "
                    + ", ".join(missing)
                )

            unique: dict[str, set[str]] = {name: set() for name in required}
            row_count = 0
            for row in reader:
                row_count += 1
                for name in required:
                    value = (row.get(name) or "").strip()
                    if value:
                        unique[name].add(value)

        counts = tuple((name, len(unique[name])) for name in required)
        repeated = any(len(unique[name]) > 1 for name in request.time_columns)
        results.append(
            SafeSchemaEntry(
                relative_path=request.relative_path,
                header=header,
                row_count=row_count,
                unique_nonblank_counts=counts,
                repeated_time_structure=repeated,
            )
        )

    return tuple(results)


def requests_from_mapping(data: dict) -> tuple[SafeSchemaRequest, ...]:
    rows = data.get("audits")
    if not isinstance(rows, list):
        raise SafeSchemaAuditError("schema plan audits must be a list")
    out: list[SafeSchemaRequest] = []
    for row in rows:
        if not isinstance(row, dict):
            raise SafeSchemaAuditError("schema audit request must be an object")
        path = row.get("relative_path")
        ids = row.get("id_columns", [])
        times = row.get("time_columns", [])
        if not isinstance(path, str):
            raise SafeSchemaAuditError("relative_path must be string")
        if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            raise SafeSchemaAuditError("id_columns must be a list of strings")
        if not isinstance(times, list) or not all(isinstance(x, str) for x in times):
            raise SafeSchemaAuditError("time_columns must be a list of strings")
        out.append(
            SafeSchemaRequest(
                relative_path=path,
                id_columns=tuple(ids),
                time_columns=tuple(times),
            )
        )
    return tuple(out)


def to_mapping(entries: tuple[SafeSchemaEntry, ...]) -> dict:
    return {
        "schema": "structural.safe_schema_audit.v0_13",
        "status": "safe_schema_audit_complete",
        "opened_files": [entry.relative_path for entry in entries],
        "entries": [
            {
                "relative_path": entry.relative_path,
                "header": list(entry.header),
                "row_count": entry.row_count,
                "unique_nonblank_counts": dict(entry.unique_nonblank_counts),
                "repeated_time_structure": entry.repeated_time_structure,
            }
            for entry in entries
        ],
        "response_files_opened": 0,
        "code_files_opened": 0,
        "unknown_files_opened": 0,
        "model_fit_count": 0,
    }
