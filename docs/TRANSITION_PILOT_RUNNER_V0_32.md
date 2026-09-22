# Transition pilot runner v0.32

## Purpose

v0.32 executes the burned-pilot estimability audit while keeping the confirmatory partition sealed.

Input 1 is a frozen v0.31 protocol.
Input 2 is a pilot-only CSV with exactly these required columns:

- partition_unit
- block
- target

The target may be 0, 1 or missing/non-estimable.

## Hard firewall

The runner stops immediately when:

- any confirmatory partition unit appears in the pilot CSV;
- a row belongs to a partition unit that was not frozen in the protocol;
- a frozen pilot unit is missing entirely from the supplied pilot response.

The confirmatory response is never used.

## Output

The output contains only estimability accounting:

- applicable pilot rows;
- positive / negative / non-estimable counts;
- block-level test/training class counts;
- estimable-block count;
- qualified-for-new-confirmatory-protocol or stop-endpoint-variation.

The output explicitly sets:

- effect_size = null
- prediction_score = null
- predictive_denominator_contribution = 0

A successful pilot therefore demonstrates feasibility only.

## Exit codes

- 0 — pilot passes the frozen estimability gate;
- 1 — invalid input/protocol;
- 2 — scientific/protocol STOP.

## Next gate

A pilot pass does not open confirmation.

It only permits creation of a separate confirmatory protocol that freezes the state/reference/connectivity/scoring design while the confirmatory response remains sealed.
