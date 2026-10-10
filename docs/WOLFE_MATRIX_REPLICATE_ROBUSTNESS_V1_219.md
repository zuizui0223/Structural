# Wolfe v1.219 — matrix concentration and replicate-matching stress test

**Evidence class: post-outcome explanatory diagnostic only.** We must not promote a narrow observed 6-patch heterogeneous low-versus-high local corridor result to a general law that greater connectivity reduces coexistence. Wolfe et al. (2022; Oecologia, DOI 10.1007/s00442-022-05178-9) already discussed offsetting benefits and costs of corridor dispersal and guild-dependent response. Thus this analysis is a robustness/interpretation audit of v1.217/v1.218, not a pristine hypothesis test.

Frozen comparison remains *day 21 joint Stentor and either Didinium/Dileptus presence within the same landscape-level microcosm*. Six patches, heterogeneous (12/12/12/4/4/4 ml) and homogeneous (8 ml × 6) use equal total volume, but 4-patch heterogeneity is 16/16/8/8 ml and has lower relative inequality. Do not call a 4 vs 6 difference a pure patch-count effect.

## Three matrix strata must ALL be reported

| Six-patch heterogeneous matrix stratum | low corridor joint positives | high corridor joint positives | low−high bounds as proportions of four intended units |
|---|---:|---:|---:|
| none | 0/4 | 0/3 | [-.25,0] |
| low | 3/4 | 0/4 | [.75,.75] |
| high | 1/4 | 0/4 | [.25,.25] |

The equality of *aggregate* high-corridor joint positives to zero is descriptive and does not show where within-patch failure occurred. All missing binary results are bounded adversarially, rather than coding non-observation as ecological extinction.

The posthoc **leave-one-matrix-out** sensitivity of the six-patch heterogeneous low-minus-high joint contrast is:
- drop matrix **none**: +50 pp;
- drop matrix **low**: **0 to +12.5 pp**;
- drop matrix **high**: +25 to +37.5 pp.

The largest single matrix treatment contributes three of the four observed low-corridor joint-positive microcosms. Removing it allows *zero* difference under one completion of the unobserved high-corridor replicate. This is evidence **against a broad uniform-matrix mechanism claim**.

## Replicate-identity check, not a randomized trial reanalysis

Matching identical `replicate` IDs within the three matrix strata of the 6-patch heterogeneous experiment, 11 low/high pairs are observed: four have joint positivity on the low-corridor side only, zero on high only, seven ties. An **assumed** within-pair exchangeability model gives exact two-sided sign probability `p=0.125`. If the missing high-corridor experiment is completed as joint-positive, one discordance reverses and the hypothetical probability becomes `p=0.375`; if completed as joint-negative, `p=0.125`. This is NOT a valid randomization p-value unless treatment exchangeability conditional on replicate is verified from original design, nor a predeclared statistical hypothesis. The missing high-corridor J is not a new observed measurement.

Authors' reported overarching predator responses and the possibility of tradeoffs already exist. Our narrower descriptive endpoint does not establish dispersal-mediated competition, invasion, predation or colonization, and original Structural GEB science remains on HOLD. A mechanistic next step requires an independent repeated/blocked factorial experiment with patch-level spatial dynamics, varying corridor frequency crossed with patch-size variance at fixed total area and species interaction measurements, plus pre-registered multi-guild persistence as a primary endpoint.
