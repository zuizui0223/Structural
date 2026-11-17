# Norway Wetherbee 2023 270 forest sites: original author R source reader and join grammar verified, but crosswalk still unproven (2026-11-17)

## Actually executed source-code audit

[Official Zenodo 10.5281/zenodo.8272489](https://doi.org/10.5281/zenodo.8272489) original author R scripts were downloaded by the GitHub runner only and original publisher MD5 + source bytes verified in [GitHub Actions #44083524412](https://github.com/zuizui0223/Structural/actions/runs/44083524412), which completed source-only script and known-truth tests SUCCESS. Artifact #**14326829847**, ZIP SHA256 **69ed7c979d75c5c5e5807546f74b4420ed0f1390d405c9c98884c2f7359f5bb6**. The original author scripts were not executed and no species, trait, site-history, guild or forest numerical data rows were opened.

| Original author source R script | Verified original methods, source-only |
| --- | --- |
| `DataAnalysis_FT_with_BioDmeasures.R` (6,204 bytes, MD5 `b5b02af2b3c07e741fe1e1afc3d022a5`) | 239 source code lines, one read call; zero generic merge/join calls under frozen lexer, 16 model-fitting calls, no exact references to the three predeclared original CSV filenames |
| `Ord_SO.select.R` (8,148 bytes, MD5 `871e3eb4ff24af8860f553fbd89b5b75`) | **227 source code lines, five reader calls, two merge/join calls, eight row/column-name calls and three transposition/wide-long calls**; code explicitly references all THREE published species-matrix/trait/site-information filenames |

The second original script is therefore a **promising source for recovering the author's intended file orientation, column keys and joins**, unlike the 270-site publication abstract alone. However, the source-only regex audit counted method grammar only; it did not extract argument expressions or execute the published transformations. **Two merge calls are NOT proof of a valid species-site-environment join, nor independent field lineage.** The authors' eight survey project identities and overlaps with older Burner Norway 468-site collection remain unverified.

Prior publisher-only original file manifest [#44082232916](https://github.com/zuizui0223/Structural/actions/runs/44082232916) SUCCESS and original three CSV MD5/header-only [#44082986667](https://github.com/zuizui0223/Structural/actions/runs/44082986667) SUCCESS verified 1090-column species×site candidate, 64-column traits and 41-column source site-info. No original site/taxon values read; no ecological endpoint selected or fitted.

**Scientific status: AUTHOR_ORIGINAL_R_CODE_SOURCE_JOIN_UNRESOLVED; biological score 0.** Next evidence requirement is inspecting the exact author-specified read/merge/rownames expressions (in code only) and verifying their field semantics against original method IDs before opening any biological values, then checking field overlap against previous Burner Norway. This would be a separate narrowly frozen method/code crosswalk, not a rerun of the 2023 published predator/morphology forest-naturalness findings. No automatic row-order merge, inferred 270 source sites from matrix width or taxonomic response fishing.

Original Georgia numeric-site vs beetle header 0/40 source join; Kriegel Europe official file access HTTP 401; Piccini original forest-floor +11.7% heldout error gain with p=.09375 non-support; Finland original deadwood +.00024237/p=.015 conditional; Burner original 3-country conditional guild D+.091059, PREDICTS, Thai, NEON, BALA and GEB science HOLD all unchanged. No eBird/TinyFish, PR #469 Draft/unmerged, main unchanged.
