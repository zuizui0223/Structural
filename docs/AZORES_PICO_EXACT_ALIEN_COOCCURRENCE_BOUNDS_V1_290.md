# Structural v1.290 — Pico native-community co-occurrence: alien-plant presence is lower under every feasible original plot allocation

**2026-10-24 · Executed exact posthoc mathematics on previously published MOVECLIM 2013 aggregates only. This is an observational, within-sampled-vegetation result, not an independent biological replication or mechanism experiment.**

## 1. New science question beyond original mean richness

Previous v1.281 reported that, among 24 original 10×10m Pico native-vegetation plots, focal native plant taxa with documented local extirpations elsewhere were observed at sites with fewer alien plant species on average. But **does this imply that alien species occur in fewer plots at all**, or might the whole difference come from differences in the number of alien species per invaded plot?

The previously released source-locked v1.281/v1.282 aggregates contain enough constraints to answer without opening any original plant occurrence or site identifier again.

## 2. Immutable original-source aggregate inputs

Original MOVECLIM source: 2013 native/better-preserved vegetation plots (doi: 10.3897/BDJ.14.e178119). Historical locally extirpated Azorean taxon set: 20 species from frozen strict Well-supported local-loss S1 source (Orihuela-Rivero et al. 2025, doi: 10.1111/gcb.70072).

- **24 independent Pico plots**, of which **19** had at least one of the five sampled historical-loss-affected native taxa and **5** had none recorded.
- The island contains **11 plots with at least one recorded alien plant**.
- There were **27 alien taxon×plot positive cells**, of which **15** were in the 19 focal-positive plots and **12** in the 5 focal-negative plots. These are exactly 19×0.7894736842 and 5×2.4 from the original v1.281 archive.
- The **largest recorded number of distinct alien taxa in any single plot was 5**, with 12 distinct alien taxa in the whole original Pico survey.
- The full native taxon×plot count was **292**, split as **26 focal** and **266 other-native** positive incidences.
- Original v1.282 reported average **14.315789 native species** per focal-positive plot versus **4.0** per focal-negative plot.

Authoritative original-source GitHub Actions: [v1.281 run 39904415725](https://github.com/zuizui0223/Structural/actions/runs/39904415725) and [v1.282 run 39905350435](https://github.com/zuizui0223/Structural/actions/runs/39905350435). Retrieved and locally verified their aggregate-only JSON SHA256s: v1.281 `135a4c5f598f686ce3691d79aa0a59b427036128d8e99760321dbc3d4f208a27`, v1.282 `3ea87c240c663c9c60383c49492b03240268f8b91da313a36821264a388d476f`. The v1.290 calculations used a count-only snapshot; **zero original source data rows opened**.

## 3. Exact partial-identification proof

Let x be the unknown number of alien-bearing plots among 19 focal-positive plots, and y among five focal-negative plots.

The frozen aggregate requires x+y=11, and group-specific incidence constraints

- x ≤ 15 ≤ 5x (because 15 alien species×plot cells were recorded among the x alien-bearing focal-positive plots);
- y ≤ 12 ≤ 5y (12 cells among the y alien-bearing focal-negative plots);
- 0≤x≤19 and 0≤y≤5.

Since 12≤5y and y≤5, **y can only be 3, 4 or 5**. The total alien-bearing plots is 11, so **x can only be 8, 7 or 6** respectively.

| Mathematical scenario, NOT reconstructed field sites | Alien-bearing focal-positive plots (of 19) | Alien-bearing focal-negative plots (of 5) | Difference in co-detection fraction |
|---|---:|---:|---:|
| 1 | 6 | 5 | −13/19 = −68.4 percentage points |
| 2 | 7 | 4 | −41/95 = −43.2 percentage points |
| 3 | 8 | 3 | −17/95 = −17.9 percentage points |

All three allocations were checked by deterministic synthetic integer plot-richness vectors: each has exactly 15/12 group alien incidence counts, max five per plot, 11 total alien-bearing plots and a possible 12-distinct-alien-taxon labeling with no same-taxon duplicate in a plot. These **are not imputed actual plot observations**; they prove that no tighter bound is available from these aggregates alone.

### Confirmed additional ecological pattern

**For every possible original plot-level realization compatible with these released aggregates, the proportion of plots where an alien plant was recorded is lower in the focal-positive group.** In the original, preferentially sampled 2013 Pico native-vegetation frame:

- Alien co-detection frequency at focal-positive plots is bounded at **6/19–8/19 = 31.6%–42.1%**;
- At focal-negative plots it is bounded at **3/5–5/5 = 60.0%–100%**;
- The focal-positive minus focal-negative alien-bearing-plot frequency difference is bounded at **−68.4 to −17.9 percentage points**;
- The alien co-detection frequency ratio is bounded at **0.316–0.702**, not an extinction risk ratio.

These are **logical sharp bounds, not confidence intervals**. They do not mean that individual focal species exclude alien plants or that alien removal increases their probability of persistence.

## 4. Focal-native co-occurrence is not explained merely by counting the focal taxa themselves

At 19 focal-positive plots there are exactly 19×14.315789=272 native species×plot positive cells; 26 involve focal taxa, leaving **246 OTHER-native incidences**. Mean other-native richness at those 19 plots = 246/19 = **12.947** species per plot.

At five focal-negative plots there are exactly 5×4=20 other-native incidences, an average of **4.000** species. Ratio of their expected *within-source observed mean* other-native richness = (246/19)/4 = **123/38 = 3.237**.

Thus the strong native co-occurrence is not an arithmetic artefact from including the focal species in total native richness. Nevertheless, the 19/5 group division is outcome-defined, so broad differences in habitat quality, richness, plot sampling and species detection remain competing, non-causal explanations.

## 5. Interpretation and relation to independent sources

Combined with v1.281–v1.282, the defensible **site-level ecological pattern** is:

> In already-sampled native/better-preserved Pico vegetation, historically local-loss-affected native plants are documented disproportionately in plots containing more other indigenous taxa and a lower prevalence of alien taxa. This holds for ALIEN PRESENCE, not just alien species richness, and does not depend on assuming any unseen individual plot configuration.

It remains **one island, one 2013 selected survey system**, and the selected historical-loss-affected taxa are only five of the fixed 20 Azorean target taxa. After correction for continuous elevation and whole-community richness, the taxon-weighted alien-species-richness difference was only −0.105 (v1.282), so large focal-specific alien effects are not established.

Independent ForestEco2 2017–2018 plant plots (90 original samples across Pico/Terceira/São Miguel) yielded only 2 target native taxa and 3 focal plot positives in Pico; the predeclared two-island and six-event gate correctly STOPPED ([v1.289](FORESTECO2_INDEPENDENT_FOCAL_TERMINAL_V1_289.md)). This v1.290 arithmetic is not an independent replication.

A 2024 independent nine-island Azorean coastal plant study surveyed **231 5×5m plots** with two endemics and alien plants, showing that alien presence is widespread with/without targets and native plant co-occurrence can be focal-species dependent (doi: 10.1186/s12862-024-02300-8). The authors explicitly say their raw analytic dataset is **available only upon reasonable request**; their published findings are contextual prior work, not an independent pooled effect size or new Structural replicate.

The 2026 Red List reassessment of **94 Azorean endemic vascular taxa** found 50 threatened of 82 non-DD taxa and uncovered unprotected hotspots (doi: 10.1038/s41598-026-52252-w). Precise species locations are withheld for conservation. These studies support the value of multi-island habitat conservation tests, **not** causal donor/rescue status of Pico or any scored replication of v1.290.

## 6. Where to stop, and what observation could actually establish the proposed mechanism

- The present within-Pico **occurrence pattern** is confirmed under exact aggregate bounds.
- **Not confirmed:** causal invasive competition, native-species facilitation, historical refuge persistence, successful immigrant establishment, donor viability, extinction reduction, or generality across islands.
- A future genuinely independently sampled test needs fixed 10×10m-type plot identity and equal/modeled effort across ≥2 distinct islands, at least two originally defined focal taxa per relevant landscape, and a measured habitat/alien-pressure gradient plus repeated species-specific detection. Pre-define the native-community reference and the total-richness adjustment before the future biological endpoint opens.
- Do not reuse the original 24 Pico records or the consumed ForestEco2 test under a new cutpoint. Do not equate difference in alias co-detection with removal intervention benefits. eBird remains off.

## Executed provenance

- Freeze contract: `development/azores_pico_alien_binary_partial_id_protocol_v1_290.json`.
- Aggregate input: `development/azores_pico_source_aggregates_v1_290.json`.
- Exact solver and synthetic witness construction: `scripts/azores_pico_alien_codetection_bounds_v1_290.py`.
- Four targeted regression tests: `tests/test_azores_pico_alien_codetection_bounds_v1_290.py`.
- [**GitHub Actions run 40070958998: SUCCESS**](https://github.com/zuizui0223/Structural/actions/runs/40070958998), **4 tests passed**. Original-source plant files read: **0**.
- GitHub Actions aggregate output artifact ID **12551097719**, ZIP SHA256 `ba1b35b3980990b9b46715addd1cb53f20a532edffd54b289a1762e79ac15d02`.
- Original GEB mechanism scientific HOLD remains; new confirmatory systems **0**; original 529 mammal, BioTIME, RLS, Macaronesia S2–S4 protected response data unopened.
