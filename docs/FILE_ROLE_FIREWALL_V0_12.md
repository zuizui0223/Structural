# File-role firewall v0.12

## Purpose

v0.11 freezes the physical file inventory without reading semantic content.

v0.12 is the next gate: every inventoried file receives exactly one role while remaining tied to its SHA-256.

Allowed roles:

- **safe_schema** — semantic content may be opened before response freeze;
- **metadata** — descriptive/source metadata may be opened;
- **response** — focal response values; remains closed;
- **code** — analysis/source code; remains closed by default because it may reveal response-driven choices;
- **unknown** — role not yet proven; remains closed.

## Safety rule

Only `safe_schema` and `metadata` are placed on the semantic-open allowlist.

A filename that looks harmless is not automatically safe. Role assignment must be explicit and SHA-pinned.

## Usage

First build inventory:

    python scripts/inventory_candidate_archive_v0_11.py candidate.zip \
      --output build/inventory.json

Then prepare a role manifest from:

    development/file_role_manifest_template_v0_12.json

Finally validate:

    python scripts/apply_file_role_firewall_v0_12.py \
      build/inventory.json roles.json \
      --output build/file_role_firewall.json

## Hard stops

The firewall stops when:

- any inventory file lacks a role;
- a role manifest contains an unknown file;
- a SHA-256 does not match the frozen inventory;
- a role value is invalid.

## Why code remains closed

Original analysis code may expose the published response definition, candidate ranking, fitted scales or post-outcome choices.

Therefore code is not treated as schema-safe by default. A later explicit code-review protocol may open it if needed, but v0.12 does not.

## Pipeline

    v0.11 opaque file inventory
        → v0.12 SHA-pinned role firewall
        → open safe_schema + metadata only
        → verify geometry / IDs / time structure
        → freeze response firewall and protocol
        → only then open response

This prevents accidental outcome access while resolving physical joins and geometry.
