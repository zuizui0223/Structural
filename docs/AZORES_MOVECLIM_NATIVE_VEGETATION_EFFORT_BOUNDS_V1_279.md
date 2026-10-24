# MOVECLIM × Macaronesia S1: native vegetation concentration on Pico survives equal plot effort (v1.277–v1.279)

**2026-10-23 | Completed, published-source observational case comparison. Ecological mechanism remains unconfirmed.**

## Biological question

Do Azorean vascular plants whose conspecific island populations have documented **Well-supported** local extirpations show a spatial concentration in the remaining sampled native vegetation, and could an apparent Pico island richness surplus be entirely due to its larger number of plots?

Sources: Andrade et al. MOVECLIM–AZORES standardized 2013 native/better-preserved vegetation plots, [DOI 10.3897/BDJ.14.e178119](https://doi.org/10.3897/BDJ.14.e178119), original [GBIF dataset f92047fa-f2cb-445d-9a93-546d637b2820](https://www.gbif.org/dataset/f92047fa-f2cb-445d-9a93-546d637b2820); Orihuela-Rivero et al. 2025 CSIC local extirpation data [10.20350/digitalCSIC/17024](https://doi.org/10.20350/digitalCSIC/17024) from the original Global Change Biology paper [10.1111/gcb.70072](https://doi.org/10.1111/gcb.70072). This analysis combines published sources; previous literature findings are prior art.

## 1. Actual standardized biological source

The source-locked [MOVECLIM schema verification](https://github.com/zuizui0223/Structural/actions/runs/39890218337) established ZIP SHA256 `612dad4edc1a5fb8e9fd057167320144d8a7791a02d1245513d58fd6c8cdabc4`, exact 111,299 bytes, Event core/Occurrence extension with original source coreid linkage. The independently frozen source design is `development/azores_MOVECLIM_2013_refugia_design_v1_278.json`.

The original [2013 field execution](https://github.com/zuizui0223/Structural/actions/runs/39890938835) passed the test suite and reconstructed **232 sampled 5×5 m subplots nested within 58 author-defined independent 10×10 m plots**, plus **2,539 Occurrence records** and 746 native/endemic species×plot positive cells. Exactly 20 historically local-loss-affected Azorean taxa were fixed from CSIC S1 before comparing to the MOVECLIM observations.

| Island | Independent plots | Historical local-loss-affected native taxa documented in standardized 2013 plots | Positive focal taxon×plot records | Other native taxa |
|---|---:|---:|---:|---:|
| Pico | 24 | **5** | 26 | 49 |
| Flores | 10 | 1 | 7 | 40 |
| São Miguel | 12 | 1 | 3 | 44 |
| Terceira | 12 | 1 | 9 | 38 |

All five affected taxa documented in the 2013 standardized native vegetation program were recorded on Pico (the same taxa may also occur on other islands). **None** of the source-verified 24 S1 historically lost taxon×island pairs coincided with a 2013 native-plot positive on that very island. These are positive, habitat-limited sample observations; no absence outside the sampled plots is inferred.

## 2. Weak within-Pico elevation contrast

Within each island, plot median elevations were converted to fractional rank. For Pico, five affected native taxa had mean detection-plot rank **0.4138**, versus **0.3802** for 49 other native taxa: a small descriptive difference **+0.0336**. The other three islands have only one affected detected taxon each and do not satisfy the frozen >=2 affected taxa per island comparison gate. **A strong high-altitude-specific concentration is not supported by this contrast.**

## 3. Nontrivial positive result from exact, response-free equal-effort bounds

After these observational outputs were frozen, a separate source-free [v1.279 analysis](https://github.com/zuizui0223/Structural/actions/runs/39891800548) asked if the 5-versus-1 difference could be completely explained by Pico's 24 plots versus 10–12 plots on the other islands. No taxon name, site ID, native-plot row, or previously held biological response was re-opened.

Fix a simple random sample of **m=10 plots without replacement** among the original plots per island. If a taxon is on k of N original plots, its probability of inclusion in this sample is:

\[P(\text{detected among }m)=1-\frac{\binom{N-k}{m}}{\binom Nm}.\]

For T taxa and P total species×plot positive cells, each unknown per-taxon occupancy satisfies 1<=k_i<=N and sum k_i=P. The inclusion function is increasing and discretely concave in k, so the **minimum** of expected observed taxa concentrates observations maximally among a few taxa, and the **maximum** distributes them evenly. Exact Fraction arithmetic and exhaustive small-N integer composition tests validate both bounds. These are mathematical constraints on expected rarefied richness, not confidence intervals or p-values.

For Pico, N=24, T=5, P=26. The most uneven feasible occupancy vector (22,1,1,1,1) gives a guaranteed E[S10] lower bound **8/3=2.6667**. The most evenly distributed vector (6,5,5,5,5) yields E[S10] upper bound **25115/5244=4.7893**.

| Island | Expected historical-loss-affected native taxa from 10 plots: exact lower–upper |
|---|---:|
| **Pico** | **2.667–4.789** |
| Flores | 1.000 |
| São Miguel | 1.000 |
| Terceira | 1.000 |

All three other islands had only one recorded focal species; 10 of their 10/12 original plots suffice to include that documented species under all possible case-species plot allocations with source-positive totals 7/3/9. Thus the **minimum Pico expected richness exceeds every other island's maximum** at matched plot number by at least **1.667**. The m=8 sensitivity is similar: Pico lower 2.333, and others at most 1.000. This rejects the very limited null that the difference is solely a simple higher count of source survey plots, conditional on the existing nonrandom vegetation-plot sampling frame.

Reference native richness was also bounded without taxon IDs. The ratio of separately **expected** loss-affected to total native species richness at m=10 is at least **5.346% on Pico**, whereas the maximum corresponding ratio across the other three islands is **2.927%**. This is the **ratio of expected richnesses**, not an expectation of the per-subsample ratio; it does not account for habitat selection, endemism/area differences or historical range breadth.

## 4. What this result means ecologically

The directly supported, new combination-of-public-data observation is that **historically local-loss-affected flora is more concentrated in Pico's sampled, relatively intact native vegetation even after conservative equal-plot-effort bounds**. Since within-Pico elevation ranks do not show a large difference, the specific hypothesis 'the focal taxa are restricted to the highest plots' is not supported. A broader mechanism involving available intact habitat mosaics, elevational range, historic range breadth or natural community composition remains a testable alternative.

**Not supported:** Pico was a historical donor or migration/rescue source for other islands, measured 2013 reproductive population persistence, true local loss risk, species extinction synchrony, or causal benefits of reserve placement. MOVECLIM surveyed relatively good native habitat along different island gradients and did not sample all human-modified lowlands. Its native species list is not a whole-island at-risk denominator. Uniform random plot rarefaction describes a mathematical resample of *this original frame*, not a randomized island habitat survey.

## Reproducibility and evidence hierarchy

- v1.278 biological results: `development/azores_MOVECLIM_2013_native_plot_field_result_freeze_v1_278.json`; [success run](https://github.com/zuizui0223/Structural/actions/runs/39890938835), result artifact 12474287889, SHA256 `06865157d918b86ef0645bafee3cde9d9857d3ba28c222a56412af7651244ba9`.
- v1.279 only uses committed aggregated input: `development/azores_MOVECLIM_2013_rarefaction_bound_contract_v1_279.json`, `scripts/azores_MOVECLIM_2013_rarefaction_bounds_v1_279.py`; [exact-source-free run](https://github.com/zuizui0223/Structural/actions/runs/39891800548), artifact 12475136151, SHA256 `4dbf4273ee6ae6cf7f61af500605999f6dd2d34c7a4ce566093f9b34252af44c`.
- v1.279 input and artifact contain no raw taxa, coordinates, habitat visit IDs or biological observations; no field source was re-downloaded.
- Macaronesia S2/S3/S4 still protected; original mammal/BioTIME/RLS protected outcomes not revisited. No eBird, zero new pristine confirmatory systems, GEB scientific HOLD unchanged.
