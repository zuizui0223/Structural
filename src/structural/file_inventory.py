"""Content-blind file inventory for connectivity candidate archives."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from zipfile import ZipFile


@dataclass(frozen=True)
class InventoryEntry:
    relative_path: str
    suffix: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class InventoryResult:
    source_type: str
    source_path: str
    entries: tuple[InventoryEntry, ...]
    total_bytes: int
    semantic_text_parse_count: int = 0
    response_value_parse_count: int = 0
    model_fit_count: int = 0


class InventoryError(RuntimeError):
    pass


def _sha256_stream(handle) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def inventory_directory(root: Path) -> InventoryResult:
    root = root.resolve()
    if not root.is_dir():
        raise InventoryError(f"not a directory: {root}")

    entries: list[InventoryEntry] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        with path.open("rb") as handle:
            digest = _sha256_stream(handle)
        entries.append(
            InventoryEntry(
                relative_path=rel,
                suffix=path.suffix.lower(),
                size_bytes=path.stat().st_size,
                sha256=digest,
            )
        )

    return InventoryResult(
        source_type="directory",
        source_path=str(root),
        entries=tuple(entries),
        total_bytes=sum(entry.size_bytes for entry in entries),
    )


def inventory_zip(path: Path) -> InventoryResult:
    path = path.resolve()
    if not path.is_file():
        raise InventoryError(f"not a file: {path}")

    entries: list[InventoryEntry] = []
    seen: set[str] = set()
    with ZipFile(path) as archive:
        for info in sorted(
            (i for i in archive.infolist() if not i.is_dir()),
            key=lambda x: x.filename,
        ):
            rel = Path(info.filename).as_posix()
            if rel in seen:
                raise InventoryError(f"duplicate archive path: {rel}")
            seen.add(rel)
            with archive.open(info, "r") as handle:
                digest = _sha256_stream(handle)
            entries.append(
                InventoryEntry(
                    relative_path=rel,
                    suffix=Path(rel).suffix.lower(),
                    size_bytes=info.file_size,
                    sha256=digest,
                )
            )

    return InventoryResult(
        source_type="zip",
        source_path=str(path),
        entries=tuple(entries),
        total_bytes=sum(entry.size_bytes for entry in entries),
    )


def inventory_source(path: Path) -> InventoryResult:
    """Inventory a directory or ZIP without decoding or parsing file contents."""

    if path.is_dir():
        return inventory_directory(path)
    if path.is_file() and path.suffix.lower() == ".zip":
        return inventory_zip(path)
    raise InventoryError("source must be a directory or .zip archive")


def to_mapping(result: InventoryResult) -> dict:
    return {
        "schema": "structural.content_blind_inventory.v0_11",
        "source_type": result.source_type,
        "source_path": result.source_path,
        "file_count": len(result.entries),
        "total_bytes": result.total_bytes,
        "entries": [
            {
                "relative_path": entry.relative_path,
                "suffix": entry.suffix,
                "size_bytes": entry.size_bytes,
                "sha256": entry.sha256,
            }
            for entry in result.entries
        ],
        "semantic_text_parse_count": result.semantic_text_parse_count,
        "response_value_parse_count": result.response_value_parse_count,
        "model_fit_count": result.model_fit_count,
    }
