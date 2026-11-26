# Ecuador saproxylic beetles: recovery-stage versus host-tree species composition axes — **descriptive only**

## Completed original-data audit (22 Nov 2026)

Original author ZIP exactly 11,201 bytes, SHA256 \`8c6e822866207a3398d6ce32fd35b6786713472ea87c2c1f3267984ebb79500d\`. This is an already published and previously opened cohort: Falconí-López et al. 2026 DOI 10.1016/j.foreco.2026.124102. Original authors already studied recovery-stage host networks and assemblage diversity. This addition is a derived **summary of pooled community distance, NOT an independent publication-quality ecological inference**.

Original source \`PlotKat4HostSpecIndiv_3.csv\` has 263 detected stage × Host × morphospecies records. *One* record has blank Morphospecies but 2 adults in \`Old × FERNAN SANCHEZ\`. After excluding ONLY that unnamed record from taxon-resolved composition, 91 exact named morphospecies and 10,648 individuals remain. \`HostBeetleIndiv_3.csv\` and \`a_*\` matrices independently contain those exact 91 named morphospecies and 10,648 adults; original 300 physical log rows sum to all 10,650 adults. The unnamed record is not a species #92. Name comparison requires punctuation-normalized identifiers (e.g. \`BOLD:AB123\` = \`BOLDAB123\`), never fallback matching of unknown labels.

Four forest recovery classes \`Agri, Reg1, Reg2, Old\` × five exact offered host classes \`CACAO, FERNAN SANCHEZ, GUABA, MASCAREI, SAPANILLO\` yield **20 pooled communities**, not 20 independent plots. The original 61 physical plots were aggregated over recovery classes and CANNOT be recovered from the morphospecies table. Distinct named-taxon columns total 91. Each pooled cell's original *identified* adult count is highly imbalanced **6 to 2,399**.

## Newly computed descriptive dissimilarities (NO new p-values)

Each of 20 pooled-cell vectors was normalized to sum 1. Hellinger distance = sqrt(sum_i(sqrt(p_i)−sqrt(q_i))² / 2) and relative Bray–Curtis = sum_i |p_i−q_i|/2. These normalized distances are bounded 0–1. Presence Jaccard distance was also computed but has the most severe rare-taxon sampling variation.

| Community pairs across 20 pooled source cells | Pair count (NONINDEPENDENT) | Mean Hellinger | Mean relative Bray–Curtis | Mean Jaccard |
| --- | ---: | ---: | ---: | ---: |
| Same recovery class, different Host | **40** | **0.747101** | **0.721920** | **0.830131** |
| Same Host, different recovery class | **30** | **0.727479** | **0.706536** | **0.822615** |
| Both Host and recovery class different | **120** | **0.758648** | **0.728876** | **0.850281** |

All are numerically high: both host types and forest recovery context can index different detected assemblages. The difference 0.747−0.727 ≈0.0196 is **not** an estimate that host filtering is stronger than succession, because: pair sets have different dimensions/opportunity counts, pairs share cells, source plots are nested and collapsed, sample size is 6–2,399, and no coverage standardization or disjoint geographic replication is available.

**Within-stage mean Hellinger across five hosts (10 dependent host pairs each):** Agri 0.8761 (min sampled cell 6 adults), Reg1 0.6810 (min 19), Reg2 0.7585 (min 126), Old 0.6728 (min 65). **Within-host mean Hellinger across four stages (six dependent stage pairs each):** CACAO 0.7565, FERNAN SANCHEZ 0.5494, GUABA 0.8408, MASCAREI 0.6453, SAPANILLO 0.8454. Do not rank biological specialist behaviour from these values: the highest dissimilarities occur where positive adult count can be very low.

## Limits and decision

This was a **post-result audit/descriptive extraction**, not a pre-registered test; no permutations, regression, pseudo-independent plot p, multivariate region variance partition or novel causal claim is authorized. The raw source does not include 61×5×morphospecies responses. Previous exploratory 59-plot host-emergence Q=24.30 (conditional p=.00005), held-plot emergence host gain p=.0906 non-support, and post-emergence Spec gain p=.6333 non-support remain **distinct**. None is rescued by an unrelated pooled beta distance.

The decisive next independent work is a source study preserving *physical plot × host × species* matrix with a true original plot-level training/holdout design, source effort and recorded zeros. Existing Sweden Ramberg 2025 public archive documents 23 plots across three regions with per-trap species matrix and source-local wood measurements but publisher file access had returned HTTP401 in prior Structural audit; no species values or cross-region effect confirmed. Future author supply/eligible independent source must retain identity before source opening. Do not collapse origin-history, site plot, observation method or species traits into one generalized forest mechanism.

**Deliverable:** anonymous aggregate-only local JSON \`falconi_stage_host_axis_descriptive_result.json\` and reproducible local \`falconi_stage_host_axis_descriptive.py\` were produced, with no plot IDs/species labels exported. Structural PR #469 Draft; no main merge, eBird/TinyFish unused, no protected island-mammal/BALA/GEB endpoint opened.
