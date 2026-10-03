# Macro dual-isolation submission readiness v1.88

## Scientific state

**Analysis is frozen for submission packaging.**

No additional biological response should be opened and no new same-data mechanism, subgroup, threshold, species, block, bioregion or endpoint search is authorized.

The empirical core and evidence boundary are fixed:

- global mammals: 5,401 islands, 79 focal species, 4,126 held-out islands, 168 held-out blocks;
- primary C−R3 = −0.001814; 95% block-bootstrap interval [−0.002817, −0.000997];
- 3.77% block-weighted relative log-loss reduction at natural prevalence;
- true-absence C−R3 = −0.00580; realized-presence C−R3 = +0.11644;
- class-balanced equal-block diagnostic = +0.04941;
- ROC-AUC 0.90947 → 0.91851; average precision 0.35612 → 0.35016;
- graph-empty C−R3 = −0.00080; graph-nonempty C−R3 = −0.01411;
- external-isolation rho = +0.287; partial rho controlling graph-empty fraction = +0.286;
- within-bioregion external-isolation rho = +0.228; corresponding partial rho = +0.228;
- occupancy-breadth rho = +0.276.

These quantities are nonconfirmatory exploratory results and must retain that label.

## Submission-facing scientific message

The paper is not “connectivity improves island occurrence.”

The defensible contribution is:

> After conventional island state, generic network context, species occupancy breadth, species × regional prevalence and direct/diffuse occupied-source proximity are represented, the topology of the focal species' training-only occupied insular source network retains additional information over the naturally sparse island × species surface. That information is geographically broad but strongly asymmetric: it mainly constrains overprediction of absences and weakens with external isolation, species breadth and graph-source emptiness.

The empty-support audit additionally shows that external-isolation attenuation is not merely a proxy for graph-source emptiness.

## Evidence hierarchy that must remain visible

1. Global mammals — empirical core; large and held-out, but nonconfirmatory exploratory.
2. Historical 318-island mammals — independent nonfresh stress context.
3. GIFT fresh lane — terminal without ecological score.
4. GIFT endpoint-available subset — severe endpoint attrition; descriptive concordance only.
5. Boreal beetles — valid fresh local non-support.
6. A-Islands/Tanzania — discovery/history, not confirmation of the present principle.

## Figures

Main / supporting frozen-output figure set:

- Fig. 1: bioregion C−R3 breadth.
- Fig. 2: external-isolation attenuation.
- Fig. 3: species-breadth attenuation.
- Fig. S1: GIFT endpoint attrition.
- Fig. S2: prediction asymmetry, graph-source support and ranking diagnostics.

No figure requires reopening response data.

## Literature boundary

Verified references are in `manuscript/macro_dual_isolation_verified_references_v1_86.md`.

The manuscript explicitly acknowledges prior work on:

- multidimensional island isolation;
- stepping stones and generic island networks;
- source/species pools;
- network occupancy models;
- empirical validation of graph connectivity.

Novelty is restricted to the incremental information in the **realized occupied source topology beyond a strong source-aware reference**.

## Non-scientific items still requiring completion

These are submission tasks, not reasons to reopen the analysis:

- select the first journal;
- confirm final author list, order, affiliations and corresponding author;
- confirm funding and acknowledgements;
- confirm Data Availability wording and permanent data/code identifiers;
- confirm Code Availability / repository release tag or DOI;
- confirm conflict-of-interest statement;
- confirm generative-AI disclosure required by the selected journal;
- adapt abstract, keywords, references, headings and figure format to target journal;
- prepare cover letter;
- generate final supplement inventory and archive figures before GitHub Actions artifact expiry.

## Stop rule

If reviewers or coauthors request a new biological analysis before submission, first classify it as:

1. correction of an implementation error;
2. prespecified robustness from already frozen outputs; or
3. genuinely new post-hoc analysis.

Category 3 must not be silently inserted into the primary evidence chain.
