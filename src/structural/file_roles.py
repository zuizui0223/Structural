"""File-role firewall applied after content-blind inventory."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FileRole(str, Enum):
    SAFE_SCHEMA = "safe_schema"
    METADATA = "metadata"
    RESPONSE = "response"
    CODE = "code"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FileRoleAssignment:
    relative_path: str
    sha256: str
    role: FileRole


@dataclass(frozen=True)
class FileRoleFirewallResult:
    allowed_for_semantic_open: tuple[str, ...]
    denied_for_semantic_open: tuple[str, ...]
    response_files: tuple[str, ...]
    unknown_files: tuple[str, ...]
    code_files: tuple[str, ...]


class FileRoleFirewallError(RuntimeError):
    pass


def apply_file_role_firewall(
    inventory: dict,
    assignments: tuple[FileRoleAssignment, ...],
) -> FileRoleFirewallResult:
    """Validate complete path/hash assignment and compute semantic-open allowlist.

    Only SAFE_SCHEMA and METADATA files are semantically openable at this stage.
    RESPONSE, CODE and UNKNOWN remain closed.
    """

    entries = inventory.get("entries")
    if not isinstance(entries, list):
        raise FileRoleFirewallError("inventory entries must be a list")

    inventory_map: dict[str, str] = {}
    for entry in entries:
        path = entry.get("relative_path")
        digest = entry.get("sha256")
        if not isinstance(path, str) or not isinstance(digest, str):
            raise FileRoleFirewallError("invalid inventory entry")
        if path in inventory_map:
            raise FileRoleFirewallError(f"duplicate inventory path: {path}")
        inventory_map[path] = digest

    assignment_map: dict[str, FileRoleAssignment] = {}
    for assignment in assignments:
        if assignment.relative_path in assignment_map:
            raise FileRoleFirewallError(
                f"duplicate role assignment: {assignment.relative_path}"
            )
        assignment_map[assignment.relative_path] = assignment

    missing = sorted(set(inventory_map) - set(assignment_map))
    extra = sorted(set(assignment_map) - set(inventory_map))
    if missing:
        raise FileRoleFirewallError(
            "missing role assignments: " + ", ".join(missing)
        )
    if extra:
        raise FileRoleFirewallError(
            "role assignments for unknown files: " + ", ".join(extra)
        )

    for path, expected_sha in inventory_map.items():
        if assignment_map[path].sha256 != expected_sha:
            raise FileRoleFirewallError(f"SHA mismatch for role assignment: {path}")

    allowed = tuple(
        sorted(
            path
            for path, assignment in assignment_map.items()
            if assignment.role in {FileRole.SAFE_SCHEMA, FileRole.METADATA}
        )
    )
    denied = tuple(sorted(set(inventory_map) - set(allowed)))
    response = tuple(
        sorted(
            path
            for path, assignment in assignment_map.items()
            if assignment.role is FileRole.RESPONSE
        )
    )
    unknown = tuple(
        sorted(
            path
            for path, assignment in assignment_map.items()
            if assignment.role is FileRole.UNKNOWN
        )
    )
    code = tuple(
        sorted(
            path
            for path, assignment in assignment_map.items()
            if assignment.role is FileRole.CODE
        )
    )

    return FileRoleFirewallResult(
        allowed_for_semantic_open=allowed,
        denied_for_semantic_open=denied,
        response_files=response,
        unknown_files=unknown,
        code_files=code,
    )


def assignments_from_mapping(data: dict) -> tuple[FileRoleAssignment, ...]:
    rows = data.get("assignments")
    if not isinstance(rows, list):
        raise FileRoleFirewallError("role manifest assignments must be a list")

    out: list[FileRoleAssignment] = []
    for row in rows:
        if not isinstance(row, dict):
            raise FileRoleFirewallError("role assignment must be an object")
        for key in ("relative_path", "sha256", "role"):
            if key not in row:
                raise FileRoleFirewallError(f"missing role assignment key: {key}")
        out.append(
            FileRoleAssignment(
                relative_path=str(row["relative_path"]),
                sha256=str(row["sha256"]),
                role=FileRole(row["role"]),
            )
        )
    return tuple(out)
