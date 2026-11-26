# Sweden6 original author Log→Shade crosswalk found before original species data access (2026-11-19)

## New independent original-source field rule

Official SLU original dataset catalogue [10.5878/dhmc-bq15](https://researchdata.se/en/catalogue/dataset/2023-8-1) explicitly documents `specieslist_xylo.csv` author `Log` codes 1–15 and their fixed `Shade` assignment:

- **Shade 1, sun-exposed**: source Log **1,4,7,10,13**
- **Shade 2, intermediate shade**: source Log **2,5,8,11,14**
- **Shade 3, fully shaded**: source Log **3,6,9,12,15**

The field source calls each original `Block` a regional study site, each `Plot` a physical study plot and `Shade` a forest-edge **horizontal** treatment (not vertical tree height). It also states original plot code catalogue `Block 1: Plot 11–15; Block 2: Plot 6–10; Block 3: 16–20; Block 4: 21–25; Block 5: Plot 1–5; Block 6: Plot 26–30`. These are 30 **allowed code slots**, not proof all 30 original physical plots were sampled. The authors' actual 2024 paper [10.1111/ddi.13836](https://onlinelibrary.wiley.com/doi/full/10.1111/ddi.13836) explicitly says **29 physical plots** (five per region except Siljansfors four), therefore **435 placed experimental spruce logs**. Exactly which original source Plot code was not sampled remains unverified until the response-blind source ID audit.

## Scientific status and allowed use

- This rule was recovered from **publisher/archived author metadata** before any Structural process opened the 3,460 original beetle numerical biological rows, and before CTI/richness or temperature rows were opened. It is not chosen by matching observed positive ecological effects or by post-hoc selection of log numbers.
- The 7-field original beetle first header is already SHA-verified (source `Block;Plot;Log;Sampling_date;Species;Number;STI`). The `Log` field must parse into a **strict integer 1…15** with no zero, other number, missing value or silent remapping. Only then is the source-author function defined. Use **exact string `Block`, `Plot`** candidate keys and derived shade category **1,2,3**; do not infer physical plot group from log ID alone.
- Before opening any species/count/STI field, inspect **only** original nonresponse `Block,Plot,Log,Sampling_date` and climate `Block,Plot,Shade` IDs. Verify that the observed source `Block×Plot` identities fit six regions and 29 physical plots, that the actual 88 climate rows represent **87 expected plot×shade keys or explainable original source differences**, and that the source-derived log shade can join without invented absences.
- A source log/date occurrence is not a verified zero-catch trapping frame. Full 435 logs were *placed*, not necessarily represented as species-positive rows; no unsampled/non-detected log is to be treated as a true absence without original author effort.
- 2020 shade-level thermal summaries and 2021 species observations are **temporally offset**, and all resources are originally spruce; no measured absence-of-host resource, three-dimensional vertical refuge or movement operator is estimated. The 2024 parent paper already examined region, shade, CTI and composition, so a mere reproduction of those main effects is prior art.

## Historical STOPs and prospective endpoint

The original six-field species CSV gate and guessed `Block,Plot,Shade` first-three header correction remain STOP in the original audit ledger. Newly fixed source-only name-order diagnostic is a separate gate, not retrospectively relabelling failures. The **next meaningful source audit** is a one-shot, response-blind `Block×Plot×Shade` crosswalk under the original published author log mapping above; do not access biological values to rescue mismatches.

After source unit and effort verification, a distinct, preregistered and original-author-prior-art-aware **leave-one-of-six-region-out** model could compare **2020 measured under-bark temperature added beyond macroclimate + horizontal shade + bark/diameter**, for 2021 detected beetle composition. No model has yet been scored, no positive empirical effect claimed.
