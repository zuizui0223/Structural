# Forest beetle resource transport: original Traylor 2026 4-study heldout any-emergence result

## Scientific decision — original source one-pass executed

**Within one published four-component-study ambrosia-beetle dataset from two southeastern USA areas, measured coarse deadwood properties did NOT transportably predict whether any adult ambrosia beetles emerged from an entirely unseen source study.** The frozen resource model performed WORSE than a source-study-independent pooled-training-prevalence reference in 3 of 4 held studies. This is **retrospective, original published source, conditional out-of-study prediction NONSUPPORT**, not evidence that wood substrate properties have no causal biological effect, nor a novel test of native/non-native competition.

Original source paper Traylor et al. (2026), *Proceedings of the Royal Society B*, DOI 10.1098/rspb.2026.1825, ALREADY published native/non-native co-occurrence and competition, wood volume/time/tree origin associations, and leave-study-out sensitivity. All that biology is PRIOR ART. Structural's different endpoint is any observed adult emergence predicted in an *entirely unseen original field study*, not species composition, larval colonization, or native/exotic competition.

## Immutable input and pre-original-outcome freeze

- Official Zenodo concept DOI 10.5281/zenodo.19206036 is linked by publisher to version DOI 10.5281/zenodo.19206037, original license CC BY 4.0. Three exact author files, original authenticated MD5: ambrosia per deadwood object data.csv 40,282B MD5 586df99f7faded8796d26d4143058883, ambrosia beetle competition script.R 20,797B MD5 05dccb112e503f6436e9fd4641079c8b, READ ME.txt 1,752B MD5 c12653c9488fd7b9254ec4a086ce218b.
- RESPONSE-UNOPENED source QA [GitHub Actions #45081609029](https://github.com/zuizui0223/Structural/actions/runs/45081609029) independently certified exactly 356 sampled/reared deadwood object records from **four original field studies** with sample sizes **48, 64, 100 and 144**, 23 wood substrate tree taxa (7 shared across two or more studies), 2 tree origin classes, original time in field 1–13 months, volume 0.003756–0.086011 cubic metres, and complete numeric nonresponse source fields. All 356 physical records represent author-sampled wood objects, NOT 356 independent forests.
- Frozen prespec BEFORE original numerical beetle response scoring: [FOREST_TRAYLOR2026_ANY_AMBROSIA_EMERGENCE_LOSO_FROZEN_20261123.md](FOREST_TRAYLOR2026_ANY_AMBROSIA_EMERGENCE_LOSO_FROZEN_20261123.md). Four holdouts each remove one entire original field study. E0 is study-equal average of smoothed positive emergence prevalence among the three training studies; E1 is logistic regression C=1.0 (L2, lbfgs, original study-equal training weights) with original log wood volume, log1p field months, tree type and tree origin, fitted/scaled/encoded TRAINING ONLY. No taxon-specific substrate-tree name, row number or held-out study identity predictor, no model/loss/threshold tuning after results.
- Source-author event integrity check PASS: exactly **141/356** original recorded objects have (native + nonnative group adult abundance)>0. Original native/exotic abundance and presence indicators and total counts satisfy the fixed source consistency checks; no missing source outcomes converted to zeros. Recorded zero means **no adults emerged under source sampling**, not proof of failed colonization.

## The one actual original data result

Original one-shot [GitHub Actions #45081945229](https://github.com/zuizui0223/Structural/actions/runs/45081945229) **technical SUCCESS, frozen ecological scoring completed**, original aggregate-only artifact #14778095411, artifact ZIP SHA256 **5755ddc6b790d4d9dc697dec66dfa02f757274a1b41d50f317c9fb6d217d3561**. No original rows, source study names, specimen IDs, tree-taxon identities or biological files exported.

| Primary four-study equal leave-study-out log-loss metric | Observed result |
| --- | ---: |
| Original source studies held out | **4**, sample n=48/64/100/144 |
| Source objects with observed emergence / sampled | **141 / 356** |
| E0 pooled-training-prevalence reference log loss | **0.6797833892** |
| E1 + wood-resource properties log loss | **0.9535478535** |
| **Primary D = E0-E1** (positive means predictive gain) | **−0.2737644643** |
| E1 relative error increase compared with E0 | **+40.2723%** |
| Original study groups with E1 improvement / worsening | **1 / 3** |
| Sorted four anonymous original study gains (NOT study-indexed) | **[−0.854705, −0.272811, −0.064827, +0.097284]** |
| Source-author positive counts per original study, sorted WITHOUT linkage to study n | **[9,15,41,76]** |
| Predeclared 4,000 study bootstrap 95% percentile CI for D | **[−0.657235, +0.016229]** |
| Exact all 2^4=16 signed study-vector two-sided p | **0.375** |
| Minimum possible exact two-sided study-level p with 4 groups | **0.125** |
| Scientific classification | **OBSERVED TRANSFER PERFORMANCE WORSE, RESOURCE GAIN NOT SUPPORTED** |

The group-level population uncertainty is extremely wide, and the exact signflip p does NOT establish a population effect (adverse or favorable). E1's poorer performance suggests that the resource coefficients learned in three source experiments do not carry over reliably to a fourth source experiment under this fixed learning, scoring and observation operator; it does NOT show that resource availability is irrelevant biologically. Different study substrates, environmental contexts, emergence opportunities, and source pools can cause instability. Those mechanism candidates are **NOT separated or tested** by this outcome.

## Importance for the broader forest programme

- The source provides an authentic held-study-out counterexample to assuming that within-site substrate associations automatically become transferable predictive rules. This is a METHOD-QUALIFIED negative predictive result, not absence of beetle ecology and not a universal ecological law.
- Prior outcome-exposed Ecuador 59-plot host-label emergence difference Q=24.301, Monte Carlo p=.00005, remains LOCAL exploratory association; its host-added LOPO emergence (p=.0906) and post-emergence richness (p=.6333) remain UNSUPPORTED. Germany Chiu offered host within-one-forest six-plot composition gain and Finland guild within-country deadwood gain are different response ontologies, reference models, source dimensions and independent units. No meta-average or simplistic contradiction is valid.
- Cours 2026 original 98 analytical records are nested in three differing forest/protocol contexts with only two source site labels each and different trapping methods; these are not 98 independent forest population replicates. Its source original author richness/SEM effects remain prior art. That source has not produced a new resource prediction.
- Any ecology claim of RESOURCE STATE GATING or forest-wide geometric niche prediction still requires independent, multiple source programmes with comparable original sampling effort, resources, beetle species/guild ontology, and precommitted heldout evaluation. More data and actual source dynamics are needed to separate resource accessibility from observation bias.

## Reproducibility and protected scope

Implementation: analysis/forest_macro_global/traylor2026_any_emergence_loso_onepass.py. Original outcome scored ONCE after method freeze. Source files were ephemeral in Actions runner and NEVER uploaded/committed. Future workflow should only run known-truth synthetic tests, not original responses. No protected PREDICTS/Finland/Chiu/Carpathian/NEON/BETA-FOR/BALA/GEB/mammal biological source reopened; no eBird/TinyFish. Existing Structural PR #469 remains Draft/unmerged.
