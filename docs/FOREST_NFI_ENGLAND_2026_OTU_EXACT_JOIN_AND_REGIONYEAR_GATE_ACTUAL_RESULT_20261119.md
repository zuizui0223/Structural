# Forest macro England NFI2026 — exact 316/316 eDNA sample header linkage, 77 paired source plots, strict cross-method ecological gate STOP (2026-11-19)

## Actual final decision in the frozen England NFI source lane

**Source sample–OTU column linkage is fully verified, but the prospectively frozen cross-method local community fingerprint biological endpoint is SCIENTIFIC STOP before reading original OTU data rows.** An original `NFI_region × Year` source stratum contains fewer than two eligible plot/year contexts, so exact same-region/same-year label randomization is not estimable over all 77 precommitted matched plot-years. Do NOT modify the grouping, delete singletons, pool years or regions, score another alpha/beta endpoint, or present a false ecological null/positive result. This is a **sampling-network exchangeability limitation**, not evidence that no local forest source pool signal exists.

UK Forestry Commission publisher [NFI Canopy & Subcanopy Arthropod Communities](https://environment.data.gov.uk/natural-capital-ecosystem-assessment/search/2b8a8f17-3745-43d1-bb32-0d509230f158), official original 2023–26 ZIP fixed at **486883 bytes**, SHA256 **`ce3a21377238cc87bde7683917f59a771d20f8e24e81ddf47915362b92281ff4`**. Data year values in this exact publication are **2023:95 sample rows, 2024:116, 2025:120, 2026:0**; title is program range, not 2026-observed samples.

## Verified original field/source completeness

[Source method paired actual result](FOREST_NFI_ENGLAND_2026_ORIGINAL_METHOD_PAIRED_SOURCE_ACTUAL_RESULT_20261119.md) had independently authenticated:
- **331** unique original `Sample_ID` metadata rows; 83 original `(NFI_region,Plot_ID)` candidate field plot keys across 8 region labels, **83/83** `Canopy` (Lindgren by original publisher) vs `Malaise` method pairs with source original deployment period overlap; **77/83** with DNA-sequenced samples in both methods and matching deployment dates.
- Two original `Trap_type` codes **Canopy 166 / Malaise 165**. They are DIFFERENT sampling technologies, inseparable from layer. Only **3/83** candidate original paired sites have numeric heights for both types and **0/3** show uniformly higher Canopy trap height. No actual 3D thermal/resource vertical inference is possible from this data alone.
- Original paired units per year 2023 **24**, 2024 **29**, 2025 **30**, across 8 regions. The 331 metadata rows are NOT 331 independent ecosystems, and 885 original valid deployment rounds are NOT 885 sites.

New [original 328-header source crosswalk #44448637232](https://github.com/zuizui0223/Structural/actions/runs/44448637232) **SUCCESS**, anonymized original artifact **#14494791585**, ZIP SHA256 **`4dcc21733fb8ab50ef00b3a2f65383f583a3d4631b8753617b911286878fd07d`**:
- Exact 328-header field count, **328 unique**, **0 duplicates**.
- **316/316** original `Sample_sequenced=yes` `Sample_ID` strings match exactly to a unique source 328-wide header; **0** yes missing, **0/15** source unsequenced samples erroneously matched.
- **12** non-sample source fields, of which 1 header name consistent with DNA sequence and 8 with taxonomic rank, 2 with IUCN/invasion status; no raw field names, OTU names, species or original sample IDs exported.
- All **77/77** original DNA-sequenced and concurrent Canopy+Malaise candidate annual plot contexts retain an exact response column header for each method. Regional/year breakdown: 2023 **24**, 2024 **23**, 2025 **30**; eight NFI region labels remain, anonymously 5,5,7,8,10,12,13,17 matching contexts by region.
- **ZERO original 328-field biological table data rows opened** during this actual source crosswalk.

## One frozen ecological attempt, scientifically blocked pre-response

Original single fixed protocol [cross-method local OTU signature prespec](FOREST_NFI_ENGLAND_2026_CROSS_METHOD_LOCAL_OTU_SIGNATURE_EXPLORATORY_ONEPASS_PRESPEC_20261119.md) was committed BEFORE any OTU data row access. Target: compare original same-plot/year Canopy–Malaise row-OTU Jaccard similarity to random pairing with another original plot in the **same NFI_region × Year**, aggregating each NFI region equally. Method and layer would remain inseparable, so this was only to test source local fingerprint across two capture channels, NOT vertical niche, climate refugia or shared resource causality. Frozen quality gate required **at least two distinct original eligible plot/year contexts in EVERY NFI region/year permutation group**, and all 77 eligible contexts retained.

The [original biological workflow attempt #44449871314](https://github.com/zuizui0223/Structural/actions/runs/44449871314) completed **SUCCESS as execution**, archived aggregate artifact **#14495091856** ZIP SHA256 **`17974b47936be0644e7b29e0a757a6698dbe4f5e83e7b2713a5966242c661a1d`**, scientific status exactly:

```text
ORIGINAL_NFI2026_WITHIN_REGION_YEAR_EXCHANGEABILITY_SINGLETON_STOP
```

All frozen source metadata/sample header prior checks passed, but some original `NFI_region × Year` stratum has a **singleton** candidate source plot. The strict original method gate stopped BEFORE any 328-wide OTU response row access. No original OTU count, Jaccard similarities, null distribution, test p, bootstrap CI or species/richness scores were computed. **This is a design/eligibility STOP, not a biological non-support result.** The CI passed because it correctly recorded the scientific STOP. The source original method could not support the planned stratified control without modifying the frozen study definition.

## Decision and next independent work

- **Final for this endpoint:** no re-scoring using region-only, neighboring year, dropped singleton, unmasked source geography, tree-stratum rescue, or other post hoc null; no posterior selection of taxa or alternate similarity.
- The available public NFI network remains a useful **documented 83-plot/year, 8-region sampling input**, with a perfect 316/316 source-to-sequence metadata linkage for *other prospectively justified hypotheses*, but not an admitted confirmatory 3D/thermal-refuge study.
- Current forest ecological mainline should next target **an independent same-method forest-stratum × directly measured microclimate/hostwood source** or an original site/year design with sufficient independent within-stratum replication, verifying sampling frame BEFORE species read. The UK NFI main issue is **year×regional replication and method confounding**, not missing data files.
- Earlier PREDICTS +0.0942, Finland142 Host_tree deadwood +0.00024237, Carpathian116 trophic-guild deadwood negative -0.00106793, Thai/Brisbane and NEON known outcomes remain separate and untouched. GEB/BALA original protected outcomes sealed; no eBird/TinyFish. Draft PR #469, no `main` merge.
