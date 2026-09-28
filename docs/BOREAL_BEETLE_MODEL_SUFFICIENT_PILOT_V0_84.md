# Boreal model-sufficient one-shot pilot v0.84

## Gap closed

v0.82 correctly preserved the burned-pilot gate result and fixed species
universe, but that is not enough to fit the later confirmatory model.

The eventual R3/C model needs the actual **pilot island × fixed-species 0/1
matrix**. Without preserving that matrix during the first pilot opening, a later
confirmatory-model freeze would have to reopen the biological response file.

v0.84 closes that route before any real pilot has been consumed.

## Single semantic pass

The byte-level router still decodes:

- species header names;
- Island routing fields for all 42 rows;
- occurrence cells for pilot islands only.

Confirmatory occurrence bytes remain opaque.

During that same parse, the router now preserves a compact matrix over the
fixed pilot-supported species universe:

- species order;
- pilot island order;
- pilot island → spatial block;
- one fixed-width hexadecimal bitstring per pilot island.

The bitstring can be replayed exactly to the 0/1 vector. No second semantic
parse is required.

## Canonical future executor

v0.84 prospectively supersedes the unexecuted v0.82 executor. The v0.81
authorization remains the parent access gate, but the first real pilot must use
v0.84.

A qualified run freezes both:

1. the normal v0.32/v0.42 admission evidence; and
2. a model-sufficient pilot training snapshot.

A failed post-access run still consumes the authorization and terminates the
protocol version. Its snapshot, if routing completed, is audit-only and cannot
rescue the failed gate.

## Evidence ceiling

The pilot snapshot is response-derived training material, but it is not a
predictive endpoint result:

- effect size: null;
- prediction score: null;
- predictive denominator contribution: 0;
- confirmatory response: sealed.

Its only scientific purpose is to allow the later R0–R3–C model and all
confirmatory predictions to be frozen without reopening pilot response.
