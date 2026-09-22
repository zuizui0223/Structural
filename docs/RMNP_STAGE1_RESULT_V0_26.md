# RMNP Stage 1 result v0.26

## Stage 1 complete

The authorized 2021 AMMA state has now been opened and frozen.

All 2022 AMMA values remain sealed.

## 2021 source state

Among the frozen 116 high-effort source sites:

- AMMA positive: **4**
- AMMA negative: **112**
- non-estimable: **0**

The state-table fingerprint is:

`38018b783ebf03a20e08b7fa8adcc2c7a0473100ef7e83ad1e6c92cb2f5a2ca5`

The occupied-source set contains four sites and is independently fingerprinted:

`447ae926b242f2ee3457364aea6fe4d954e11388de5fdbe6e3551db0ecfb5274`

## Evaluation-site lagged state

Among the frozen 69 evaluation sites:

- 2021 positive: **1**
- 2021 negative: **68**
- non-estimable: **0**

This strong class imbalance is retained; it does not change the target protocol or connectivity worlds.

## Frozen connectivity features

The complete 69-row R0/R1/R2/C feature table has SHA-256:

`e45ad76a41126fed7dea2c147c094e2d5998dda548f99ac3efc700c68b900a1c`

Feature-side diagnostics:

- 57/69 evaluation sites have another generic source pond within at least one of the 500/1000 m worlds;
- 5/69 have another occupied source within at least one world;
- 1/69 has an occupied source within both worlds.

No 2022 target was used to construct or inspect these features.

## Firewall

- 2021 AMMA opened: yes
- 2022 AMMA opened: **no**
- PSMA/LISY opened: no
- model fits: 0
- candidate ranking: 0

## Next gate

Before 2022 AMMA is opened, the exact preprocessing/learner/scoring implementation must be frozen and merged. A separate Stage 2 authorization must then pin this Stage 1 feature fingerprint.

No feature, source anchor, scale, spatial block or reference variable may change after this point.
