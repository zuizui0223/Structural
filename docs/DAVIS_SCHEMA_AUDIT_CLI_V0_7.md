# Davis schema audit CLI v0.7

## Purpose

This tool is the first executable step of the v0.6 retrospective Davis pilot.

It accepts an extracted Dryad archive directory and inspects only:

- required file presence;
- CSV headers;
- identifier support;
- repeated-year structure;
- literal `Patch` / `Pop` identifier-set relationships;
- file sizes and SHA-256 fingerprints.

It does **not** fit a model, rank candidate connectivity metrics, or summarize the values of the genetic endpoints.

## Usage

    python scripts/audit_davis_schema_v0_7.py /path/to/extracted/DRYAD_Clean \
      --output build/davis_schema_audit_v0_7.json

A successful audit returns exit code 0.

A missing/duplicate file or required-header mismatch returns a scientific/data-structure STOP with exit code 2.

## Required source objects

The adapter locates exactly one instance of each basename recursively:

- `Genetic_Data_Master.csv`
- `Hummingbird_Data.csv`
- `Data_Patches.csv`
- `whole_landscape_metrics.RData`
- `patch_based_metrics.RData`

The RData objects are fingerprinted and presence-checked only. v0.7 does not open them.

## Join boundary

The genetic and patch tables use `Pop`; the hummingbird table uses `Patch`.

v0.7 reports literal identifier-set equality and differences. It **does not** treat equality as proof of ecological identity and it does not repair aliases when the sets differ.

An explicit source mapping or documented identity is required before building a joined analysis table.

## Response boundary

Although the genetic CSV physically contains endpoint columns, v0.7 only reads:

- `Mom_ID`
- `Year`
- `Pop`

from data rows. Endpoint columns are checked for header presence only.

The output therefore has:

- `model_fit_count = 0`
- `candidate_ranking_count = 0`
- `endpoint_value_summary_count = 0`

This does not make Davis fresh evidence—the published result is already known. It only prevents the retrospective adapter itself from using outcome values prematurely.
