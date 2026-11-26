# Ecuador Falconí original archive: independent *source integrity* crosswalk, NOT new ecology (2026-11-22)

## Decision

The original supplied 11,201-byte Figshare ZIP SHA256 8c6e822866207a3398d6ce32fd35b6786713472ea87c2c1f3267984ebb79500d has **two different evidentiary conditions**:
1. **Adult abundance arithmetic PASS:** all 61 source physical Plot rows' summed original log Indiv match corresponding original plot Individuals exactly, and *all twenty* four-forest-recovery-class × five-offered-host adult sums match the original stage × host × morphospecies long table. Total **10,650 adults**. These are independent cross-table source accounting checks, NOT 61 biological replications of an ecological model.
2. **Taxonomic richness reconciliation HOLD:** the stage × host × morphospecies long source file has **one adult-count row for 2 individuals with a BLANK Morphospecies ID**, at the original Old × FERNAN SANCHEZ cell. Excluding this unlabelled source taxon reproduces **91 named morphospecies and 10,648 adults** in BOTH the 5 × named-morphospecies \`HostBeetleIndiv_3.csv\` matrix and the four \`a_Agri/Reg1/Reg2/Old_3.csv\` matrices. This EXACTLY resolves the 10,650 vs 10,648 count difference. The missing label is NOT an established 92nd species, and the two individuals were **not lost from the raw log- or long-format counts**.
3. **Incompatible or differently defined source richness fields:** among the 61 physical Plot keys, **7** have original \`PlotSpeciesIndiv_3.csv:Species\` smaller than the largest \`PlotLogSpeciesAbundancesDensity.csv:Spec\` of a single original log in the SAME Plot. Counts of such records by source recovery stage: Agri 1, Reg1 5, Reg2 0, Old 1. If both fields were identical species-union richness estimands this is impossible; it could instead reflect different taxonomic filters, preprocessing or a data error. **Do not invent a correction or claim an identified cause.** The previous per-log conditional-richness LOPO result is strictly for source \`Spec\`, not a verified full-plot richness estimate.
4. **Opportunity limitations unchanged:** source 61 physical plots and 300 original \`Plot × Host\` log rows vs paper's 62 plots / 306 recovered logs. There are 59 exact complete five-host physical plots, one four-host and one one-host; the missing source plot / six recovered log records cannot be inferred, converted to zeros, or reconstructed from pooled species matrices. \`PlotKat4HostSpecIndiv_3.csv\` uses four stage labels in its \`Plot\` field, not 61 physical keys, so it cannot support a plot×host×taxon prediction target.

## Audit implementation, privacy, and evidence class

The single original ZIP was opened locally for **source-invariant recomputation only**. No additional inferential model, ecological p-value, permutation, pairwise host significance, novel species response, or change to any earlier scoring rule was made. Original taxon identifiers and plot coordinates/keys/rows were NOT exported. The four stage matrices and pooled matrix were compared after **fixed name punctuation normalization** (e.g. BOLD:AB123→boldab123); blank remains blank, and all named-species cells and stage/host abundance totals match exactly.

Run locally:
\`python falconi_author_source_invariants.py --test\`
\`python falconi_author_source_invariants.py --source 'R%20skript%20and%20raw%20data.zip' --output aggregate_source_invariants.json\`

Integrity class: **SOURCE_ARITHMETIC_PASS_TAXON_LABEL_AND_RICHNESS_DEFINITION_HOLD**. Not a new independent biological dataset, not an ecological null, and not a causal result.

## Boundary on existing interpretations

- The 59-plot within-site emergence Q=24.301, conditional Monte Carlo p=.00005 is a **post-outcome exploratory host-label association**, with original host positions/randomization unknown. This QA does not turn it into an experiment.
- The source's host-added emergence LOPO gain +0.030624 / p=.0906 remains **NON-SUPPORT**.
- The separate after-emergence \`log1p(Spec)\` LOPO host-added difference −0.000711903 / p=.6333 remains **NON-SUPPORT** and SPECIFIC to the CSV's \`Spec\` column, whose compatibility with source plot-level \`Species\` cannot yet be established.
- Original authors already reported 91 named taxa, regeneration effects and host networks; the source QA findings are not a new ecological mechanism.

## Next precise author-codebook request

1. Please provide exact definitions and sample inclusion criteria for plot \`Species\` and per-log \`Spec\`, and explain why 7 plots violate the expected species-union upper bound when the same taxon universe is assumed.
2. Please identify the unlabelled Old × FERNAN SANCHEZ taxon record (2 adults), or confirm it should be excluded as unassignable from named-species comparisons.
3. Please reconcile original published 62 plots / 306 recovered logs with the public 61/300 tables and provide the full plot×log opportunity ledger including sampled zero logs.
4. If available, provide original actual **physical Plot × Host × Morphospecies × adults** source-key records with method and reuse provenance, rather than four-stage pooled records.

Prior original-source and forest/bat/mammal/BALA/GEB results unchanged, eBird and TinyFish unused. Keep existing PR #469 Draft/unmerged, no main merge.
