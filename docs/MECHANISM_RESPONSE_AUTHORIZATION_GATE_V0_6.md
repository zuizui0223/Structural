# Mechanism response authorization gate v0.6

## Purpose

v0.5 freezes an immutable confirmatory protocol for one eligible mechanism lane.

v0.6 is the first gate allowed to authorize opening that lane's confirmatory response.

It does **not** calculate the mechanism result.

## Committed freeze receipt required

A v0.5 receipt must already be committed to the repository.

v0.6 refuses an untracked receipt.

This gives a reviewable checkpoint between:

1. protocol freeze;
2. response access.

## Exact replay

v0.6 reruns the entire v0.5 freeze from raw inputs.

The committed receipt must equal the recomputed receipt exactly.

That binds response access to the already reviewed:

- Structural admission;
- mechanism admission;
- qualification inputs;
- response partition;
- primary estimand;
- reference and candidate;
- scoring rule;
- uncertainty rule;
- success rule.

Editing any of those after receipt commit breaks replay and stops authorization.

## Single-use scope

A successful receipt authorizes only:

> read the exact frozen response partition for this exact lane protocol once.

It does not authorize:

- another mechanism lane;
- another response partition;
- a changed scoring rule;
- protocol retuning;
- a mechanism conclusion;
- TTF handoff.

## Still no result

At authorization time:

- effect size is null;
- prediction score is null;
- predictive denominator contribution is zero;
- mechanism-claim contribution is zero;
- mechanism claim remains unauthorized.

The response has not yet been scored.

## After authorization

The next operation is:

`open_exact_response_partition_once_then_record_access_before_scoring`.

The access record must be created before any scoring output is accepted.

That later scoring stage must consume the exact v0.5 protocol fingerprint and v0.6 authorization id.

## Synthetic CI

Synthetic fixture authorizations are explicitly marked:

- `synthetic_ci_authorization = true`;
- `counts_as_empirical_evidence = false`.

They exercise the firewall only.

## Current state

No empirical mechanism response is authorized.
