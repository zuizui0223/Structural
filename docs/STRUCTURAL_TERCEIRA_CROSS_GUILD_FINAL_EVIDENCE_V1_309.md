# Structural v1.309 — Island forest community structure does not transfer uniformly across sampling frames or guilds

**28 October 2026 · Final observational evidence adjudication. Original biological observations exist; original strict and confirmatory gates are not repaired.**

## Current scientific decision

The central cross-taxon hypothesis was that shared forest structure should make arthropod assemblage turnover a transferable predictor of woody plant turnover beyond geographic distance. **That broad claim is not supported by the current independent inventories.** A small positive Beetle→Woody predictive increment on one ten-plot frame was not retained when restricting the *same original Beetle dataset* to the eight forest plots that passed an independently source-Event-defined geographic quality gate. The independent Spider guild also failed to add predictive information on the exact same eight sites.

This is a scientifically useful **boundary** on biodiversity-surrogate claims, not proof that tree and arthropod communities are unrelated or that the two excluded plots created a causal spatial effect.

## 1. Cross-taxonomic experiment in field data: what actually matches

The three source lineages are original published BioMonI 50×50 m forest samples on **Terceira**, linked by exact normalized author plot IDs and geographical Event coordinates:

- **Woody flora:** published v1.7, original 30 Event / 402 Occurrence records, of which Terceira has ten physical forest plots.
- **Beetles:** published v1.3, 308 nested sampling Event / 539 Occurrence records across Pico/Terceira; original full-method beetle effort differed 13–27 Events per Terceira plot. The original full-method comparability gate v1.298 is **TERMINAL**. An original response-blind *different* fixed subset uses three methods [1,1,4] = **6 Beetle Events per matched plot**, not the entire source sampling programme.
- **Spiders:** published v1.8, 423 Event / 1,639 Occurrence records. Author IDs match the ten Tree sites, but an Event-only audit found 27 of 260 Terceira Spider Events outside the original tree–spider 0.0003° coordinate tolerance, affecting **two** plot IDs (26 Events with systematic 0.000803° offset at one site and one 0.01144° outlier at another). Another 145 source Event dates were in day/month/year instead of year-first formatting, but source year fields were populated. The original v1.303/v1.304 **ten-plot** strict endpoint remains **TERMINAL**.

Without inspecting Spider or Beetle species outcomes, a new **post-Event-QA exploratory eight-site** design was fixed to the eight physically consistent plots. Spider mode effort was standardized to five methods [2,3,3,4,11] = **23 Spider Events per site**, **184 total**, chosen by author Event ID ordering alone.

These multiple methods and taxon observation opportunities are not equivalent, even after within-guild Event count standardization. There are only eight independent forest plots and 28 dependent plot pairs in the final like-for-like spatial comparison.

## 2. Executed original source results on a common woody response and common eight plots

The target was identical Woody taxon Jaccard pair dissimilarity, with the same original Tree coordinate-derived geographic-distance ridge reference. Eight leave-one-plot-out folds each fit on 21 training pairs among seven other sites and tested on seven pairs containing the held-out site. Tree and beetle original Event/Occurrence joins both reconciled at 100% in v1.309; the fixed eight-site geography baseline **exactly reproduced** the v1.308 Spider analysis value, avoiding accidental changes in the response or spatial population.

| Measured model/score | Original independent plots | LOPO MSE | MSE difference vs geography only | Source-label null |
|---|---:|---:|---:|---:|
| Geography only, same eight plots | 8 | **0.0135436884** | — | — |
| Geography + Beetle turnover, same eight | 8 | **0.0137215576** | **−0.0001778692** (1.31% worse) | 0.249 |
| Geography + Spider turnover, same eight | 8 | **0.0155154990** | **−0.0019718106** (14.56% worse) | 0.867 |

Both guilds' 999 label-shuffle controls permuted **independent original plot identities**, not the 28 dependent pairs. Source-label null exceeds the Spider observed gain far more frequently than the Beetle gain, but this is not evidence for a *statistically significant Beetle–Spider contrast*. The study was exploratory, the Woody target and Spider results were already exposed before the fair Beetle subset was planned, and no independent repeated island/fragment was reserved.

Additional verified field data: the eight original matched plots contain **11 Woody operational taxa** and **18 Beetle operational taxa** in the restricted six-Beetle-Event/site comparison; the latter used **48 source-Event records, containing 88 original Beetle Occurrence records**. The Spider 23-Event/site subset contained **28 operational Spider taxa** and **717 original Spider Occurrence records**. Source Event compatibility/effort was checked *before* each new taxonomic score.

## 3. Why the earlier weak positive ten-plot beetle result is not a reliable general law

The earlier ten-plot v1.300 result, under its own fixed data frame, was geography-only MSE **0.0113032821** versus geography+Beetle **0.0107459614**, a **+0.0005573207** reduction in predictive error, **4.93% relative reduction**, with original plot-label permutation exceedance rank **0.040** (999 permutations). The finite simulation precision analysis (v1.301) found an approximate Wilson interval **0.0287–0.0529** for the uncorrected permutation exceedance fraction (39/999), which crosses 0.05 and is NOT an ecological confidence interval.

Under the new common eight-plot frame, the Beetle effect changed from +0.0005573 on ten plots to **−0.0001779** on eight. As the eight-plot subset was selected solely from independent Spider source-coordinate quality, this is genuine *response-independent spatial-support sensitivity* of the original Beetle predictive claim. However, different n and geographic distributions also change LOPO training pairs. We **cannot** attribute the earlier result to a specific excluded site, state that no biological cross-taxon signal exists, or infer cause from the sign change.

Therefore the appropriate positive claim is **limited and descriptive**: in one particular ten-site forest sample, a measured Beetle assemblage reduced a geography-only Woody dissimilarity prediction error slightly. It did **not** provide a robust, portable ecological surrogate across an independently source-QA-constrained subset, and the Spider guild did not replicate the prediction gain.

## 4. Connection with the earlier Pico and trail observations — do not pool endpoints

Separate original island-vegetation studies already recorded:
- **Pico native vegetation:** history-of-local-loss native plants co-occurred with other native taxa and less often with introduced plants: binary alien-bearing-plot fraction was bounded at **31.6%–42.1%** in focal-positive plots versus **60%–100%** in focal-negative plots; other-native richness averaged **12.95 versus 4.00 taxa per plot**. These are 2013 *selected native-vegetation* associations, not a causal alien-removal or demographic rescue test.
- **Terceira/São Miguel trail flora:** four independent trails showed opposing native/introduced composition gradients; the sign of the sample mean changed from **−0.0344** for equal trails to **+0.0979** when 17 nested area-year groups were weighted as if comparable independent observations. On two trails, *relative native/introduced ratio* and *absolute indigenous richness* changed in opposite directions. This illustrates different estimands and dependent sampling, not a universally positive forest-interior effect.

These results are **not interchangeable or pooled estimates** of connectivity, colonization, or local extinction. They collectively constrain interpretations of habitat condition and community structure but cannot substitute for replicated mechanistic island ecology.

## 5. Specific next ecological evidence necessary

A credible test of a transferable spatial community filter would require:
1. **At least two independent island/fragment landscapes**, not a reweighting of these same ten original sites;
2. **Multiple physically matched forest plots within each landscape**, with georeferenced source plot identity verified before taxonomic values;
3. **Equal and documented taxon-specific survey effort** at each plot with repeated detection where possible;
4. **Independent environmental habitat descriptors and fragment membership** (canopy, forest age, microclimate, anthropogenic pressure), allowing a non-trivial habitat-only reference beyond geographic distance;
5. **A withheld source/landscape-level validation** in which neither taxon sampling, feature selection nor model parameters were tuned using the holdout community responses.

No repeated original source outcome search is justified in this cohort. The old GEB mapped-mammal paper's separate scientific HOLD and zero new confirmatory systems remain unchanged. The broad donor/rescue mechanism is still unobserved.

## Reproducibility and fixed status

- v1.305 original Event date crosswalk: [run 40610110696](https://github.com/zuizui0223/Structural/actions/runs/40610110696)
- v1.306 source-only coordinate/date quality: [run 40610499954](https://github.com/zuizui0223/Structural/actions/runs/40610499954)
- v1.307 exact eight-plot source-only frame: [run 40611215086](https://github.com/zuizui0223/Structural/actions/runs/40611215086)
- v1.308 original Spider→Woody **negative**: [run 40611772269](https://github.com/zuizui0223/Structural/actions/runs/40611772269), original artifact #12783532137; read-only verification [run 40612171049](https://github.com/zuizui0223/Structural/actions/runs/40612171049)
- v1.309 original **same-eight Beetle comparator negative**: [run 40612940936](https://github.com/zuizui0223/Structural/actions/runs/40612940936), artifact #12782549849; ZIP SHA256 `4dc86493c6baa4a235fefa2b3bae9638ef0622d980b0db48fc156416b9dd67a6`, inner JSON SHA256 `84c828861cc8a8e35f94a97a18d7a86e0d25a46164cffb279c6b7102a45d61b4`.
- Frozen original field aggregate, source identity, old STOPs: `development/biomoni_fair_eight_spatial_transfer_final_v1_309.json`.
- Original ten-site beetle result v1.300 remains intact; no data/p-value thresholds retuned to turn this non-support into a positive.
- v1.309 reopened already-exposed Woody 402 and Beetle 539 Occurrence records once under the fixed source-only eight-site protocol; **Spider original Occurrence rows reopened: zero**. All were published source records, not protected heldouts. No eBird, no original mammal/BioTIME/RLS or Macaronesia S2–S4 protected responses reopened.

**Status: the matched-guild spatial transfer branch is scientifically closed at v1.309.** The broad cross-guild conservation surrogate / causal habitat mechanism is NOT established; a genuinely independent landscape dataset is now the next evidentiary step.
