# Structural forest macroecology: independent DATASAPROX vertical sampling intake (2026-11-11)

## Current position and single objective

The established Thai beetle result (18 paired stations within **two** forests) supports a local canopy-capture excess, not a global vertical-niche law. The Brisbane independent source has strong canopy/ground species composition differences at 10 sites nested in one region, but its forest-edge interaction is unsupported. The Nardi 13-landscape/8-country beetle turnover association is a **horizontal**, near-entry-point surveillance sample, not a vertical-stratum replication.

**Next falsifiable main question:** among independently sampled forest locations, does upper versus lower capture stratum predict **species-composition replacement** beyond original effort, trap model, study and forest context? A separate question is whether this response differs between Corsica and continental France; it must not be inferred from merely having Corsica records.

## New external source, verified from primary publisher and data paper

- Source: DATASAPROX, GBIF dataset UUID `d050a143-2e62-4908-9d9e-a7f541eab94d`, published by INRAE, CC-BY 4.0.
- Original IPT release fixed for the first schema audit: `https://ipt.gbif.fr/archive.do?r=datasaprox&v=1.6`.
- Published source-wide denominator: **675,525 occurrence records**, **66,202 sampling events**, **8,969 geographic points**, **2,039 identified saproxylic beetle species**, 21 data providers, 485 source projects, 1997–2025.
- Original Darwin Core field `dynamicProperties` includes `ID_plot`, `ID_subplot`, `trap_stratum`, `trap_model`, `trap_type` and others. Original columns include sampling end date, duration, method, producer and coordinates.
- Source publication/field dictionary: Bosc et al. (2026), *Biodiversity Data Journal*, https://pmc.ncbi.nlm.nih.gov/articles/PMC12993481/ . Dataset: https://www.gbif.org/dataset/d050a143-2e62-4908-9d9e-a7f541eab94d .
- These totals are **source-wide**, not the usable vertical subset. Do not mislabel 8,969 points as paired canopy/ground forest plots.

## Executed stage 0: schema-only and untouched biological responses

`.github/workflows/forest-macro-datasaprox-original-schema.yml` downloads **one** exact publisher-version archive, checks its size, inspects ZIP entry names and `meta.xml` only, confirms declared core `Occurrence` and sample-key/stratum fields, and reports archive SHA-256. It **does not semantically open the Occurrence table**. It outputs only field-presence booleans and aggregate file metadata. A missing source schema is a scientific STOP, not a negative ecological result.

When its run is complete, the observed JSON/CI status must be checked before promoting any next stage. No original species or coordinate data are uploaded.

## Frozen next metadata gate (no taxon values yet)

1. First confirm original sample identity (`eventID` or a source-defined equivalent), source producer/project and published DwC-A core table schema. Do not fabricate IDs from point coordinates or treat occurrence rows as samples.
2. Parse only sampling metadata columns. Verify `trap_stratum` meaning from original source, `ID_plot`, `trap_model`, month/year and collection duration. Unknown/missing stratum stays unclassified.
3. A candidate matched pair requires the **same original producer, source project, field plot, year-month and exact trap model**, with both declared upper/lower strata and sampling durations 7–35 days differing by at most seven days. Same plot sampled repeatedly across months is only one physical plot.
4. Distinguish `candidate plot×month pairs`, `distinct original physical plots` and `independent projects`. To advance to an exploratory macro stratum contrast, require at least **30 physical matched plots across three original source projects**, with source-truth independent field-hierarchy verification. Corsica/mainland comparisons require separate original geographical identity and matched-protocol support.
5. If those gates fail, retain a numerical scientific STOP and do not score species; a nonzero `trap_stratum` column by itself is insufficient.

A separately tested synthetic Python prototype (6 tests passing locally, 2026-11-11) covers duplicate species rows within one event, incompatible year/method/effort, missing field plot, source event identity conflicts and forbidden taxon/ID export. **This is not a successful original source run**; only the GitHub Actions schema gate is in the branch at this stage.

## Scientific effect gate (conditional, NOT yet executed)

When original author-defined physical plots and traps are genuinely comparable: select a source-frozen occupancy/incidence response, calculate paired upper-vs-lower Bray–Curtis/Simpson composition differences, and compare with within-stratum baselines and/or explicit covariates under original-project holdout. Equal trap model and duration do not imply equal detection, and source projects may target taxonomic subsets. Do not pool qualitative presence and quantitative abundance without a declared conversion. No causal height, temperature refuge, source dispersal, island rescue or cross-biome generalization claim without a separate design.

## Guardrails

The previously frozen BALA taxon values, Thailand species scorers, Brisbane outcomes, Nardi urban turnover, island mammal heldout and GEB SCIENTIFIC HOLD are unchanged. DATASAPROX and Nardi are independent original field sources; the UK NFI canopy/subcanopy eDNA source uses **different Lindgren versus Malaise traps**, making a naive elevation effect non-identifiable. eBird and TinyFish are not used. Branch PR #469 remains Draft/unmerged.
