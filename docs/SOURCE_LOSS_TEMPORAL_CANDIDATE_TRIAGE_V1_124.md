# Source-loss leverage candidate triage v1.124

## What changed

The v1.123 three-time hypothesis was frozen before candidate-specific source-leverage analysis. Candidate search was then restricted to metadata: repeated census structure, island identity, geometry, survey design, data accessibility and whether the system has already contributed to Structural discovery.

No candidate has yet earned confirmatory status.

## Best immediately usable system: Finnish Common Eider

The strongest located stress-test system is the Finnish Archipelago Bird Census common-eider series.

The published dataset spans 1997–2020, contains 18,516 island-year counts from 3,648 islands, and exposes a stable `Island_ID`, annual breeding-pair counts, year fields and a coarse public spatial representation. The core Archipelago Bird Census estimates breeding numbers using at least two annual counts under a standardized protocol. Monitoring is unbalanced in time, with roughly 100–1,200 islands surveyed per year.

This is unusually close to the v1.123 design: the same species can experience many independent source-loss events through time, and later occupancy can be evaluated on islands that survived the first transition.

However, it is **not pristine confirmatory evidence**. The associated paper already reports broad population decline and geographic redistribution. Candidate selection therefore cannot be represented as response-sealed in the strongest sense. The correct evidence class is an independent, design-frozen retrospective stress test.

Before any source-leverage effect is computed, a schema-only gate must answer four questions:

1. Can `pos2` or another public field reconstruct a deterministic 2×2-km geometry without opening or tuning on the Structural endpoint?
2. Does `Eider_pairs = 0` always mean a surveyed zero for that island-year rather than missing/non-surveyed?
3. Can the subset of observations produced by redistribution of grouped-island counts be identified from the public data? If not, their inclusion rule must be frozen rather than chosen after seeing the Structural effect.
4. Are enough island sequences observed at t0, t1 and t2 to generate source-loss events and subsequent survivor contraction under disjoint burned-pilot and confirmatory partitions?

Only if these pass should the eider dataset enter a retrospective v0.31-style estimability pilot.

## Other candidates

**Thousand Island Lake birds** have the right biological monitoring structure: 36 of 42 long-term islands are reported to have consistent bird data. The blocker is access to the raw annual island×species sequence, not the ecological design.

**Thousand Island Lake vegetation** may ultimately be even cleaner for occupancy because plants avoid many detection problems. The programme reports 29 island plots surveyed every five years since 2009, but the public material located so far does not establish one accessible, same-protocol three-census island×species matrix.

**The global eBird island derivative** is enormous—4,205 islands across 2002–2019—but the archived files are occurrence records with checklist IDs and coordinates. The documented derivative does not include the complete-checklist and effort fields required for a safe species-specific absence rule. It therefore remains an endpoint HOLD.

**A-Islands** has 251 repeatedly sampled islands, but it is already a Structural discovery system and cannot provide independent confirmation. Its resurvey timing is also heterogeneous.

## Scientific consequence

This search sharpened the empirical requirement further. A useful source-loss dataset is not simply “long term.” It must contain **surveyed zeros**, because the mechanism is defined by disappearance between t0 and t1 and additional disappearance between t1 and t2. Presence-only archives can describe sources but cannot identify population loss without an effort-aware absence rule.

## Current next step

The immediate executable route is therefore:

> Finnish eider metadata/schema audit → response-free reconstruction of a coarse island geometry → estimability-only three-time pilot → only then freeze a retrospective source-leverage score.

The parallel confirmatory search remains open; no currently located system is promoted merely to avoid an empty confirmatory queue.
