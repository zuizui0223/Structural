# Indo-Pacific atoll plants corrected pre-pilot freeze v0.20

## Why v0.18 was retired

The v0.18 router defined a different species universe for each held-out pilot block. That is incompatible with the frozen v0.32 arithmetic, which treats the rows in all other blocks as the training complement of the held-out rows.

This defect was detected **before any plant response was opened**. The v0.18 protocol is preserved as retired pre-response provenance and contributes zero evidence.

## Corrected endpoint

The 13 burned-pilot blocks and 50 confirmatory blocks are unchanged.

After the pilot response opens, define exactly one fixed pilot-supported species universe:

> species with native code `N` in at least two distinct frozen burned-pilot spatial blocks.

The same species set is then used in every pilot block.

For every source-designated complete plant inventory atoll and every species in that fixed set:

- `N` -> target 1;
- `I` -> target 0;
- no row -> target 0.

Blocks without a complete catalogue, or an empty supported species universe, are non-estimable.

The sorted pilot-supported species list and its SHA-256 are design outputs only. If the pilot passes, they may be frozen into a separate confirmatory protocol. They do not count as effect or predictive evidence.

## Immutable identities

- replacement v0.31b fingerprint: `ee8cccc38fb8f4602e05e97d9d875c5ad8773280460c0dafca36ac03fe5871f5`
- bound v0.42b fingerprint: `1b3ad5da960ceac60e594b3ed664a39835e2f49ba1f7d70bfd32ee1c54e28fc6`

Spatial design remains:

- physical graph: 310 atolls;
- model targets: 292 atolls;
- graph radii: 36 / 58 / 126 / 233 km;
- partition radius: 233 km;
- pilot blocks: 13;
- confirmatory blocks: 50;
- q75 major-landmass isolation: 775.3375 km.

## Firewall

Confirmatory rows may expose only the atoll routing field. Their species and presence bytes are never decoded.

Synthetic tests additionally require the exact fixed-universe raw surface to pass the existing v0.32 complement arithmetic.

## Evidence ceiling

Before the one-shot burned pilot:

- pilot response accessed: false;
- confirmatory response accessed: false;
- effect size: none;
- prediction score: none;
- predictive denominator contribution: 0.
