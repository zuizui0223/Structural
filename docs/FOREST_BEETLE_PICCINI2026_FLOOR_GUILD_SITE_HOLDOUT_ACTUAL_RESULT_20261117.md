# Piccini 2026 independent German forest-floor beetles: prospective site-heldout guild-composition TEST COMPLETED, directional gain but no formal support (2026-11-17)

## Main scientific result — one original-data exploratory endpoint, genuinely executed

**Executed one fixed original biological-response test** from [prebiology/source-gated protocol](FOREST_BEETLE_PICCINI2026_FLOOR_GUILD_HELDOUT_SINGLE_TEST_PRESPEC_20261117.md), committed **before first original source species/guild/abundance access in this Structural branch**. [GitHub Actions #44076373342](https://github.com/zuizui0223/Structural/actions/runs/44076373342) **SUCCESS** (synthetic positive/null/leakage test PASS, publisher original MD5/field method PASS, exact one original response score, artifact #**14324443045**, workflow ZIP SHA256 **490101d3b090fecf809c505166dd86cfe9eb9978d6df23378b863b771c16c94b**). Original source: [Piccini 2026 GRO.data DOI 10.25625/H8EMJS](https://doi.org/10.25625/H8EMJS); published prior work: [Piccini et al. (2026) JAE 10.1111/1365-2664.70472](https://doi.org/10.1111/1365-2664.70472).

**Result: 2019 forest-floor originally observed, detected-species feeding-guild composition is predicted slightly better at new parent sites when the source stand category is used, but the precommitted exact site-unit randomization p fails the support gate.**

| Original frozen outcome / effective unit | Actually computed |
| --- | ---: |
| Source verified full field method rows | **22,414** |
| Independent geographical parent site IDs / stand types / plot labels | **8 sites / 5 types / 40 plots** |
| Original published-design-compatible 8 recorded 'trapID' identifiers per plot in the floor panel | **40 / 40 plots** |
| Distinct original floor species with positive recorded abundance | **594**, exactly agreeing with author's published floor species count |
| Source-active floor species with feedingguild assigned / guild conflicts | **594 / 594; conflicts 0** |
| Distinct original feedingguild label categories (unmodified, none selected) | **5**; source labels NOT exported |
| Original source period tokens per selected floor plot | **5–7**; period tokens NOT calendar years or equal exposure days |
| **Primary 8-site-equal heldout baseline Hellinger²** | **0.00435610** |
| **Primary heldout with original forest stand-type identity** | **0.00384644** |
| Primary paired baseline minus extended Hellinger² | **+0.00050966** |
| Site-equal heldout relative error reduction | **+11.69986%** |
| Site-bootstrap 4,000, percentile 95% CI for Δ | **[+0.00009345, +0.00090021]** |
| **All 2^8 = 256 site-signflips two-sided exact conditional p** | **0.09375** |
| Parent site heldout groups showing improvement / worsening | **5 / 3** |
| Minimum/maximum anonymous individual site gain | **−0.00011664 / +0.00124428** |
| Fixed predictive shrinkage for stand groups | **lambda=5**, 7 training sites per stand |
| Frozen exploratory support rule: Δ>0, block CI>0 AND exact p<.05 | **NOT MET** (exact p=.09375) |

### Inference: why this is still worth recording, and not a significant positive

The independent **heldout geographical prediction** is an executed additional response diagnostic, not just another planned hypothesis. Stand identity improved the sample-average Hellinger² prediction of detected-guild fractions by about 11.7%; this is descriptive *within the original eight-site field study*, and only **five** of eight site blocks improved. The paired percentile bootstrap CI above zero is conditioned on resampling **only eight observed site contrasts** and does not override the **precommitted 256 exact signflip p=.09375**. The two uncertainty procedures have different null/sampling assumptions and this is a small, potentially skewed block distribution. **No statistically established portable forest-floor stand effect**, no second favorable variant, no p-value replacement, no species/guild cherry-picking. Do not call 40 plots or 557 trap labels 40 or 557 independent forests.

The original Piccini et al. 2026 article already found that **feeding-guild composition on the forest floor and subcanopy overlaps among forest stand types, with most pairwise comparisons non-significant after multiplicity adjustment**, whereas canopy assemblages show clearer tree-identity differentiation. Our heldout floor-only source-conditional direction is consistent with a weaker/lower-layer role for tree identity and does **not** independently replicate the published canopy effect. It is scientifically distinct only in **leave-parent-site-out prediction against an explicit frozen baseline**; the same original field dataset is not independent publication-level replication. The source's five raw guild labels were deliberately all retained even though the author's paper separately analyzed four major feeding guilds. No special trait labels are inferred.

### Original data eligibility and privacy firewall

The source-only stage required unique original exact 'trapID' at CSV column 8 and verified 557 global IDs restricted to plot×layer, all 40 physical plots eight recorded trapIDs in a uniquely identified stratum; other strata 37 of 40 plot 8/3/3 and 3 plots 8/3/2. The source's 8 parent sites×5 stands and plot/stratum hierarchy were all verified without reading original biology. Only after this gate did the script parse original positive-abundance species names and guild labels in the selected 8-ID floor layer (594 taxa, five raw guild classes, guild coverage 100%). Original field species names, plot and trap IDs, guild labels, raw abundances, response vectors, individual folds, site coordinates and fitted predictions were never exported. No abundance- or trap-day-weighted biological effect was scored. Source period labels were never conflated with calendar years; 2019 floor sampling is based on the **paper**, not the period token string.

### Scientific limits and next best evidence

- **This is NOT a causal intervention in tree resources**. A source stand category is a coarse tree identity proxy confounded with soils, understory, site histories, bark/litter and sampling detection. The 17-field source has no distinct original trap-days exposure and no complete zero-catch ledger; although 40 plots each had eight observed trap IDs, periods per plot vary (5–7) and equal detection opportunity is unverified.
- No vertical-height or between-stratum causal inference: floor 2019 pitfall, subcanopy 2019 FIT, canopy 2021 FIT, four storm-replaced plots; source labels do not identify a same-year/same-method three-layer contrast. The algebraic rank deficiency is documented in [independent design audit](FOREST_BEETLE_PICCINI2026_LAYER_YEAR_METHOD_RANK_AUDIT_20261117.md).
- Feedingguild is not the Finnish/Burner Host_tree broadl/conifer/both. **No shared Hellinger² effect-size meta-average across countries, guild definitions, temporal protocols or forest structure outcomes.**
- **Next clean independent ecological replication** requires new original forest network with author-verified site/stand/hostwood identity, taxon↔functional trait crosswalk, full trap × exposure-days incl. zeros, and a predeclared *leave-region/site-out* test. Do not rerun canopy or subcanopy post result, change lambda, source periods, guild class selection, or positive threshold on this cohort.

Original Finnish 142-site local deadwood guild predictive ΔHellinger² +0.00024237, original 3-country Burner Host_tree trait-label D+.091059, PREDICTS forest alteration +.0942, Thai within-two-forest canopy catch excess, NEON CHM non-support and BALA temporal composition remains **unchanged** and not rescaled. Mapped mammal GEB main remains **SCIENTIFIC HOLD**, zero freshly prospective multia rchipelago confirmations. No eBird/TinyFish, Draft PR #469 stays unmerged, main untouched.

## Reproducibility / freeze decision

Original code: `analysis/forest_macro_global/piccini2026_floor_guild_site_holdout_onepass.py`. One-source workflow: `.github/workflows/forest-macro-piccini2026-floor-guild-onepass-holdout.yml`. One run [#44076373342](https://github.com/zuizui0223/Structural/actions/runs/44076373342), no post-result variants. This file closes the tested original response: **DIRECTIONAL_PREDICTIVE_GAIN_BUT_PRECOMMITTED_EXACT_TEST_UNSUPPORTED**. A new field network (not another favorable slice of this source) is required to adjudicate portability.
