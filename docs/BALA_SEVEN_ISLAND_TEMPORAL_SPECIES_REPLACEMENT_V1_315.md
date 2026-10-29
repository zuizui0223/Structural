# Structural BALA v1.314–v1.315 — Richness stability does not imply persistence of island forest assemblage composition

**2026-10-28 · Executed, source-locked seven-island multi-decade taxonomic community survey.**

**Evidence update (29 October 2026):** [v1.316–v1.317 original same-period half-sample detection benchmark and source-free audit](BALA_SEVEN_ISLAND_DETECTION_CONTROL_EXCESS_V1_317.md) now provide a stricter, source-observed ecological claim: both major guilds show more B1→B3 compositional non-similarity than within-campaign disjoint half-sample comparisons on all seven islands (Sørensen excess **+0.1908 Spiders / +0.2212 Beetles**, source site signs 26/29 and 25/26). The same-period heterogeneity is sizeable, so this is NOT an occupancy-detection corrected effect or biological extinction/colonization inference. Original v1.314 and v1.316 taxon source scorers are SEALED; further audit must be aggregate-only.

 All inference here is **observational species detection turnover**, not documented actual biological immigration/extinction. The original authors' aggregate richness/abundance stability is prior art; the independent *estimand* here is beta-diversity replacement at the exact revisited same physical forest transects.

## Research question and main new observed result

Can arthropod taxonomic membership change substantially in the same island forest, even when observed species richness changes only modestly? Does the size of the replacement component vary between spiders and beetles?

The original BALA dataset (University of the Azores, GBIF DOI [10.15468/rpdkx9](https://doi.org/10.15468/rpdkx9)) was published with **10,379 original Event rows and 63,904 original Occurrence rows**, spanning B1 (1997–2004), B2 (2010–2012), B3 (2019–2022). The published-source article is Pozsgai et al. 2024, [Scientific Data 11:368](https://doi.org/10.1038/s41597-024-03174-7). The later 2026 Pozsgai et al. [Scientific Reports](https://doi.org/10.1038/s41598-026-57146-5) already reported relatively stable aggregate arthropod abundance, biomass and richness, plus species-specific increases/declines; this was **known before** our study. The new measured quantity below is explicit **within-original-transect species replacement and net richness decoupling**, not the original published temporal-stability claim.

### Frozen physical field sampling frame, verified before opening any taxonomic response

- The original BALA Event island field uses source author codes \`FLO, FAI, PIC, SJG, TER, SMG, SMR\`, not full island names. Original v1.311 was appropriately marked **terminal** after the wrong full-name source schema excluded valid Event records. An independent author-code-corrected Event gate v1.312 was frozen before any original species values were read.
- v1.312 source-only yielded **29 original source-identical locationID transects appearing in all 3 campaigns** across **seven Azores native-forest islands**: Terceira 8, Flores 4, Pico 4, São Jorge 4, São Miguel 4, Faial 3, Santa Maria 2. Graciosa's 198 source Events occurred outside the three frozen campaign intervals and are not silently pooled.
- v1.313 froze a per-site/per-method sample-effort equalization. For every original site, each of the two fixed source methods—\`Pitfall solution\` and \`Open beating tray (with bag)\`—was represented in B1/B2/B3, and the **minimum** within-site original Event count across 3 periods was selected by original Event core-ID sorting, **before taxon outcomes**.
- This yielded **4,620 original source Events**: **1,540 per campaign**, separately **781 pitfall and 759 beating Events per campaign**. A priori source sample UID SHA256: \`39db7c6db04e022b495e233506e9c9774d8e1cf9e2e1c35830bbe6aadce9d6ac\`. Original author physical repeated-site SHA256: \`31a323a378f29e60ff656699081ccbbb47b546568f13f43e6472391adc8b7c72\`.
- The first original occurrence scoring v1.314 occurred **once**, after those source Event checks. All **63,904** original Occurrence rows were read; original Event–Occurrence join coverage **100%**. Selected group occurrences: **12,699** source guild records, **12,649** species/subspecies/morphospecies-rank accepted source records, original establishment origin category resolved for **94.56%** of accepted records. Those are *record* counts, not independent spatial replicate counts.
- Main unit of ecological inference is an original forest transect, and island-equal weighting is reported for seven island contexts. Never use 4,620 Events or 63,904 taxon occurrence rows as independent forest replicates.

## Core positive finding: observed species replacement can coexist with small net site richness change

On the *pitfall* source method, B1-to-B3 source-original same-site detected guild sets yielded:

| Original B1→B3 observational metric (seven-island equal-weight mean) | Araneae (Spiders) | Coleoptera (Beetles) |
|---|---:|---:|
| Original same-transect species-set comparisons | **29** | **28** |
| Islands with one or more valid matched sites | **7/7** | **7/7** |
| Sørensen total beta dissimilarity | **0.4697** | **0.6160** |
| Simpson turnover/replacement beta | **0.3486** | **0.5115** |
| Species changes appearing as balanced replacements rather than net change | **61.6%** | **67.9%** |
| Absolute net site richness difference | **2.07 taxa** | **2.42 taxa** |
| Signed richness B3 minus B1 | **−1.79 taxa** | **+1.04 taxa** |
| Site×guild comparisons with a balanced replacement and abs(net richness change) ≤1 | **12/29** | **11/28** |

**Crucial:** **23 of 57 observable site×guild comparisons (40.35%) show both species replacement and no more than one species of net richness change.** This is not 23 independent forest sites—there are 29 physical transects, each potentially contributing up to two guild comparisons—and it does not establish unchanged native species composition. It is a **positive original field demonstration that richness and community identity are different axes**.

The total Sørensen non-similarity \( (b+c)/(2a+b+c) \) and the Simpson replacement component \( \min(b,c)/(a+\min(b,c)) \) use \(a\) species observed in both B1/B3, \(b\) observed only B1, \(c\) observed only B3. A balanced replacement event has \(b>0,c>0\), but observation-only occurrence does **not** establish genuine biological extinction or immigrant colonization. Balanced change share \(2\min(b,c)/(b+c)\) is a different **metric** from Simpson beta, and must never be labelled an extinction/turnover *rate*.

Both source-defined guilds had **positive mean site replacement on all seven islands**. The Beetle island mean Simpson replacement exceeds Spider on **6 of 7** islands, descriptive only: one Beetle site lacked B1/B3 supported sets, source guild detection/taxonomic pool sizes differ, and there is no confirmatory guild-isolation interaction test.

## Separate prespecified method/period and nativeness context — not a new primary

- Beating versus pitfall cannot be treated as equivalent vegetation sampling. The *beating* method gave Spider Sørensen **0.3101**, Simpson **0.2114** (29 same-site comparisons), and Beetle Sørensen **0.6136**, Simpson **0.4264** (22 comparisons). Method-based guild representation and source detection explain why the pitfall method is fixed as the primary.
- B1→B2 and B2→B3 original source interval decompositions were also computed in the same one-shot v1.314 original run. These are **not comparable per-year turnover rates** because interval lengths and broad survey campaigns differ.
- Exact author \`establishmentMeans\` recognized endemic/native/introduced classes for **94.56%** of qualifying species-rank source records. Exploratory source origin decompositions in v1.314 illustrate native/endemic/introduced turnover differences but are affected by sparse per-guild origin supports. For example, the source-defined *native nonendemic Beetle* secondary had only **two** B1/B3 valid site pairs on two islands, and is **not** evidence of a seven-island origin-specific rule. Keep incomplete statuses excluded rather than imputed or renamed after outcome access.

## Why the finding matters to island ecology and conservation

**Positive observation:** Species assemblages in the same oceanic-island forest can be dynamically rearranged even if simple ecological totals are relatively stable. This makes a species-richness-only long-term monitoring metric insufficient to summarize *identity persistence*. The result is present across seven source island contexts and two biological guilds in a consistent response-referenced survey frame.

**Still unproven:** A universal rate of replacement, climatic cause, invasive taxon displacement, competitive exclusion, true persistence/survival, internal island-source recruitment, donor connectivity or successful demographic rescue. Species non-detection in B1/B3 may reflect imperfect detection, seasonal survey timing, source taxonomic identification drift and phenological or original method opportunity differences.

An important theoretical interpretation, kept as a hypothesis rather than a mechanistic empirical conclusion, is **community identity and richness are separate state variables** in island forest succession and disturbance. Conservation decisions that rely only on stable inventory richness can miss replacement of constituent species. True conservation intervention or island biogeographic mechanisms require independent environmental and repeated-survival observations.

## Strict evidence ceilings and next meaningful experiment

1. **Original population:** seven islands, 29 same-source native-forest physical transects; no other archipelago, no invented 10,379 independent sites.
2. **Sampled source:** equal **number** of original Event opportunities per site/phase/method, not guaranteed equal probability of detecting all species. Broad epochs B1/B2/B3 are discontinuous.
3. **Composition metrics:** island-equal descriptive estimates only; no causal inference, inferential p-values, false colonization/extinction claims or independently held-out island.
4. **Next unrelated field input:** a second time-series or method-compatible independent island/fragment dataset, with prespecified original site IDs and observation effort across species; preferably site-level environmental covariates and repeated detection. Do not refit threshold choices or taxonomy based on original v1.314 outcomes.
5. **Manuscript priorities:** Keep the original Structural geographic mapped-mammal mechanism scientific HOLD; **no fresh pristine confirmatory systems** were admitted, no protected original mammal/BioTIME/RLS/Macaronesia S2–S4 records were reopened, and **eBird was not used**.

## Exact reproducible record

- Source protocol: \`development/bala_longitudinal_original_source_protocol_v1_310.json\`; [first source meta-only run #40614266603](https://github.com/zuizui0223/Structural/actions/runs/40614266603) (zero Event/Occurrence data).
- Original source island-name code discrepancy: strict v1.311 remains terminal; source-corrected [v1.312 run #40615134355](https://github.com/zuizui0223/Structural/actions/runs/40615134355).
- Original source 4620 equal Events, no taxon values [v1.313 run #40615429426](https://github.com/zuizui0223/Structural/actions/runs/40615429426).
- Original one-shot observational species replacement [v1.314 run #40615946292](https://github.com/zuizui0223/Structural/actions/runs/40615946292) **SUCCESS**, four synthetic tests, exact source ZIP SHA256 \`4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2\`, aggregate artifact **12784808941**, downloaded source result ZIP SHA256 \`cb351957b5eed7d282283715017dd3e5070fe497389c49c58fab5a7c7a67d802\`, result JSON SHA256 \`b30eca5283d6984ee056ca8e74dd46fa2192c83558b175fbb84ff6546170f7a1\`.
- Frozen durable aggregate copy: \`development/bala_seven_island_species_replacement_original_result_v1_314.json\`.
- Source-free v1.315 rigorous original-source identity, 23/57 ecological claim, 7/7 guild and 6/7 guild-difference checks in \`scripts/bala_7island_sourcefree_replacement_audit_v1_315.py\` and \`tests/test_bala_sourcefree_replacement_audit_v1_315.py\`. Original Event/Occurrence rows reopened **zero** during v1.315.
- GEB mammal paper scientific HOLD remains. No eBird.

**Final claim for this dataset:** *Observed long-term taxonomic community reshuffling recurs within matching forests across seven Azorean islands, including many survey-site guild contrasts with little net richness change; this does not establish species-level survival or causal island metacommunity rescue.*
