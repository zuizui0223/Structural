# Confirmatory freeze gate v0.33

## Purpose

A successful burned pilot must not become a shortcut to confirmatory response access.

v0.33 inserts one more gate:

> a clean pilot pass may authorize **construction of a confirmatory protocol**, and nothing else.

## Required evidence

The pilot result must:

- report `qualified_for_new_confirmatory_protocol`;
- carry the exact fingerprint of the frozen v0.31 protocol;
- contain no effect size;
- contain no prediction score;
- contribute zero rows/effects to the predictive denominator;
- prove that the confirmatory partition was not opened.

The confirmatory response must still be unopened at the time this gate is checked.

## Eligible outcome

`eligible_to_freeze_confirmatory_protocol`

This means the project may now freeze:

- current-state/reference representation;
- typed connectivity representation;
- feature construction;
- heldout design;
- scoring implementation;
- confirmatory response firewall.

It does **not** authorize opening the confirmatory target.

## STOP outcomes

Any fingerprint mismatch, failed pilot, predictive pilot output, confirmatory-row exposure, or prior confirmatory response access stops the protocol version.

## Full future sequence

    metadata/schema qualification
      → v0.31 partition freeze
      → v0.32 burned-pilot execution
      → v0.30 estimability decision
      → v0.33 confirmatory-freeze gate
      → freeze confirmatory state/connectivity/scoring protocol
      → only then authorize confirmatory response
