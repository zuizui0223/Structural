# Structural forest macro: BETA-FOR 234 paired-district candidate — original publisher source-only pre-intake (2026-11-20)

## Science decision: WHY 234, distinct from old 99 but not independent

Original Rothacher et al. (2025; DOI 10.1111/1365-2664.70086) already established higher standardized Hill `alpha` in canopy-gap + retained wood treatments up to 47%, and showed different indicator assemblages in open vs closed patches. Their original 2025 sampling frame has 99 patches in 11 German forests, with **ONE untreated internal CC patch + EIGHT distinct treatments per forest**, and six fortnightly Malaise samples each. The 99-patch panel has NO replicated untreated-control patches within the same forest: therefore a matched **control–control spatial `beta`** reference for the eight treated patches cannot be estimated from those 99 source patches alone.

The wider **same BETA-FOR experimental network**, documented in Müller et al. 2023 and 2026 BETA-FOR papers (e.g., DOI 10.1111/1365-2664.70252), has **234 physical patches**, with **one treated and one homogeneous-control district within each of the 11 forests** (nine each in most forests, fifteen each in the three University Forest sites). The 234-patch dataset is **NOT** a new 11-forest replication, new climate biome or independent intervention relative to the 99-patch source.

NEW *data-source candidate*, not biological discovery: author/Zenodo DOI [10.5281/zenodo.18467123](https://doi.org/10.5281/zenodo.18467123), described as `BETA-FOR_SP9_Arthropods_MalaiseTraps_Metabarcoding_one-time-sampling_all234Patches`. Official [US NLM catalogue](https://datasetcatalog.nlm.nih.gov/dataset?q=0002963396) identifies a single one-time 2022/23 sample per available patch and notes **one P08 sample lost in a storm**. This is NOT identical to the 2025 six-period 99-patch sampling, so cross-file OTUs/sample years must not be concatenated or counted independent without an exact author bridge. The present stage does not verify 234 usable source response rows or storm-affected ID, and does not assume that all 234 patches yield OTU records.

Relevant prior art: Rothacher et al. 2025 original alpha/indicator treatment effect, and the 2026 *Journal of Animal Ecology* paper `Temperate forest heterogeneity decreases local and landscape-scale spider diversity through habitat filtering despite increasing species turnover` DOI 10.1111/1365-2656.70297, from the **same parent experiment**, already studied spider alpha/beta. Do not present taxonomic turnover or alpha-beta separation in general as a novel mechanism.

## Research question for a genuinely different endpoint (prospective, NOT observed)

**Does experimental forest structural heterogeneity increase forest-scale effective insect diversity by creating distinct communities, or mostly increase local richness through recurrent/shared taxa?**

Three opposing signatures, all permitted:
- **H1 beta differentiation**: within-forest between-patch Simpson or Sørensen dissimilarity is GREATER in the treated district than matched undisturbed control district (plus alpha gains).
- **H2 alpha gain with spatial homogenization**: alpha increases under treatment, but within-treated-district beta is LOWER because shared disturbance/resource users expand widely.
- **H0 transfer failure/no difference**: after source effort and coverage standardization, there is no stable beta difference across independent forests/regions.

This is **not** a restoration-effect or dispersal mechanism claim; actual movement/rescue requires new observations.

## FIRST new source intake permitted — publisher metadata only, no original file content

Make one read-only GET to *version-specific* official `https://zenodo.org/api/records/18467123` only. Verify record ID/DOI/status/licence. Enumerate and freeze every public original file descriptor as `filename, positive file size, published checksum, file count` and the exact record ID. Files may have different versions/rights than the 2025 data; do not substitute the 2025 six-file hash list. No download of any original `csv/xlsx/zip/fasta` member, no first header, plot label, sample/OTU data or row. Fail closed on missing/changed publisher DOI and public license or unsafe descriptor. No inferred effect, no current 234 biological eligibility claim.

If source-only manifest passes, FREEZE a second `Region × Forest × District × Patch × Treatment × Year × Method × SamplingOpportunity` original *metadata* ID crosswalk based on actual author field schema. Require treatment/control district pairing and missing storm loss as an explicit attrition record, not a zero beetle OTU count. Do not read the response before sample frame passed.

## Future study (do NOT fit here)

Prespecify a **within-forest matched treated-vs-control district spatial `beta` contrast** of community taxon turnover (e.g., original incidence-based Simpson replacement). Calculate diversity at harmonized sequence depth / coverage and check detection normalization, then aggregate `beta_treatment−beta_control` by **forest** (n=11 nested in **six geographic regions**). No pairwise-pseudoreplication, no mixing 2022/23 years as independent replicated climate conditions. Predefine a one-shot held-out-region prediction against a strong geography/forest/effort/reference model; assume no unseen-biome generality until new regions appear. Disallow changing `beta` metric, OTU screening, storm patch handling or alpha/β direction after observing outcomes.

Existing BETA-FOR 99 source frame, all prior Structural PREDICTS/BALA/Finland/Germany/Slovakia/Sweden/NEON/island outcomes, v1 original version STOP and v2 role HOLD remain unchanged. Draft PR #469, no main merge; no eBird/TinyFish.
