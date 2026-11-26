# Pre-response source-label correction for conditional beetle richness LOPO

Earlier frozen endpoint docs/FOREST_FALCONI2026_POST_EMERGENCE_RICHNESS_LOPO_FREEZE_20261122.md described host-factor labels by informal author R names (Cacao, Fernan, Guaba, Mascarei, Sapanillo), which are NOT literal source CSV values.

The **actual author PlotLogSpeciesAbundancesDensity.csv strings** were independently source-audited previously and rechecked by parsing ONLY Plot/Host original fields, BEFORE the new per-log Spec outcomes were read: **CACAO; FERNAN SANCHEZ; GUABA; MASCAREI; SAPANILLO** (300 unique Plot×Host rows, 59 complete five-host physical plots, 1 four-host and 1 one-host plot). The first new executable run stopped at this source-label mismatch with status SCIENTIFIC_OR_SOURCE_STOP_BEFORE_PREDICTION, and no original Spec values, model fit, or ecological scores were computed.

**Change only this literal source-label gate** from informal names to exact five author CSV strings. Retain exactly the earlier 59 complete sites/295 log records, source gate, response (log1p(Spec) conditional Indiv>0), baseline E0 incl. log1p(Indiv), E1 plus Host, Ridge alpha 10, 59 LOPO folds, plotting/inference equal weight, 4,000 bootstrap/9,999 signflips seed 20261122 and preregistered acceptance rule. Do NOT reselect response, exclusions, covariates or endpoint based on Spec results.

This is a **pre-response codebook correction**, not a post-hoc selection of favorable labels. The original document remains on the branch as immutable evidence of the initial mistaken label claim. The study is retrospective/outcome-exposed and cannot be promoted to new confirmatory replication.
