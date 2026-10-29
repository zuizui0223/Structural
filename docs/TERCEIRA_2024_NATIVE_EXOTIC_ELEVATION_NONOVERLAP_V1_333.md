# Structural v1.333 — 2024 Terceira forest type is completely confounded with elevation

**29 October 2026. Original 2024 field Event values were checked once, and species outcomes remain sealed. Scientific status: `TERMINAL_2024_FOREST_ELEVATION_NO_COMMON_SUPPORT`.**

## Central result and why it matters ecologically

A native forest can contain more endemic species than an exotic forest because of the vegetation itself, **or** because the two forest types occupy different environments where different species are naturally found. These are distinct causal explanations. An apparently balanced **10 native / 10 exotic forest plots** is not by itself a balanced ecological comparison.

The 2024 Terceira survey provides an especially clear counterexample:

| Original 2024 Terceira source observations | Native forest | Exotic secondary forest |
|---|---:|---:|
| Original independently identified forest sites | **10** | **10** |
| Source plot elevation range | **590–927 m a.s.l.** | **256–461 m a.s.l.** |
| Original sites with ground-level SLAM traps | **10** | **10** |
| Original sites in same elevation support as the other type | **0** | **0** |

There is a **129 m elevational gap** between the highest exotic plot and the lowest native plot. There is **no shared elevation region at any observed original site**. Any native-versus-exotic forest model fitted to this cohort would have to extrapolate from native plots in a higher montane region to exotic plots at lower elevations (or vice versa). Even when a standard GLM provides a habitat coefficient, the separate effect of habitat type is not identified by within-elevation comparisons in these data.

This is why the source originally identified by [Lhoumeau & Borges, *Forest Ecology and Management* (2025), DOI 10.1016/j.foreco.2025.123059](https://doi.org/10.1016/j.foreco.2025.123059) cannot independently validate a causal forest-type effect on endemism. Its published vertical-stratification and source species-origin findings are prior art, not new Structural discoveries. Another published 2025 study, [*Beyond native habitats: Indigenous arthropods adapted to mid-elevations find refuge in exotic forests*](https://www.sciencedirect.com/science/article/pii/S2351989425005372), already emphasized elevation as a dominant predictor and showed that some indigenous mid-elevation arthropods occur in exotic forest. This provides an ecological reason to be especially cautious about calling exotic forests invariably inhospitable for every indigenous species.

## Executed original-source gate

**Original dataset:** [*Stratified sampling of Azorean forest arthropods*, DOI 10.15468/7aue4t](https://doi.org/10.15468/7aue4t), original fixed version v1.6 (2025-03-28), ZIP SHA256 `c4dcf060bc2554be7fe49fb569f2fd7a8514ba3a888db673b40cb65aad60ef21`. Official original source **326 Event rows / 2,399 Occurrence rows**. The original field campaign ran in summer 2024. The authors sampled up to three SLAM trap heights (GRD/UND/CAN) and supplemented with ground Pitfall traps (EPI). These capture channels are not interchangeable.

- **v1.332 metadata-only:** [GitHub Actions #40841670131](https://github.com/zuizui0223/Structural/actions/runs/40841670131), three synthetic tests PASS. Original source ZIP directory and `meta.xml` verified a source `locationID`, explicit `habitat`, `minimumElevationInMeters`, `samplingProtocol`, Event remarks and Occurrence `establishmentMeans`. No original Event or Occurrence data rows opened.
- **v1.333 Event-only original environmental overlap:** [GitHub Actions #40842289055](https://github.com/zuizui0223/Structural/actions/runs/40842289055), six synthetic tests PASS. All **326 original Event** rows read under exact source SHA. Source plot count **20**, native **10**, exotic **10**; both habitats had all **10 ground-SLAM source plot IDs**. Original elevations: native **590–927m**, exotic **256–461m**. The original physical site×forest elevation common-support interval was **empty**. **All 2,399 original arthropod Occurrence/source origin records remain unopened**.
- The original scientific STOP does not change the earlier source-neutral study design or allow a later species-informed "matched" subset; a zero-overlap ecological exposure cannot be corrected by arbitrary regression terms or propensity reweighting.

## Interpreting the earlier positive SLAM origin-habitat observation

The separate SLAM 2012–2022 archive (three eligible Azorean island cohorts, source-scored and sealed at v1.328) found the source-observed **endemic arthropod richness native-minus-mixed/exotic +2.335 species per sampled Event**, **introduced richness −2.515**, and **non-endemic native richness −0.852** (three islands equal-weighted, original matched source campaign strata). These are *real descriptive observational contrasts* and remain useful.

They do **not** demonstrate that changing forest type at the **same elevation** would cause these differences. The old SLAM source is a different original field panel, but the new 2024 Terceira balanced forest sample cannot repair this key causal gap because its native and exotic original sites live at disjoint elevations. One must not claim "SLAM endemics are preserved *because of* native forest" without a design with environmental overlap.

## Specific future evidence necessary (no more response-chasing in this original source)

**Prospective environmental-overlap gate:** before any species sampling or outcome exposure, document at least **two independent native and two exotic/mixed forest plots within each of two jointly sampled elevation bands**, same island and source campaign, and record vegetation composition, forest history, altitude, canopy structure, disturbance, ALAN/light exposure, method and effort. If the ecological landscape has no native/exotic overlap at any relevant elevation, use an explicitly different *restoration before–after / matched reference* design or study the **combined vegetation-and-elevation habitat gradient**, never a falsely identified independent vegetation effect.

**Response:** named endemic, native nonendemic and introduced species richness **separately**, plus local composition similarity, per original source plot and equal trap source method/height. A claimed forest-type mechanism must outperform an elevation/fragment/environment-only predictor out-of-site; plot/detection replicates are nested within physical habitat plots, not independent forests.

**Scientific ceiling:** This does not test actual individual immigration into forests, persistence, colonization, local extinctions, causal impacts of invasive plants, island isolation or metapopulation rescue. Native forest/endemic conservation remains important, but landscape-specific native-versus-exotic observations need environmental design support.

No BALA, older SLAM, PRIBES, Madeira or global mammal original species data were reopened. All older original one-shot scorers remain sealed, mapped-mammal GEB SCIENTIFIC HOLD and zero pristine confirmatory admissions unchanged. No eBird and protected original mammal/BioTIME/RLS/S2–S4 biological files unopened.
