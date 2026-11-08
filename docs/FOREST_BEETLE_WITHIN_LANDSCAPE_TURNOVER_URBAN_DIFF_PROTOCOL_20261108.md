# Forest beetle community replacement along within-landscape urbanization differences
*Analysis-specific protocol recorded 2026-11-08. Exploratory, not preregistered before the 2026 Nardi dataset was first opened.*

## Goal

The prior original-source 13-landscape analysis (CI #42444893080) found **no support** for a uniformly positive relationship between trap-local urbanization and the fraction of detected *exotic* beetle taxa (mean +0.00363; 95% landscape CI −0.00373–+0.01184; conditional permutation p=0.3723). That negative result remains frozen, with no rescue by changing its estimand or excluding landscapes.

**Distinct question now:** Does *difference* in original trap-local urbanization index predict **species replacement** between two traps **within the same landscape**, beyond simple changes in species richness? The previous analysis tested exotic proportion at each trap; this analysis tests *pairwise beta diversity* in the full native+exotic species assemblage. Original Nardi et al. 2026 already evaluated trap capture efficiency and landscape-scale species turnover, so any finding is a secondary reanalysis of a published dataset, not new independent confirmation.

## Input / grain

Frozen original Zenodo v3 `10.5281/zenodo.17044394`, four TSVs with known MD5:

- `bio_cast.txt` 207 unique SITE×CELL_ID traps by 301 species incidence columns, validated binary 0/1.
- `bio_data_trapscale.txt` 3,215 positive species×trap records; counts are *not* used for this turnover contrast.
- `env_data_trapscale.txt` 207 SITE×CELL_ID records with original urbanization_index, composition, configuration.
- `env_data_sitescale.txt` 13 SITE-referenced forest-cover records (not used as exposures in this primary test).
- Same source identities and original trap join QC from `qualify_eight_country_beetle_joins.build()`. 13 landscapes with 15/16 trap positions; each landscape is one geographic sampling stratum and pair comparisons are heavily dependent.
- No source response heldout: this entire same study was previously opened. **Exploratory only.**

## Exactly one new primary test, fixed before running this code

For any pair of traps i,j from a single landscape:
- `x_ij = abs(urbanization_i - urbanization_j)/SD(urbanization within that landscape)`, where SD is population SD of all original traps in that landscape.
- `beta_sim(i,j) = min(b,c)/(a + min(b,c))`: a=taxa in both traps, b=only at i, c=only at j. This is the *Simpson turnover component* of Sørensen dissimilarity, chosen instead of Jaccard to limit richness/nestedness confounding. Undefined pairs from empty species assemblages are excluded with explicit counts. Each 15/16 trap study landscape must have at least 10 valid trap pairs and >1 unique x; otherwise it is ineligible rather than silently dropping from denominator.
- Within each landscape, calculate the OLS slope of beta_sim on x; aggregate **equally across the 13 landscapes**. Positive slope would mean greater community replacement between traps with more different urbanization scores.
- **Uncertainty:** 9,999 fixed-seed permutations of original urbanization values *among traps within each landscape*, preserving species composition, within-trap richness, each species’ site-specific occupancy, pair dependencies, and observed exposure distribution. Two-sided conditional p. 10,000 bootstrap draws of 13 landscape-specific slopes. Report 95% percentile interval, 13 slope signs, leave-one-landscape-out slope direction. Never treat within-site pairs as independent n or use their OLS p values.
- **Support condition:** mean slope >0, 95% landscape bootstrap lower bound >0 and conditional permutation two-sided p <=0.05. Failure remains non-support, not proof that turnover is zero.
- Jaccard dissimilarity vs x is secondary descriptive only, no additional claim or p-based rescue.
- No source geography for the actual intertrap spatial distances. Therefore any positive association could still be environmental/spatial confounding. This is a **within-landscape community-sorting signature**, not a demonstrated effect of urbanization or functional dispersal barriers.

## Decision logic

1. Check exact original source version, sample IDs, wide/long positive incidence and site environments before any species effect.
2. Test parser, study hierarchy, actual label permutation and known positive/flat/negative cases.
3. Score *once* under original 13 landscapes. Archive anonymized slope and biogeographic support only. No original trap/site IDs, species labels, individual coordinates, or raw source rows.
4. If positive: follow with *future* independent source/forest/region test, not immediate causal/biogeographic claims. If not supported: preserve and prioritize an independently sampled canopy/microclimate source, not serially search many ad-hoc endpoints.
5. No eBird; existing original Thai, BALA, global island mammal scores remain unchanged.

## Original publication

Nardi et al. 2026, *Ecological Applications*, DOI https://doi.org/10.1002/eap.70194. Original publicly licensed source https://doi.org/10.5281/zenodo.17044394 .
