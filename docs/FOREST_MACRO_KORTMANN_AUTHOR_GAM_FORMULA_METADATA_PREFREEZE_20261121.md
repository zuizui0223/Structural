# Kortmann 2026 author original GAM expressions — fixed source-code-only method diagnostic
Frozen 2026-11-21, independent of any OTU, site, disturbance or diversity response opening.

## Why another code-only gate
Previous original hash-pinned script lexical audit [CI #44761846381](https://github.com/zuizui0223/Structural/actions/runs/44761846381) found 27 `gam(` calls and 19 `offset(` calls in the 16,103-byte source `scripts_public/models.R`, but no author source data-frame or site×state×sampling record key was established. These counts are **method-token diagnostics, not 27 independent sites, 19 samples or 19 confirmed offsets from data rows**.

Exactly source-verified Zenodo `17775805`, original `data_code.zip` 46,205,253 bytes / MD5 `41f9a8428d80e833e4785be198a5c886`, original R script `models.R` 16,103 bytes / SHA256 `240d1b37150db6cf0b8b0288906dd0ba653fe92661a8a07e86a942f5af797b32`. Historical concept-source HTTP302, BETA-FOR99 original onepass and BETA-FOR234 no-files STOP are unchanged.

## One permitted operation
Reacquire exact original source-publisher ZIP, validate manifest/hashes, then open **only** original `models.R` (and NOT `.rda` or `.xlsx`). Do not execute original R code.

A deterministic, source-free tested parser records only:
1. number of parseable `gam(...)` call expressions, with bounded parenthesis and quote/comment state;
2. for each parsed call, whether safe, **predeclared** tokens from fixed categories `site/plot/patch/triplet`, `forest type`, `disturbance/clearing`, `sampling time/effort`, `OTU/coverage` appear in its literal source expression; output only category counts and whitelisted term names, not code;
3. count of formula `s(...,bs="re")` cues referring to a predeclared candidate site/patch field; count `offset(...)` occurrences inside GAM calls (not arbitrary strings);
4. source member SHA, parsed call count and explicit `source_organism_rows_read=0`, `source_models_fitted=0`.

Do not export R source text, full mathematical formulas, model coefficients, literal data, taxon names, sampling IDs, unlisted identifiers, full paths, source response columns or any original ZIP data member. An unrecognized model field is a `SOURCE_AUTHOR_GAM_FIELD_IDENTIFICATION_HOLD`, NOT a reason to inspect a response-bearing RData file or substitute guessed site IDs. A source-code model term is **not proof that original records actually have that column**.

## Future biological target remains UNTESTED
Author paper reports 40 triplets × 3 patches, 702 of 720 nominal sampling opportunities, 21,218 OTUs, four tree-dominated forest types; no original site/state/sample row evidence opened. The only prospective distinct estimand under consideration is matched `beta_sim(U,C)-beta_sim(U,R)` after source sampling and detection/coverage compatibility, not the prior BETA-FOR geometry-vs-wood `G-W` contrast. Sampling within-state beta is unestimable with one patch per state within site.

If model-cue audit cannot identify a safe original method key, stop further source-only code inspections and diagnose whether author supplies a response-independent original codebook. No reoptimization of frozen BETA-FOR, PREDICTS, BALA, Finland, Sweden, Slovakia, GEB or NEON endpoints. Draft PR #469 only; eBird/TinyFish off.
