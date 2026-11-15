# 2026-11-15 Structural forest macro: BELongDead 13 host wood types × 30 plots, original source validation and effort gate

## Current state and decision

**Genuinely licensed, downloadable and physically nested original field experiment now source-verified:** 2010–2017 German Biodiversity Exploratories BELongDead, original public BExIS 31123 full beetle long-form data. It includes **13 experimentally offered deadwood `TreeSpecies` labels in 30 forest `Exploratory×PlotID` plots nested in 3 Exploratories**, with **379 original nested source `TreeID` units**, 8 source collection calendar years and 2,943 tree×year contexts. All original 59,850 long records have valid `TrapID/PlotID/Exploratory/TreeID/TreeSpecies` and `CollectionYear` and no source tree-host identity conflicts. **No species abundance, taxon, guild or effect estimation was done in this turn.** The 30 original sites are independent sampling *clusters* nested in 3 Exploratory regions; neither the 379 logs nor thousands of collection events are 379 or 2,943 independently randomized forests.

**New scientific method STOP:** the published original tree inventory BExIS3546 has 797 stem rows, 75 PLOT labels, original German `Baumart` tree-species field, `BHD` diameter and `Baumhoehe` height, but **0/30 exact `PLOT` vs BELongDead `PlotID` token matches**. This means the *local site supply of each host tree species* is **NOT source-verified** for this 30-plot cohort. Neither fuzzy matching nor a guessed VIP–plot crosswalk is permitted. Original 3546 inventory has no explicit year column in its 16 headers; even a future author-verified plot alias would need date/age alignment before calling it contemporary host-source availability.

**Additional original-author complete-record view BExIS31124 is not a pure method-tuple subset.** Its source has 26,845 original long rows; the full source has 59,850. All original **379/379 physical nested tree keys** are represented in both, but the original complete-view has only **2,352** original source tree×year contexts compared with full **2,943**, and 8,699 original (tree×year×TrapID) metadata tuples vs 12,865 in full. The full original 6-field author method tuple `(Exploratory,PlotID,TreeID,TreeSpecies,CollectionYear,TrapID)` matches **8,684/8,699** subset tuples; exactly **15** complete-view tuples are not in the full-source exact method tuple set, so it is NOT a strict row/method subset. The mismatch is a **source-data-method consistency problem**, not evidence of a beetle effect or evidence that taxa are missing.

### Narrow subsequent diagnosis of those 15 fixed method discrepancies

A newly frozen method-only diagnostic on the same two source files shows:
- **15/15** unmatched 31124 original method tuples DO have the **same exact source (Exploratory,PlotID,TreeID,TreeSpecies,CollectionYear) five-field parent** somewhere in original 31123.
- **0/15** 31124 unmatched `TrapID` values occur **anywhere** in 31123 within the same source log or same original plot, even allowing other collection years. Original `Traptype` method category changes: **0/15**.
- Those 15 nonmatching trap tokens are distributed across **9** original field plot IDs, **11** physical nested log IDs, and **5** calendar collection years.
- All 379 physical log IDs remain present and no new log×host parent was introduced. The new IDs appear to be **additional/relabelled trap identifier tokens within a previously known log×year sampling context**; the true cause (**author correction, omitted original trap event or naming convention**) is **NOT established** without a publisher-authored method crosswalk.
- No 31124-only method record may be equated with a 31123 zero-capture, ignored as “15 insignificant rows,” or used to inflate effort. Any ecological analysis must resolve original sampling opportunities and original source taxa-trait meaning in a separate pre-outcome protocol.

## Source evidence: all GitHub Actions actually executed and original publisher digests

| Source gate | Actually executed | Result |
| --- | --- | --- |
| BExIS 31123/31124 individual publisher metadata, original BExIS3546 via separate gate | [#43701688869 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43701688869) | BExIS31123 + 31124 each official dataset metadata/version HTTP200 and **CC BY 4.0** |
| BExIS31123 official source file header | [#43701987094 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43701987094) | 8,103,493-byte CSV; 17 fields, `TrapID,PlotID,Exploratory,TreeID,TreeSpecies,Traptype,CollectionYear` present |
| BExIS31123 *full* source-method original grain | [#43702414237 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43702414237) | 59,850 rows, 30 plots/3 regions, 379 original wood units, 13 original host categories, 2,943 wood×year contexts; original SHA256 `73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e` |
| BExIS3546 actual stand inventory rights/header | [#43702823330 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43702823330) | Original version5 CC BY4, 40,458-byte 16-column stand-tree inventory; first CI #43702740955 failed due *code-only* v1 tag parser, fixed before inspection |
| Original BE31123 vs 3546 exact original plot tokens | [#43703102896 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43703102896) | **0/30 exact join**. 3546 797 stem rows, 75 plot tokens; source SHA256 `80aeaee5ec18e99277665ac18f77bae06a9e762ce3a69072df2fd23522ea4a94`. No original habitat amounts read |
| BExIS31124 complete-view method compare initial | [#43703613963](https://github.com/zuizui0223/Structural/actions/runs/43703613963) (CI **FAILURE only in status assertion**, original method counts computed and artifact archived) | 31124 source 3,636,045 bytes SHA256 `e9c6ab60c05c842434c8d976bfedd5da11893200c45556906ce1da1f68ea4c8c`; 26,845 original rows; 15 novel 6-field exact method keys. Scientific STOP as designed; CI mistakenly lacked `source_stop_not_ecological_non_support` flag |
| Same fixed 31124 method comparison, status bug repaired | [#43703716544 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43703716544) | Source method non-subset **scientific STOP** correctly persisted, without rerunning any biological effects. No method-filter changes |
| Frozen 15-tuple source parent diagnosis | [#43703965411 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43703965411) | All 15 known log+host+year parent; none shares source original TrapID in parent plot/log. Artifact **14157379200**, SHA256 `db3229d10949011a803895b8409433ae4b0cb3866a95f9df7327b5c944e2dd9d` |

**No exposed original source ID values, beetle records, tree species names, specimen counts, raw stand measurements or restricted user data were reexported.** Original published 13 host types are known only at source metadata level, without any species/abundance outcome. Code:
- `analysis/forest_macro_global/belongdead_bexis_13tree_original_source_gate.py`;
- `analysis/forest_macro_global/belongdead_bexis_31123_data_header_gate.py`;
- `analysis/forest_macro_global/belongdead_31123_original_source_plot_tree_grain.py`;
- `analysis/forest_macro_global/belongdead_bexis3546_stand_inventory_source_gate.py`;
- `analysis/forest_macro_global/belongdead_31123_3546_original_plot_crosswalk.py`;
- `analysis/forest_macro_global/belongdead_31124_author_complete_log_effort_gate.py`;
- `analysis/forest_macro_global/belongdead_31124_unmatched_trap_method_parent_gate.py`.
Original public dataset licence CC BY4, BE BExIS publisher versions/IDs in corresponding frozen source prespecs.

## Ecological interpretation ceiling and one next action

This is excellent source material for a **new original German forest hostwood experiment** because the 13 deadwood types were offered under a shared study design to 30 original plots across three Exploratories and original physical wood identities are coherent through eight collection years. But:
1. The original publisher and prior original 2016 paper already showed **host-tree beetle preference and early deadwood succession**; rediscovering that hosts differ is not novelty.
2. Local forest standing tree *species composition / actual source species pool* is not available via an exact join to BE3546. A new “source species pool × supplied deadwood host” interaction is **not currently identifiable**, and no invented matching allowed.
3. Neither full 31123 original long records nor author-labelled 31124 complete-view guarantee **zero-capture or effort-complete sampling opportunities**. Source trap identifiers need author codebook reconciling 15 novel keys and the original host×year trap sampling protocol. Do not interpret unobserved beetle rows as true absence or zero capture.
4. The 30 plot clusters nested in three Exploratories, 13 tree host types and eight years provide a robust experimental substrate hierarchy, but NOT 30 independent study replicates. All future source evidence must be plot-cluster/repeated log-level with actual effort normalization and no post hoc favorable host/taxa/decay-year restriction.
5. **Immediate next necessary legitimate source input is author-published plot/experimental-substrate and trap deployment/effort method crosswalk**, ideally official BExIS 31123/31124 codebook or independently published effort-zeros archive. Use verified official metadata/documentation, not new probability tests. A result that the source is currently blocked scientifically is preferable to a spurious new “universal” positive.

Previously frozen Finland 142 forest guild +.035237, local deadwood spatial-block added prediction +.00024237/p=.015, three-country Burner D+.091059, PREDICTS 39-study +.0942, NEON CHM non-support +.0349/p=.1759, BALA and mammal GEB HOLD unchanged; eBird/TinyFish unused. Structural PR #469 remains **Draft/unmerged**.
