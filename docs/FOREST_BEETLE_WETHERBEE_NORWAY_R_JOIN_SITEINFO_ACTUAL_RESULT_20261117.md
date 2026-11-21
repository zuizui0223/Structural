# Wetherbee 2023 Norway270: exact author R join calls and source SiteInfo hostwood HEADER eligibility — FINAL SOURCE METHOD HOLD (2026-11-17)

## Main executed result

[GitHub Actions #44088265400](https://github.com/zuizui0223/Structural/actions/runs/44088265400) **SUCCESS**, artifact **14330736281**, with exact publisher-original Zenodo 8272489 MD5 verified for two published R scripts and one SiteInfo CSV. This code audited **only the published author R program syntax and the FIRST original SiteInfo CSV header**. Original R scripts were **never executed**; there was **zero** access to original species, guild, abundance, site environmental/numeric/identity data rows. The gate was fixed and committed beforehand: [author R join and original resource-header prespec](FOREST_BEETLE_WETHERBEE_NORWAY_R_JOIN_AND_HOSTWOOD_HEADER_GATE_PRESPEC_20261117.md).

The 2023 authors had reported 270 original southern Norway forest sites from eight historical projects, 339 obligate saproxylic beetle species and forest naturalness indicators; their predator/morphology findings are **PRIOR ART**, not Structural findings. Older Burner 468 Norwegian source sites and this 270-site panel may share original collectors/field sites, so this cohort cannot yet be counted as independent.

| Source-only original method feature | Actual observed result | Biological interpretation |
| --- | ---: | --- |
| Publisher-original two R script MD5 checks | **PASS** | Exact publicly released code |
| Published `Ord_SO.select.R` code lines | **227** | Code only, never executed |
| Original three named species/trait/siteinfo CSVs referenced by that script | **3 / 3** | File lineage likely, but joins not proven |
| Original R `read.csv` calls in that script | **3** | Reader grammar only |
| Original `merge` calls | **2** | Both have explicit `by` arguments |
| Explicit literal `by` keys falling in strictly predeclared generic site/project/year set | **0 / 2** | Neither is proven an original physical site/project key |
| `row.names` / `colnames` / matrix-transpose transformations | **multiple** | Row/column remapping must be traced, not joined by position |
| Exact source SiteInfo CSV columns | **41** | Original publisher file MD5 PASS |
| Header names explicitly matching resource quantities/hostwood (`deadwood`, `dwvol`, `woodvolume`, `basalarea`, etc.), including predeclared lexical stems | **0** | Local stand deadwood resources NOT demonstrably measured via headers |
| Ambiguous `tree`/`wood`/`forest` lexical field candidates | **2** | May be trap-hanging/tree-class/context, not hostwood amount |
| Original species/trait/forest values read or biological beta/p computed | **ZERO** | No new ecological effect, not an ecological null |

This corrects a potential misunderstanding of the earlier [R code grammar count #44083524412](https://github.com/zuizui0223/Structural/actions/runs/44083524412): two explicit join calls do **not** imply they are keyed by original physical site or historical project IDs. The code-reader extracted named-argument grammars without exporting source expressions or unknown literal labels; the two literal `by` values remain unknown semantic keys under the prespecified privacy firewall. Likewise 41 SiteInfo headers with zero strong resource patterns does **not prove** resource fields absent under every possible original naming convention, but the necessary wood-resource covariate cannot currently be source-author validated.

## Scientific decision and project boundary

**Status: `SOURCE_ORIGINAL_HOSTWOOD_OR_PROJECT_CROSSWALK_NOT_YET_VERIFIED`.** No new independent Norwegian hostwood×feeding-guild predictive test is legitimate here. Prerequisites not met: (i) original source project×physical site/year correspondence to species columns and traits, (ii) quantified site-level deadwood/host resource field and units, (iii) trap effort including zero events, (iv) verified original study-lineage overlap/nonoverlap against older Burner Norway collections. Do NOT multiply 270 sites × 8 projects as independent studies, infer 1090 independent physical sites from species-matrix column count, or merge by source dataframe row order.

The primary Structural biological evidence remains:
- Finnish original 142-site spatial-block deadwood added guild Hellinger² prediction +0.00024237 (exploratory conditional block test p=.0150); original 3-country Host_tree shuffled-label conditional D=.091059 (source IDs partly unresolved);
- German 2026 Piccini floor 8-site leave-site-out guild prediction +0.00050966 Hellinger², +11.70% relative improvement but **two-sided exact site-signflip p=.09375 UNSUPPORTED**, frozen;
- Thai paired within-two-forest vertical beetle capture +24.3%, PREDICTS 39-study forest alteration turnover +.0942, BALA temporal turnover positives are **different estimands**, not replicate hostwood mechanisms.
- Mapped mammal GEB in SCIENTIFIC HOLD; previous Norway Burner and all old species values unopened. No eBird/TinyFish, no PR merge, no author communication.

**New cohort eligibility path:** select an independently published site/wood experimental study with explicit physical plot×resource×sampling/trait metadata rather than further optimizing Wetherbee's unverified source. A later author-defined codebook can reopen the Norway method gate as an entirely new task, but not under this source-free result.
