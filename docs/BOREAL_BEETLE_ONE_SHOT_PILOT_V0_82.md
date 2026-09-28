# Boreal one-shot burned pilot v0.82

v0.82 freezes the irreversible pilot execution path but does not execute it.

## Pre-access failures

Before any response semantics open, the executor verifies:

- a valid unconsumed v0.81 authorization;
- exact v0.31 and v0.42 fingerprints;
- exact v0.75 spatial receipt binding;
- exact response size and SHA-256.

A failure here is `STOP_PRE_ACCESS` and does **not** consume the authorization.

## One-shot semantic access

After the exact response identity passes, the authorization is considered
consumed. The v0.81 byte-level router then opens only pilot occurrence cells and
must keep confirmatory target parse count at zero.

The router fixes one common pilot-supported species universe, emits the exact
three-column v0.32 surface, and the executor runs the existing v0.32 runner.

## Post-pilot admission

The executor then calls the existing v0.42 future-admission wrapper, which
recomputes the v0.31-v0.33 chain and the response-quality attrition gate.

A fully qualified pilot can authorize only:

> freeze_confirmatory_protocol_only

It still cannot open confirmatory response.

Any pilot-domain, endpoint-variation or response-quality failure after semantic
access is terminal for that protocol version. The authorization is consumed,
effect size and prediction score remain null, and the pilot contributes zero
predictive evidence.
