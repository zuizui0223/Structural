# Structural

Standalone repository for the structural/reference-adequacy paper formerly developed inside `zuizui0223/eog`.

## Scientific question

> After a declared reference model has already represented local support, source proximity and generic landscape context, does occurrence-conditioned landscape configuration retain additional held-out information?

## Central claim

Structural information is **reference-conditioned**. An occurrence-conditioned landscape signal can be detectable under a restricted reference yet fail to provide incremental held-out predictive value beyond a richer reference. Structural adequacy must therefore be earned relative to an explicitly declared reference and endpoint.

## Two origins of spatial separation

The paper deliberately spans two different origins of spatial separation:

- **pre-existing isolation** — A-Islands are naturally separated by ocean from the outset;
- **habitat fragmentation** — Tanzania forest fragments represent habitat that is partitioned within a terrestrial matrix.

These origins are not assumed to be biologically equivalent. The shared question is narrower and more general:

> **After the best declared description of the current ecological/geographic state is supplied, does an additional structural representation retain endpoint-relevant held-out information?**

Thus the framework does not require “island isolation” and “fragmentation” to be the same process. It tests whether their different histories leave residual predictive information beyond the state/reference already represented.

This creates a direct conceptual bridge to EGWE: **origin/history should not receive explanatory status merely because it is plausible; it must retain future-relevant information after an adequate current state is supplied.**

## Frozen empirical boundary

- **A-Islands original:** conditional concordance = **0.6177466** across 845 estimable taxa under climatic support + nearest-source conditioning.
- **A-Islands strong reference:** `C - R3 = +0.0034852` log loss, 95% CI **+0.0024664 to +0.0045082**; 341 taxa favourable, 545 adverse. Positive is adverse because lower log loss is better.
- **Tanzania:** adverse primary LOSO increment beyond a matrix-aware strong reference; spatial-block sensitivity remains uncertain.

The original A-Islands endpoint and the strong-reference endpoint are different estimands and must not be pooled as one effect size.

## Separation from EOG-WF

This repository has a **separate empirical denominator** from EOG-WF. Azores yellow eel, Louisiana King Rail, Tampa seagrass, STOC, Glanville and the post-closure NCRN programme are not replications of this paper and are intentionally excluded.

Shared EOG terminology/code provenance does not merge the scientific claims.

## Relationship to EGWE

Structural and EGWE share a higher-level principle: a candidate variable or representation must demonstrate **endpoint-relevant residual information after an explicit reference/state has been supplied**.

- Structural tests this principle for **landscape configuration under pre-existing isolation and habitat fragmentation**.
- EGWE tests it for **future-relevant eco-genetic state, origin/history and process representation**.

EGWE is conceptual/methodological context, not empirical evidence for this manuscript.

## Current state

Science and presentation are closed. Remaining work is author/admin/release/live-policy only: author metadata and declarations, tagged release, archived DOI, release-fingerprint replay, and submission-day *Ecological Informatics* checks.

## Provenance

Initial standalone migration source: `zuizui0223/eog@d7d18be0d34ba28065a947df59338e4d660a4b4c`.

The frozen scientific hard stops from the original boundary remain in force. Authoritative A-Islands outcomes must not be rerun, R3 must not be weakened, graph scales/taxa must not be retuned, and no favourable dataset may be added to rescue the result.
