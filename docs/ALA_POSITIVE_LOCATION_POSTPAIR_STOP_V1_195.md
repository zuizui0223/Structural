# ALA v1.194 one-shot terminal execution audit (v1.195)

The `v1.194` ALA execution **did not produce an ecological score**. The exact source ZIP and frozen-input fingerprints passed, but the scorer exited `STOP_ALA_EXTERNAL_PAIR_SCHEMA_OR_FROZEN_INPUT_DRIFT` with `prediction shape drift` during prediction loading. Workflow run: [37746153286](https://github.com/zuizui0223/Structural/actions/runs/37746153286).

## Technical root cause (response-free static source inspection)

`scripts/freeze_global_mammals_ultrarare_predictions_v1_113.py` writes an actual prediction-file header using `struct.pack("<II",4126,S)`. Each island/species cell then has **two** float64 predictions, giving logical payload dimensions `(4126,529,2)` but only **two dimensions recorded in the header**.

`scripts/score_global_mammals_ala_positive_locations_v1_194.py` instead passes `(4126,529,2)` to a generic reader that takes the length of the requested *logical payload shape* to decide how many uint32 header dimensions to read. It attempts to unpack **three** header integers from a **two**-integer header. That deterministically yields the observed shape drift before any loss is scored. The original published scoring code correctly reads the two-integer actual header and then reshapes the payload to `(4126,529,2)`.

This is a technical schema bug, *not an adverse independent-validation result*.

## The important access boundary

The execution code extracts deduplicated ALA taxon–FID positive pairs, checks >=50 pairs / >=10 taxa / >=15 islands / >=5 blocks, **then** reads the prediction file. Because the failure occurred at that final read step rather than returning the insufficient-support receipt, the minimum support gate was passed in that particular execution. Exact eligible counts are not preserved in the final public receipt. Do **not** infer or publish exact counts.

The external source ZIP and taxon×FID×eventDate observations were already semantically decoded at failure. The original 4,126-island heldout IUCN-derived labels remained unopened. This invalidates any claim that a corrected same-archive retry would be a never-before-seen confirmatory test.

The precommitted `v1.194` request explicitly says `same_lineage_rerun_authorized=false`. **Do not change the parser and retry this one-shot route**. Preserve the frozen technical STOP; do not treat it as support or non-support for C−R3 or kNN-versus-rewired superiority.

## Consequences

The 529-species kNN occurrence result remains internally supported **for curated IUCN-range-derived labels**, not confirmed contemporary movement or island census occurrence. v1.181's source-turnover analysis and BALA's temporal result remain adverse. GEB remains on ecological-mechanism submission HOLD.

A future independent validation must preflight its **exact prediction binary format and score implementation before any new external biological pair is exposed**; this is a response-independent software reliability gate, not a license to rescue this ALA lineage.

The separate Hébert et al. mammal checklist preintake remains response-opaque and awaits exact source-independent island identity and provenance support.
