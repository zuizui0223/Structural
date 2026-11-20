# Kortmann 2026 canonical Zenodo version 17775805: original publisher index ONLY — source prefreeze 2026-11-20

## Why this new gate is admissible after the historical STOP

Kortmann et al. *Biological Conservation* 313 (2026) 111647 DOI 10.1016/j.biocon.2025.111647 cites Zenodo **10.5281/zenodo.17775804** for original data and code. Historical source index [#44744082425](https://github.com/zuizui0223/Structural/actions/runs/44744082425) stopped on **HTTP302**, while opening **zero** file members, sample keys or biological source rows. This STOP is immutable.

A separately precommitted source-response-free diagnosis [#44757596857](https://github.com/zuizui0223/Structural/actions/runs/44757596857) subsequently verified that the original official publisher URL `https://zenodo.org/api/records/17775804` returns an HTTP302 `Location` to **`/api/records/17775805`** on the same Zenodo origin. It did NOT follow or GET that destination. Official Zenodo documentation states that concept records may redirect to the canonical versioned record.

**This new independent pre-data gate** pins the exact candidate `https://zenodo.org/api/records/17775805` and requires a version-specific published DOI. We are NOT substituting an arbitrary latest record or treating the HTTP302 alone as data eligibility.

## One and only one publisher-record GET permitted

1. GET exact `https://zenodo.org/api/records/17775805` once with **redirects disabled**, JSON `Accept`, body <= 1 MiB, no cross-host requests; original concept 17775804 is NOT refetched.
2. Require source JSON `id=17775805`, `doi=10.5281/zenodo.17775805`, `status=published`, and public metadata license in the predeclared set `cc-by-4.0`, `cc0-1.0`, `cc-by-sa-4.0`. An absent `metadata.version` is allowed only under the exact pinned DOI and immutable original record; a nonempty version may be reported if syntactically safe. No concept/latest DOI fallback.
3. Require a **nonempty file descriptor list of 1–100 original entries** with unique safe source filenames, positive integer byte sizes and publisher checksum in `md5:<32 hex>` or `sha256:<64 hex>` format. No 'file unavailable' rescue from an external mirror. These are **publisher-reported digests only**, not independently verified member bytes.
4. Output a non-identifying publisher file manifest of **name/size/checksum only**, JSON roster SHA256, versioned record ID and license. No file-member link access or original data download; no original study/forest ID, years, sample/OTU names, abundance, plot data, coordinates, treatment, taxon or models parsed. No source file gets performed by this stage, even if a file appears to be metadata-only.
5. If exact record/DOI/status, rights, source-file roster or checksum fail, emit a named `SOURCE_CANONICAL_PUBLISHER_STOP_*` with zero ecological inference and preserve the historical HTTP302 STOP. Passing index metadata means only `SOURCE_CANONICAL_INDEX_READY_NO_BIOLOGY` and does not license any raw member/response opening.

## Next AFTER a source-index PASS (not authorized by this prefreeze)

Freeze a separate source file-role/first-header method gate for **forest site × triplet × state (undisturbed/disturbed/cleared) × sampling method/year/effort**, first proving physical independence from the same BETA-FOR 11 forests via published source geography or original site lineage. Do not assume Kortmann triplets provide >=2 source plots per state per forest; if a condition has only one, **within-condition spatial beta is not estimable**, so the BETA-FOR within-forest matched A/D-vs-wood contrast cannot be reproduced by renaming effects. 21,218 published OTUs are NOT an observed species-row count verified by this gate.

No old BETA-FOR99 one-shot retuning, BETA-FOR234 no-files bypass, PREDICTS/Finland/Slovakia/Sweden/BALA/Island scorer reopening; no eBird/TinyFish. PR #469 stays draft and main unchanged.
