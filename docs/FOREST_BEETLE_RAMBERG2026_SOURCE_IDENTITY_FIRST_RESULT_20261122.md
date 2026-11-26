# Ramberg 2026 official 150 stump samples × species headers: first original key test HOLD (2026-11-22)

## Original source-only onepass
[GitHub Actions #45033120434](https://github.com/zuizui0223/Structural/actions/runs/45033120434) SUCCESS as a **source-only** program; original anonymous aggregate artifact #14758148983 SHA256 10137dddffe4511b27f32f7bc7a40f7cba69f34b6426bbaa5a851ae262dbf4ed. The job DID NOT open original species/taxon data rows or score any ecological response. The result is **SOURCE_ORIGINAL_SAMPLE_OR_HIERARCHY_IDENTITY_HOLD_NO_BIOLOGY**, not an ecological null.

Original Zenodo DOI 10.5281/zenodo.23021809, published exact file Beetles_data.xlsx 56,235 bytes MD5 42b6ba1d401cf77fc70efcfa91bf7adf SHA256 352c28b0615a3186914e95fbac27a6159b95d4c28f4028d5f47671513f818344.

First source-key audit (only author Samples physical/method ID fields and Species *header* numeric IDs):
- Species has **150 distinct numeric sample-column IDs**.
- Samples has **150 rows with a nonempty source field literally called sample id**, but **only 15 distinct values**; each is reused across different original physical stands.
- Naive exact overlap between the 150 species column IDs and the Samples single-field ID set is only **15/150**. There are **135 species header IDs without a one-field Samples counterpart**, and **15 source IDs are duplicated** among those 150 Samples source rows.
- **Independently recovered field hierarchy:** matched source rows contain **5 unique Pair_number values** and **10 unique Site_code values**, source Pair_number×Site_code groups = 10, **15 stump records per original stand and 30 per original pair**, all one source tree category (spruce). No missing in the four source fields sample id / Pair_number / Site_code / tree_species for the matched original rows.
- Source worksheet *used range* Samples A1:R168 had **161 actual XML data rows** in this run (not 167 sampled observations); exactly 150 rows held nonblank sample id. The Excel rectangular used-range bounds are not a biological sampling denominator.

## Scientific interpretation and STOP
The author field sample id is **stand-local (15 unique)**, while the Species wide table has **150 sample columns**. Joining by sample id alone is invalid. Although a composite Site_code + sample id might uniquely identify a stump, the published Species numeric headers do not contain stand IDs, so **do not infer that numeric column order equals the row order or author stand concatenation**. This is an explicit source data-format identity problem, not biological evidence for/against stump or landscape effects.

The next **strictly metadata-only** diagnostic is to inspect *all 18 author Samples first-row field-name labels*, plus the three species sheet descriptor header labels (no original specimen rows or sample IDs exported) to determine whether a genuine globally unique sample-key field exists elsewhere in the same workbook. If not, author-supplied column-to-physical-sample lookup is required. No ecological p, beta, model fit or large-n pseudo-replication authorized.

The original article already studied forest status and geographic community composition (prior art). At the appropriate **5 original pair** level, exact two-sided signflip p floor is 0.0625. No earlier Ecuador, Finland, Chiu, PREDICTS, NEON, BETA-FOR, BALA/GEB or mammal scores reopened. Frostgård 2026 official Dryad README HTTP401 and old Ramberg 2025 Dryad HTTP401 remain frozen access stops, no retries/mirrors. PR #469 Draft/unmerged, no eBird/TinyFish.
