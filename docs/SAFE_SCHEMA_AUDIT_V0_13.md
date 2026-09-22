# Safe-schema header audit v0.13

## Purpose

v0.13 is the first stage that semantically opens table contents for a fresh connectivity candidate.

It can open **only files already assigned `safe_schema` by the SHA-pinned v0.12 firewall**.

Response, code, metadata and unknown files cannot be requested.

## What the auditor may read

For CSV/TSV safe-schema files:

- header names;
- total row count;
- values of explicitly declared ID/time columns only.

It emits only **unique nonblank counts** for those ID/time columns, never the identifier values themselves.

This is sufficient to answer questions such as:

- Is there a stable waterbody/site identifier?
- Are coordinates in the safe table header?
- How many ecological units exist?
- Are multiple years/time points present?
- Can a leave-site-out or future-year split be defined?

## What it cannot do

v0.13 does not:

- open response files;
- open original analysis code;
- open unknown-role files;
- inspect focal species detections;
- compute connectivity;
- fit any model;
- choose a species, radius or kernel from outcomes.

## Source identity protection

Before opening a safe-schema table, the tool recomputes the v0.11 opaque inventory and requires an exact path/size/SHA match.

If the archive changed after role assignment, the audit stops.

## Usage

    python scripts/audit_safe_schema_v0_13.py \
      candidate.zip \
      build/inventory_v0_11.json \
      roles_v0_12.json \
      schema_plan_v0_13.json \
      --output build/safe_schema_v0_13.json

The plan template is:

    development/safe_schema_plan_template_v0_13.json

## Pipeline

    opaque inventory
        → SHA-pinned roles
        → safe-schema header/ID-time audit
        → geometry and response-firewall decision
        → freeze protocol
        → only then response access
