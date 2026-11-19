# BETA-FOR parent 234 patches versus Rothacher 99-patch insect subset — do NOT count two independent datasets (2026-11-19)

## Evidence and unit distinction

**Original primary paper:** Rothacher et al. 2025 *Journal of Applied Ecology* DOI 10.1111/1365-2664.70086, sec. 2.1–2.2, selected **11 German forests across six regions**, nine specific original patches per forest and six fortnightly Malaise sampling periods = **99 physical experimental patches / 594 recurrent samples**, with experimental manipulation of gap configuration and wood retention. Source sample programmes at different regions are 2022 or 2023. Authors already reported increases in coverage-standardized Hill diversity up to 47% under gap+deadwood and treatment-associated community differences (prior art).

**Parent BETA-FOR experiment:** the wider forest experiment includes **paired managed/heterogeneous and homogeneous control districts**, at some sites fifteen rather than nine patches per district, total **234 parent patches** across the **same eleven German forest sites** (see original BETA-FOR forest-design paper summaries, including DOI 10.1111/1365-2664.70252). These are 234 patches, **not 234 independently replicated forests**.

**Potentially newer source, not scored here:** Public NLM catalogue indexes [BETA-FOR_SP9_Arthropods_MalaiseTraps_Metabarcoding_one-time-sampling_all234Patches](https://doi.org/10.5281/zenodo.18467123), publicly described as one-time metabarcoding output from *all 234 BETA-FOR patches*, with author names overlapping the 2025 paper and Creative Commons Attribution 4.0 rights stated in the catalogue. The exact primary original Zenodo member filenames/hashes, event/patch/OTU common ID format, survey year, sample completeness, and overlap with 2025 `com_singletons.csv` **have NOT been verified**. It must NOT be counted as a distinct sixth or seventh BETA-FOR region, a new ecosystem source or an independent replication.
A separate [2022–2025 Malaise biomass dataset](https://doi.org/10.5281/zenodo.18922434) is likewise catalogued across 234 patches but belongs to the **same experimental units**, not a fresh experiment.

## Distinct future ecological question, NOT an observed result

The already published increase in local insect diversity under gap opening can coexist with several distinct spatial outcomes:
- **Heterogenization**: treatment districts increase species/OTU dissimilarity among patches or retain more within-forest unique species.
- **Homogenization**: local diversity increases but the treated patches recruit broadly shared open-habitat taxa, leading to reduced among-patch distinctiveness.
- **No spatial reorganization**: local diversity rises but among-patch Simpson replacement stays similar.

The question—**does experimental canopy manipulation increase `alpha` while preserving, increasing or decreasing within-forest `beta` and `gamma`?**—is not answered by simply citing the original 47% Hill-diversity effect, and could align logically with the BALA observation that some islands' local richness increases while forest assemblages become more spatially similar. However, BALA is observational 7-island time series, not causal replication of BETA-FOR and cannot be pooled with it.

## Blocking gates, no access authorized yet

1. Exact original 234-patch source version/licence/checksums and original author `Region × Site × District × Patch × Year × Trap ` identity, matched treatment-control exposure and zeros must be verified **before** any OTU count.
2. Original 2025 99-patch programme vs 2026 parent dataset must be de-duplicated at patch/time/survey level before either can be treated as one coherent experiment. Do not treat shared OTUs/capture periods as independent effects.
3. **Same technology** across treatment and control districts; establish completeness/coverage and replicate counts within each source forest. Predeclare one detected-OTU response/coverage operator and one primary spatial-beta contrast before biology; compare treatment and controls **within forest**, not cross-region pairs of different species pools.
4. Uncertainty/transfer blocks are source forests nested within the **same six regions**, not thousands of OTU pairings. Exact 6 independent-region sign-flip two-sided minimum p is 2/2^6=0.03125 under the usual symmetric simple sign-flip design, itself not a guarantee of independent region exchangeability.
5. If official source identity or treatment/control matching fails, STOP; no effect inference or rescue under changed metrics.

This note is **source discovery only**. The current active mainline is still the 2025 99-patch BETA-FOR official publisher version correction and first information-header-only gate. The 234-patch source is explicitly **LATER**, not a backdoor biological outcome or extra geographic evidence. Do not touch existing PREDICTS/Finland/Slovakia/Sweden/Thai/BALA/mammal source seals, merge Draft PR #469 or use eBird/TinyFish.

Original published scope: https://doi.org/10.1111/1365-2664.70086
Parent paired forest design: https://doi.org/10.1111/1365-2664.70252
2026 catalogue: https://datasetcatalog.nlm.nih.gov/dataset?q=0002963396
