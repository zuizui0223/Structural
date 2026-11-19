# Forest macroecology: what generalizes, what does not, and the next ecological discovery test (2026-11-19)

## Decision (source-free synthesis; no new organism scores)

**Broadly supported phenomenon:** Forest alteration is associated with excess *detected-taxon replacement relative to reference/reference variation* in 36/39 eligible PREDICTS studies across 20 countries. The inference denominator is **39 studies in 2 forest biomes**, not 4,920 forest sites in 7 biomes and not a worldwide mechanism.

**More difficult unanswered question:** What *additional ecological information*—physical structure, resource identity/decay stage, accessible source communities—improves prediction of communities in genuinely unseen forests? Existing resource/structure increments are **mixed and non-comparable across different endpoints**. Therefore neither “more deadwood universally predicts better” nor “structure is irrelevant” is supported.

**Novelty target, not an established result:** Identify *when* local resource identity and temporal resource continuity beat coarse forest amount/height, and whether a **single prespecified effect on the same taxon/guild endpoint** transports outside its source region/forest biome. Generic host filtering, temporal succession, vertical niche differences, and richness–identity decoupling are all prior art; they are not discoveries merely because this repo reproduces them.

This document uses only already-frozen aggregate reports; it **does not reopen** PREDICTS, NEON, Thai, Norway/Finland/Germany, Carpathian, Sweden, BALA, mammal or England biological files. It is not a meta-analysis and is not a new external replication. All old source, outcome and STOP boundaries remain intact. PR #469 stays draft and `main` unchanged.

## Evidence ledger with the correct independent denominator

| Evidence lane / original physical support | Frozen effect, original inference | Statement permitted |
| --- | --- | --- |
| PREDICTS: 39 original Studies / 20 countries / 1,145 eligible forest sites / **2 biomes** | altered–reference minus reference–reference Simpson taxon replacement **+0.0942**, Study-bootstrap 95% **[+0.0638,+0.1253]**, **36/39** positive, study signflip p=.0001 | Repeated reference-relative assemblage divergence **within original studies**; neither temporal turnover nor causal structural filtering |
| Nardi: 13 landscapes / 8 countries, surveillance-trap context | within-landscape urbanization-difference slope of recorded beetle Simpson replacement **+0.0146126**, landscape bootstrap [+0.003167,+0.027825], p=.0062, 10/13 positive | A different broad geographic *association* in selected surveillance landscapes; **not** independent replication of PREDICTS forest alteration estimand |
| BALA: 7 islands in **one archipelago**, repeated forest transects | temporal Sørensen identity-change excess versus within-campaign half-sampling: spiders **+0.1908**, beetles **+0.2212**, both 7/7 island directions and p=.015625 | Detectable temporal replacement in sampled island forests; not extinction/rescue, and not global homogenization |
| Thai beetles: 18 matched stations nested in **2 forests** | same-method upper-vs-lower trap counts **899 vs 723**, 18-station signflip p=.0043945 | Paired *capture activity* difference, not 3D species-richness or vertical-temperature mechanism |
| Burner three-country matrices: Finland, Germany, Norway; 1,622 **sample columns**, not forests | trait-label-null host guild sqrt-JSD difference **+0.091059**, conditional p=.000333 | Host-affiliation sorting relative to label shuffle, **not** site-level population inference or measured local host abundance |
| Finland: 142 author-verified plots, 9 coarse geographic cells | adding total deadwood VD10 to forest/climate/age/effort reference for **Host_tree 3-guild** Hellinger² prediction **+0.00024237** block-equal, interval [+0.00012123,+0.00035658], conditional p=.015, 7/9 positive | Small conditional **within-country out-of-grid** prediction gain, not causal or across-country transfer |
| Germany Chiu: 6 parent plots in **one Steigerwald forest** | adding experimentally offered tree-host identity to shade for **264-species composition**: Hellinger² gain **+0.019699892**, all 6/6 positive, exact p=.03125 | Within-one-forest *out-of-plot* predictive host-identity signal; not multi-biome replication |
| Slovakia Gloor/Weiss: 116 plots, **18 stands** nested within nine reported ranges | adding lying deadwood to baseline for **six larval trophic guilds**: Hellinger² gain **−0.0010679329**, 95% [−0.0022770806,+0.0000944958], exact stand p=.1121 | **Not supported** in this post-format exploratory test; 170/309 headings matched, no author-confirmed taxon-format bridge; not strict refutation of Finnish Host_tree result |
| Sweden Goßmann: 87 shade observations / 29 plots / **6 geographic blocks** | adding bark+diameter to regional climate/microtemp model for community **CTI**: MSE gain **−0.0002024886**, 95% [−0.00145838,+0.00092768], p=.6875 | **Not supported** for a different response/driver; resource identity absent (spruce logs throughout) |
| Sweden Goßmann **same original network**, not another independent study | adding measured under-bark microtemp to climate/shade/bark/diameter model for **log richness**: MSE gain **+0.0003012203**, 95% [−0.00146722,+0.00206966], p=.78125 | Small positive point estimate, **not supported** for cross-region incremental prediction |
| NEON: 18 original US sites / 10 domains / 121 plots | static CHMv2 height difference vs recorded ground-beetle Simpson replacement **+0.0349 per 10m**, site-bootstrap [−0.0158,+0.1079], p=.1759 | **Not supported** for this static-height predictor; does not test internal canopy structure or disprove structural biology |
| England NFI: 83 candidate plot/year contexts / 8 regions, 77 matched Canopy–Malaise sequenced pairs | prespecified within-region×year community-fingerprint null **STOP before OTU rows** due to singleton group | **No biological direction**. Different trap technology confounded with sampling layer; 2026 programme title has no 2026 observed rows |

### Non-pooling rules

1. PREDICTS study-relative Simpson, Nardi urban-gradient Simpson slope, BALA temporal Sørensen, Thai capture counts, guild-label JSD, Hellinger² for different response spaces, CTI MSE and richness MSE are **different estimands with different units, denominators and nulls**. No pooled mean, sign-test over “studies”, generic forest-effect p, or global universality claim is valid.
2. Finland Host_tree, Slovak trophic guilds and Swedish CTI **do not** form three replications of the same deadwood predictor experiment. Germany Chiu's offered host treatment differs from ambient local wood composition.
3. Multiple endpoints from one source, and taxonomic slices, repeated forest/plot/year units, geographic folds, permutations and bootstrap draws **do not multiply independent regions/studies**.
4. Forest cover and remotely sensed maximum height are not equivalent to canopy stratification, tree host species, wood decay stage, colonization opportunity or within-forest thermoregulation.
5. An unavailable source, zero-capture uncertainty, frozen design failure, HTTP401 or insufficient matched taxonomy is **HOLD/STOP**, never evidence for an ecological zero.

## Three competing prospective ecological explanations

**H0 — geometry/forest amount suffices.** Given climate, age, management history, forest amount, physical structure, space, effort and study, explicit substrate identity/decay stage cannot improve held-out composition prediction; gains from local host labels vanish outside source plots.

**H1 — resource-state gating.** Given the same baseline and total deadwood volume, **source-measured wood tree identity, decay-stage composition and continuity** add held-out information for *a predeclared comparable saproxylic guild/species endpoint* in genuinely new forest blocks. Predict stronger added value where specialized larvae require uncommon resources. This is a **prospective prediction**, not established by current cross-study mixed results.

**H2 — operator/observation dependence.** Source method, guild ontology, capture opportunity and regional source-pool composition determine whether extra resource information is estimable or portable. Differences among Finnish Host_tree, Slovak trophic guild, Swedish CTI and Germany Chiu composition must **not** be explained away as biology until these are harmonized.

Landscape source access `C` is a distinct *later* hypothesis: only after local resource and observation reference adequacy are demonstrated can occupied, training-only forest source configuration be compared against nearest-source distance and an operator-specific landscape graph. Ocean-island connectivity cannot be copied to terrestrial matrix movement.

## One reproducible future comparison, without reopening any burned outcomes

**Selection before biological read:** admit a genuinely independent original multi-region forest network with source-pinned plot × year × method × effort (including sampled zeros), observed beetle species IDs with a frozen trait ontology or complete predeclared species-composition endpoint, original substrate tree ID and wood decay classes or time since death, woody-resource total quantity, regional sampling blocks and date-aligned climate/structure. Confirm actual independent forest/region count; do not count traps, logs, species or pixels as forests.

**Single primary estimand:** use identical response ontology and method within network; in leave-one-**region**-out validation, compare held-out negative log-score or predeclared multivariate composition loss for:
- `E0`: climate + region-independent geographic context + forest amount + stand age + disturbance + documented effort;
- `E1`: E0 + canopy/landscape structure + total deadwood quantity;
- `E2`: E1 + measured wood host identity × resource decay-stage distribution (the **one primary increment E1 minus E2**, sign convention positive = gain);
- `C` source-configuration after E2 is **later**, not a substitute if E2 fails.

Only if a new original network has matched species/guild ontology, original resource gradient, sufficient independent holdout regions and adequate observed-zero exposure can its one-shot outcome be evaluated. A result in one country remains regional even if p<.05; require **at least two genuinely independent original regional programmes** with comparable endpoint and consistent transfer metrics before asserting geographic portability, and more biomes/providers before discussing broad generality. Holdout prediction **intervals across original programmes** are required for any statement about new forests. The final programme count/threshold/endpoint must be fingerprinted in a separate pre-response contract, not backfilled from a favorable test.

**Discriminating interpretation:** If E2 consistently improves in independent programs while E1 is weak, a resource-state mechanism has external predictive support; direct causal resource constraint still requires manipulation or transition observations. If E2 fails after a strong E1, structural context may be an adequate proxy for that endpoint; no universal ecological null follows. If gains change with taxonomy/method or the source cannot support exact comparison, report mixed/unavailable, not a rescued mechanism.

## Prior art (novelty firewall)

- Müller et al. 2015 DOI 10.1111/1365-2664.12421; Neff et al. 2022 DOI 10.1111/1365-2435.14186: host identity, forest context and saproxylic filtering studied before.
- Piccini et al. 2026 DOI 10.1111/1365-2664.70472: vertical stratum conditions beetle response to tree composition; vertical stratification itself is not novel.
- Vogelfänger et al. 2025 DOI 10.1016/j.foreco.2025.122880 and Lettenmaier et al. 2026 DOI 10.1111/1365-2656.70183: deadwood age/decay succession can dominate composition, and temporal continuity matters; **do not** call this mechanism unprecedented.
- The novel test would be **a harmonized, prospective, out-of-region resource-state increment under a strong forest structure/reference**, and a mapped boundary of when this increment fails; that *test has not been completed*.

## Evidence sources (original frozen repo receipts)

[PREDICTS](FOREST_MACRO_PREDICTS_REFERENCE_RELATIVE_TURNOVER_ORIGINAL_RESULT_20261112.md) · [Nardi](FOREST_BEETLE_13_LANDSCAPE_TURNOVER_URBAN_DIFFERENCE_RESULT_20261108.md) · [Finnish 142](FOREST_BEETLE_FINLAND_142SITE_DEADWOOD_HOSTGUILD_SPATIAL_HOLDOUT_ACTUAL_RESULT_20261115.md) · [Chiu six plots](FOREST_BEETLE_CHIU2023_STEIGERWALD_SIXPLOT_HOST_SHADE_SITE_HELDOUT_ACTUAL_RESULT_20261117.md) · [Carpathian 116](FOREST_MACRO_CARPATHIAN116_WEISS170_GUILD_DEADWOOD_LOSO_ONEPASS_ACTUAL_RESULT_20261118.md) · [Sweden CTI](FOREST_SWEDEN6_ORIGINAL_CTI_SUBSTRATE_6BLOCK_LOBO_ACTUAL_RESULT_20261119.md) · [Sweden richness](FOREST_SWEDEN6_87SOURCE_MICROTEMP_LOBO_RICHNESS_ORIGINAL_ACTUAL_RESULT_20261119.md) · [NEON](FOREST_MACRO_NEON_CHMV2_BEETLE_ONEPASS_ACTUAL_RESULT_20261115.md) · [England STOP](FOREST_NFI_ENGLAND_2026_OTU_EXACT_JOIN_AND_REGIONYEAR_GATE_ACTUAL_RESULT_20261119.md) · [older source-free crossaudit](STRUCTURAL_POSITIVE_EVIDENCE_SOURCEFREE_CROSSAUDIT_20261115.md).

**Scientific completion status at this commit:** broad community replacement yes, conditional local resource predictors yes, one universal resource mechanism no, causal mechanism no, forest↔island operator transfer no, original next fresh transfer cohort not yet admitted. No biological result or p-value was created in this synthesis.
