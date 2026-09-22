from __future__ import annotations

import pytest

from structural.file_roles import (
    FileRole,
    FileRoleAssignment,
    FileRoleFirewallError,
    apply_file_role_firewall,
)


def inventory():
    return {
        "entries": [
            {"relative_path": "sites.csv", "sha256": "a" * 64},
            {"relative_path": "responses.csv", "sha256": "b" * 64},
            {"relative_path": "analysis.R", "sha256": "c" * 64},
            {"relative_path": "README.txt", "sha256": "d" * 64},
            {"relative_path": "mystery.dat", "sha256": "e" * 64},
        ]
    }


def roles():
    return (
        FileRoleAssignment("sites.csv", "a" * 64, FileRole.SAFE_SCHEMA),
        FileRoleAssignment("responses.csv", "b" * 64, FileRole.RESPONSE),
        FileRoleAssignment("analysis.R", "c" * 64, FileRole.CODE),
        FileRoleAssignment("README.txt", "d" * 64, FileRole.METADATA),
        FileRoleAssignment("mystery.dat", "e" * 64, FileRole.UNKNOWN),
    )


def test_only_safe_schema_and_metadata_are_openable():
    result = apply_file_role_firewall(inventory(), roles())
    assert result.allowed_for_semantic_open == ("README.txt", "sites.csv")
    assert result.response_files == ("responses.csv",)
    assert result.code_files == ("analysis.R",)
    assert result.unknown_files == ("mystery.dat",)
    assert set(result.denied_for_semantic_open) == {
        "responses.csv", "analysis.R", "mystery.dat"
    }


def test_missing_assignment_fails_closed():
    with pytest.raises(FileRoleFirewallError, match="missing role assignments"):
        apply_file_role_firewall(inventory(), roles()[:-1])


def test_unknown_extra_file_fails_closed():
    extra = roles() + (
        FileRoleAssignment("extra.csv", "f" * 64, FileRole.SAFE_SCHEMA),
    )
    with pytest.raises(FileRoleFirewallError, match="unknown files"):
        apply_file_role_firewall(inventory(), extra)


def test_sha_mismatch_fails_closed():
    wrong = list(roles())
    wrong[0] = FileRoleAssignment("sites.csv", "0" * 64, FileRole.SAFE_SCHEMA)
    with pytest.raises(FileRoleFirewallError, match="SHA mismatch"):
        apply_file_role_firewall(inventory(), tuple(wrong))


def test_code_is_not_semantically_open_by_default():
    result = apply_file_role_firewall(inventory(), roles())
    assert "analysis.R" not in result.allowed_for_semantic_open
