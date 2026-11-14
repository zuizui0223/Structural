# Forest environment × contemporary assemblages — 2026-11-06

New exploratory environmental analysis, not independent confirmation or a rerun of the sealed BALA temporal/spatial endpoints. PR461 manuscripts/scorers remain unchanged; work continues in PR469.

## Units and outcomes
Use original Event start years 2019–2022 from SHA-locked BALA1.0 and SLAM1.7 and the completed WorldCover2021 plot ledger. Join original Event core IDs, then exact dataset/island/location IDs; no spatial-ID merging or pooling different source methods.

Primary taxonomic pool: named species/subspecies of Arthropoda. Distinct source scientificName within each Event; duplicate specimen records are not additional taxa. Outcomes: all named taxa, endemic, native non-endemic, introduced, and endemic-minus-introduced richness difference. Unclassified origins and higher ranks audited, not recoded as native. Conflicting origin assignments flagged. Events without any source-linked records do not establish true biological zeros.

BALA pitfall/foliage analyzed separately: incidence rarefaction across source sampling Events to metadata-only minimum23 pitfall /10 foliage Events per plot. Flag insufficient samples after Event linkage. Sampling opportunities are not independent forest sites or equal detection probabilities.

SLAM quarterly records: primary60–120day duration, selected without taxonomic values; each site total weight1. Outcome distinct species/Event, not species/day. Log(days/90) is an estimated covariate, not an abundance offset. All positive durations retained as a sensitivity.

## Model fixed before new response extraction
Primary exposure: WorldCover2021 tree-class area fraction within500m, coefficient per20 percentage points. Primary15 coefficient tests:3 collection channels ×5 outcomes; show unadjusted p and Benjamini–Hochberg q. Native origin is not equivalent to forest specialization.

BALA ordinary least squares on rarefied richness, island fixed effects and elevation/200m. SLAM weighted least squares with island, start-year and midpoint-quarter fixed effects plus elevation and log(duration). Cluster covariance by source forest-fragment/area labels, small-sample correction and cluster-based t degrees of freedom. Report model rank and support; finite clusters do not guarantee unbiased inference. No assumption that different datasets are geographically independent.

Planned descriptive sensitivity:100/1000m tree area;500m tree+shrub area;45m positional min/max; log1p outcomes; leave-one-fragment and leave-one-island coefficients. Source native/mixed/exotic habitat label and BALA sampling month/host-code diversity as additional conditional checks. These do not rescue a failed primary test or establish causal independent habitat effects.

Report full results, including null/negative directions, cluster counts, source coverage and comparison failures. Do not call old-source repeated records independent replications. Near-contemporaneous2021 cover is not historical cover; tree class area is not canopy closure/height/native forest.

## Execution
The extraction script reads the two public archives once in its job, retains only response rows joined to2019–2022 Events, and writes a reusable selected-response artifact. Archived original source scores are not invoked. Save provenance, exact source/filter counts, sample and plot responses, analysis code and all model tables. Manuscript author emails/submission actions are outside this task.
