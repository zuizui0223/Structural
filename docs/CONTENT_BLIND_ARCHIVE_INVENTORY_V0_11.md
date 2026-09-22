# Content-blind archive inventory v0.11

## Purpose

v0.11 is the first physical-file operation allowed for a fresh connectivity candidate.

It inventories a directory or ZIP using only:

- relative file path;
- extension;
- uncompressed size;
- SHA-256.

It does **not** decode text, inspect headers, classify response columns, fit models, or summarize values.

## Usage

    python scripts/inventory_candidate_archive_v0_11.py candidate.zip \
      --output build/candidate_inventory_v0_11.json

Directories are also accepted.

## Why hashes are allowed

The tool reads file bytes only as an opaque byte stream for SHA-256. It never decodes or parses those bytes.

The receipt therefore explicitly fixes:

- `semantic_text_parse_count = 0`
- `response_value_parse_count = 0`
- `model_fit_count = 0`

This permits immutable file identity to be frozen before deciding which files may be opened for schema inspection.

## Sequence

    DOI/catalog metadata
        → v0.11 content-blind file inventory
        → classify files as safe-schema / response / unknown
        → open only safe-schema files
        → verify geometry and response firewall
        → protocol freeze
        → response-blind admission
        → outcome access only after authorization

## Claim boundary

File existence and hashes do not qualify a biological protocol. They only establish a reproducible physical source snapshot.

A file whose name appears to contain response data is **not** opened merely because it is present in the inventory.
