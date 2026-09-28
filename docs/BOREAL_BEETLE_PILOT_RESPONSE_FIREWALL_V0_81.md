# Boreal beetle pilot response firewall v0.81

v0.81 prepares the first biological-response boundary without opening it.

## Authorization

A future authorization can be issued only after exact committed v0.31 and
fingerprint-bound v0.42 artifacts exist and the v0.80 receipt proves that both
were constructed from the validator-clean v0.12 intake and SHA-bound v0.75
spatial partition.

The authorization binds the primary beetle response file to the exact Dryad
identity already frozen in v0.65:

- file ID 4569032;
- 49,005 bytes;
- SHA-256
  `01eef34863bfd49fdc68dfae0aec58766a6fcdd1234751a9c75824df9f038be0`.

A successful authorization is one-shot and still contributes zero empirical
evidence.

## Byte-level router

The response matrix is a pure response file, so ordinary whole-file CSV
decoding is too permissive. The boreal router parses records at byte level.

For all 42 rows it may decode only the first routing field (`Island`). When an
island maps to a **confirmatory** v0.75 block, the remaining 466 occurrence
fields are discarded as opaque bytes.

Only pilot-island rows have their 0/1 cells decoded.

The header may be opened to identify the 466 species. The frozen prospective
schema is one `Island` column plus 466 unique nonblank species columns.

## Common pilot species universe

After pilot cells open exactly once, the common species universe is:

> species detected on at least two distinct frozen pilot islands.

That single universe is applied to every pilot spatial block. Each emitted v0.32
row uses the spatial block ID as both `partition_unit` and `block`, matching
the v0.80 v0.31 protocol.

Confirmatory occurrence parse count is structurally required to remain zero.

## Ceiling

v0.81 only prepares authorization and routing. A separate consumption/execution
receipt is still required to prove the one-shot pilot was actually routed and
audited. Confirmatory response remains sealed throughout.
