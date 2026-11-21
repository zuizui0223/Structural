# Kortmann 39-triplet original OTU identity: completed sample-link HOLD

**Result: `SOURCE_OTU_SAMPLE_LINK_HOLD`.** The source gate completed normally, with exit code 0. It did not establish an individual sample join and does not authorize a biological calculation.

## Fixed code and single original execution

- Executed code-only freeze: [`9b81d0a5f7624d8170fd561967e17ef2f59bf4b9`](https://github.com/zuizui0223/Structural/commit/9b81d0a5f7624d8170fd561967e17ef2f59bf4b9), committed before source access. The [repair and execution-routing record](FOREST_MACRO_KORTMANN39_OTU_IDENTITY_REPAIR_20261121.md) was part of that freeze.
- Original execution: **2026-11-21 23:31:28–23:33:19 JST** (14:31:28–14:33:19 UTC), once, using Python 3.12.14 and R 4.5.0. The original command was not rerun after seeing the result.
- [Anonymous receipt](../outcome/kortmann39_otu_identity_20261121/receipt.json), SHA-256 `be7dafd2bd2736117bb3993c31c436323b10aa30767774c5b0ac02457d4a3147`.
- [Execution provenance](../outcome/kortmann39_otu_identity_20261121/execution.json) records the frozen commit, six code/specification hashes, command, runtime, time bounds, exit code and receipt hash. An independent reviewer checked these hashes against the frozen Git blobs without reopening the original data.

## What the original source established

| Check | Observed result | Meaning |
|---|---|---|
| Publisher source | Zenodo version 17775805; original ZIP size and MD5 matched the frozen declaration | The intended archive was obtained |
| Method member | `diversity_satellite.rda` matched its previously fixed SHA-256 | The already qualified method table was reused |
| OTU member SHA-256 | `6405103aa3797a283b691da8997585f95a98c76e066d8f0e56ad1414da9ec52c` | A fingerprint computed this time, not a previously published expected SHA-256 |
| Loaded OTU objects | 1 plain `data.frame` | The admitted simple-container schema was observed |
| Object shape | 20,898 rows × 702 columns | Dimensions only; 20,898 is not a certified taxon count |
| Candidate-axis labels | 702 column labels; noncandidate row labels not accessed | A sample-sized named axis exists |
| Predeclared method ID columns present | 0 | None of the frozen exact candidate column names was present |
| Eligible distinct method key vectors, including row names | 0 | No nonblank, unique, non-default 702-key vector was available through the frozen rules |
| Exact 702-key matches | 0 | The individual sample join could not be established |

The method-population checks passed before the OTU load: **39 complete triplets, 117 retained patches and 690 retained records**, with 105 patches having six records and 12 having five; each of the three anonymous treatment classes has 230 records. The excluded triplet has two six-record patches, totaling 12 records. These are the previously fixed method-only population checks, not an ecological result.

The receipt's retained/excluded match counters of zero mean **no accepted join**. They do not show that 690 or 12 samples disappeared, and the lack of a candidate does not prove that no author identifier exists under any other name. The conclusion is restricted to the prospectively declared candidate fields and row-name rules. Equal numbers of rows and columns do not establish identity; no row-order join, stripped-label guess or outcome-based key search was used.

## Exposure history and unchanged scientific boundary

The original response-bearing OTU RData was deserialized into isolated R memory. Its exposure state is **`DESERIALIZED_SCHEMA_ONLY`**, not unopened. The frozen code accessed the admitted structure and sample-sized column labels, and performed no indexing, summation, detection summary, richness calculation, alpha/beta calculation or model on original numeric OTU cells. It did not access the noncandidate taxon-name axis. No sample names, site labels, treatment values, source object names or taxon names were exported.

The separate phylogenetic-tree RData and large Excel workbook were not opened. The original strict 40-triplet gate remains HOLD. The original 39-triplet source-informed scope is unchanged. Previous ecological results remain sealed, and no new ecological effect was estimated.

## Method evidence and the missing input

The [author paper, sections 2.1, 2.3 and 2.5](https://elib.dlr.de/220269/1/Kortmann_et_al_2025.pdf) supplies the overall trap design, approximately biweekly collection in May–July 2022, and a sampling-length offset in the model. It does not provide a per-bottle identity/date crosswalk or establish the stored offset's units and transformation. Its figure labels do not identify the serialized treatment codes.

The publisher's [Supplement 1](https://ars.els-cdn.com/content/image/1-s2.0-S0006320725006846-mmc1.docx) was subsequently obtainable from the official CDN despite the article/API access failures. The primary document was independently retrieved and its methods read directly: **991,180 bytes**, SHA-256 `51c1448824a79bbc739409a63f79d5256273a6b0a063101f3c285b41418ab30a`. The [bounded supplement review record](../outcome/kortmann39_otu_identity_20261121/supplement_methods_scope.json) covers six method prose paragraphs: one under `Metabarcoding`, two under `Bioinformatics`, and three under `iNEXT Calculations`. Result tables and figures were not inspected. This review has not supplied the missing sample ledger or treatment-code mapping. Reference-database Process IDs described in the bioinformatics prose are not a trap/bottle-to-method-record crosswalk. Absence from the checked text is not proof that such author metadata does not exist elsewhere.

**One external input is required:** an authoritative, response-free author sampling ledger with its codebook, linking each original OTU column ID to the corresponding method record and physical patch/triplet. The same package should state collection start/end, interruption or malfunction status, effective duration, offset units/transformation and the stored treatment-code meanings. It must contain no species/OTU response columns. This would support the next method-only identity and timing gate without changing the fixed 39-triplet population.

Until that evidence is available, sample identity, seasonal comparability and treatment-code semantics remain HOLD. A biological beta comparison is not executable from this receipt.

## Verification and repository state

The corrected fixture and R-to-Python synthetic boundary passed using actual R offline; seven Python regression tests passed. The full repository suite passed **1545 tests**, with six optional Shapely-dependent tests skipped. Two warnings were recorded: an existing pytest plugin deprecation and an intentional duplicate-member ZIP fixture warning. The final code and source-result receipts received independent review.

This audit was executed locally, not as a successful GitHub Actions source run. Code and result commits use `[skip ci]` because the PR's accumulated diff would otherwise replay unrelated live source analyses. This workflow's original step is disabled for every event. No new workflow runs were observed for the code freeze. Broader legacy CI routing is a separate later task; do not restart sealed source workflows merely to clear pending checks. PR #469 remains draft and unmerged.
