# Structural forest macro — BELongDead original experiment method-source identity and eclector coverage (2026-11-18)

## Current scientific decision

**A new ORIGINAL, publisher-verified method-record chain makes the BELongDead experiment much better documented, but does not yet authorize an independent feeding-guild×ambient deadwood ecological effect.** Original BExIS20406/tag2 is a retrospective author-provided record of log, instrumentation, methods and Status (not new field sampling or an independent country). Original BExIS31123/tag1 is the separately published positive-catch beetle source. Exact source plot and plot-log token universes align across these two sources, but log-year coverage differs in specific years, and complete source trap deployment/zero-catch denominators are not established. The 15 original 31124 TrapID discrepancies remain untouched and unresolved.

## Source authenticity and execution

Original University of Jena BExIS dataset **20406**: Weisser (2018), *BELongDead – 10 – Study overview logs*, published tag2, source rights CC BY 4.0 in official metadata. Original tagged CSV **2,717,980 bytes**, exact SHA256 **9bf68312668065a5d533fbbe65b22e9aef45b32f0d146921ab45e5133354b13f**. Original BE31123/tag1 beetle CSV **8,103,493 bytes**, SHA256 **73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e**. [Original author catalogue](https://www.biodiversity-exploratories.de/en/projects/arthropods-i-land-use-above-ground-arthropod-diversity-and-arthropod-affected-processes/).

All new tests were **separately prespecified and executed on the draft PR #469 analysis branch**, using exactly publisher-authorized original tagged datasets. CI success is not ecological hypothesis support.

| Original prespecified method gate | Actual Actions, result | Limits |
| --- | --- | --- |
| 20406 original public rights, variable dictionary and tagged header | [#44213090714](https://github.com/zuizui0223/Structural/actions/runs/44213090714) SUCCESS; artifact 14386537740 SHA256 `651a38b097661c3fb4ffc28a01ae8412204dcf938f62c9a3a39313a6b6be5561` | 14 field names only, no source data rows opened |
| 20406 exact public original source header field spelling | [#44213702688](https://github.com/zuizui0223/Structural/actions/runs/44213702688) SUCCESS; artifact 14386514340 SHA256 `bc9533db800d331d3937cd521907052a3fd2715031a0f48045143bba4929f425` | Source public original methods named PLOT, SUBPLOT, StammNR, Jahr, Variable, Methode, Equipment, wann, Status. Exact 20406/31123 author column semantics had not yet been demonstrated |
| German method/status lexical source records | [#44214274395](https://github.com/zuizui0223/Structural/actions/runs/44214274395) SUCCESS; artifact 14387023869 SHA256 `8fc23315cbf7d475df7447c8c9c15f6049025b25957d57bb5cc2991231f6999c` | Source method rows only, no organism responses |
| Frozen original eclector Equipment source grain | [#44214810326](https://github.com/zuizui0223/Structural/actions/runs/44214810326) SUCCESS; artifact 14387817155 SHA256 `c3c9b80b98af8da7dad6a2d2ba6a09d4bbd38e50f8a02b32f87beeb3d2d9cf4c` | Equipment mentions ≠ deployed traps |
| 20406 vs 31123 exact literal plot/log/year method token comparison | [#44215415641](https://github.com/zuizui0223/Structural/actions/runs/44215415641) SUCCESS; artifact 14387867134 SHA256 `63580e1da600f43ad4d8ebfb3df74c7c2426214ccdcf2bc0299e972602291b6a` | Literal concordance ≠ approved biological join |
| Four original public method Status categories by year | [#44216059042](https://github.com/zuizui0223/Structural/actions/runs/44216059042) SUCCESS; artifact 14388012397 SHA256 `1fa2ccf77c10aaa88087a102f1e98e5f8ca56023dafcbb822a31802604c5eda6` | Exact Status labels **REDACTED** after predeclared safety filter, semantic interpretation unknown |
| 2013/17 unmatched eclector subset vs ALL original 20406 method records | [#44216559956](https://github.com/zuizui0223/Structural/actions/runs/44216559956) SUCCESS; artifact 14388232433 SHA256 `1cf882de3307e76b678c526e32676f61cfa2a349de21f459ae66fb5b98b894b4` | Pure method metadata. No source capture effort/zero inferred |

## Source method grains: corrected from English-only audit

**Prior English-only source-header keyword matching (zero explicit trap/effort names) was incomplete**, because original column labels are German: `Methode`, `Equipment`, `wann`, `Status`. The source has:
- **12,289** actual original long METHOD rows (not 12,289 traps or 12,289 field sites), no 14-field parsing errors.
- **90** original plot×subplot combinations; **1,360** original plot×subplot×StammNR keys; **7,063** log×Jahr method-context keys across 9 original years.
- `Equipment` **4,233** original method rows matching a **precommitted** `eklekt|eclect|emergenz|emergence` lexicon; original `Methode` 1,128 long rows with sampling-time/effort words, `Status` 4 original levels in the equipment-filtered source. No explicit capture-zero lexical phrase was found. Keyword counts may overlap and do not establish sampling effort.

Source `Equipment` eclector rows grouped without species values:
- Original 30 PLOTs, **61** PLOT×SUBPLOTs, **995** PLOT×SUBPLOT×StammNR keys, **4,208** log×Jahr method keys. This smaller 4,208 denominator replaces the nonindependent 4,233 *row* count when describing source method contexts; it is **still not a verified number of independent deployments**.
- Yearly original **Equipment rows**: 2010=392, 2011=776, 2012=764, 2013=764, 2014=418, 2015=379, 2016=379, 2017=361. Distinct projected PLOT×StammNR×year tokens for 2010=380 and 2011=763; later years as in the source rows.
- 2015 and 2016 each have 379 eclector-equipment source rows; these numerically agree with the **379** original 31123 physical log tokens, **but counts alone would not establish common physical identity**.

## Actual cross-source physical identity evidence and 2013/17 attrition

A strict **no-conversion** comparison of original source `20406.PLOT,StammNR,Jahr` and `31123.PlotID,TreeID,CollectionYear` produced:
- Exact original PLOT vs PlotID token intersection **30/30**, with the same complete 30 source tokens.
- Exact original plot×log token intersection **379/379**; no 20406 `SUBPLOT` projection collisions on the equipment-selected method source and no original 31123 PlotID shared across regions. This is strong **literal author-ID alignment evidence**, but direct field-name semantic correspondence is still not independently established.
- Original 31123 **2,943** distinct source plot×TreeID×CollectionYear tokens, of which **2,829** occur within the original 20406 Equipment eclector source projection (**96.13% token coverage**). **114** original 31123 keys unmatched, concentrated in **2013=109**, **2017=5**. All 2010/2011/2012/2014/2015/2016 source tokens match the Equipment source.
- Precommitted, entirely method-only diagnosis of these **114** unmatched source tokens against ALL **7,063** original 20406 log×year method tokens:
  - **2013: 109/109 missing not just from eclector Equipment, but from the entire 20406 original method table.** This is an archive/source-frame omission or coverage mismatch, NOT proof that beetle traps were not deployed in 2013.
  - **2017: 5/5 present elsewhere in original 20406 method rows** (16 other-original-method rows with nonblank Equipment; no `eclector`, generic `other_trap` or `forest_log_measurement` pattern). It is a different original apparatus/method description, not a proven sampling failure.
- Of the 4 original 20406 eclector Equipment `Status` categories, one anonymous category comprises **3,763** method rows and all **764** equipment rows from 2013. Since the four exact category texts did not all pass the predeclared safe display filter, their labels remain **masked**. The 2013 109-key gap is not resolved by partitioning the Equipment-selected rows into multiple Status categories.

All numbers are source-method key *coverage*, not modeled richness/replacement, true absence, eDNA detection or live arthropod outcomes.

## Scientific consequences and next permissible task

The method-only source support is materially improved: a German author-provided multi-year instrumentation record exists, with verifiable original tagged bytes, and cross-source original plot/log names line up almost completely. This strengthens the empirical feasibility of connecting tree-host identity, experimental deadwood and beetle guilds at the original site/log-year level.

**But the required final method gates remain NOT SATISFIED**:
1. **2013** lacks original 20406 method records for 109 real original 31123 taxon-source plot-log-year keys; **2017** has 5 alternative apparatus-name contexts. These cannot be imputed as source effort zeros, and the publisher may have incomplete time/measurement coverage.
2. Original BExIS31124 versus 31123 still has **15 extra TrapID strings**, despite 15/15 sharing original log×host×year parent contexts. No author-authenticated trap alias / deployment table was obtained.
3. Original ambient deadwood BExIS24546 matches all 30 source plots in 2012, but author `DWV` has **mixed raw m³ and m³/ha units by survey stratum**; `Vharv` is estimated harvested wood, not existing stand deadwood. These must not be summed, and contemporary 2010–17 resources are not observed annually.
4. The old literature already studied 13 host-tree types, forest management and succession from this field experiment (prior art). A new *causal* universal host preference, stable cross-country *feeding-guild transfer*, or forest conservation response is NOT identified.

**Next necessary input** is a source-authored trap-occasion/zero-catch codebook and an explicit 20406↔31123↔31124 mapping for instrumentation, rather than further anonymous label matching or switching 2013 to a favourable year. If such source documentation cannot be obtained, keep BELongDead source-conditional analyses on **scientific HOLD**, and retain existing Finnish and 6-plot German observational predictive positives as separate endpoints. No new taxon/abundance data reopened or ecological effect run in this chain.

Original bounded forest results unchanged: Finland 142 author sites original total deadwood incremental heldout Host_tree guild H² +0.00024237 (9 spatial cells; source-conditional signed-cell p=.015), Chiu/Vogel 6-German-plot offered host identity detected-species prediction H² +0.019699892 (6/6, exact p=.03125), Piccini 8-German-floor site guild +11.70% relative prediction improvement but exact p=.09375 non-support, PREDICTS 39-study forest alteration Simpson replacement +0.0942, NEON CHM–beetle response p=.1759 unsupported. No new independent multi-country/biome feeding-guild transport. BALA and mammal GEB seals untouched. No eBird/TinyFish, no merge or author communication. PR #469 remains Draft, main unchanged.
