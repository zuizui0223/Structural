# SLU Sweden6 climate source 88-rows README vs original CSV: structure-only diagnosis (2026-11-19)

## Exact prior source STOP

The original *environment/nonresponse-only* source test [Actions #44454981572](https://github.com/zuizui0223/Structural/actions/runs/44454981572) completed CI SUCCESS but **scientific input status `SLU_CLIMATE_ORIGINAL_88_ROWS_AUTHOR_FRAME_STOP`** because the immutable author README stated `boreal_forest_climate_data` contains 88 rows while the authenticated exact 7019B climate file yielded a different number of **data records**. Archive artifact #**14497173359** ZIP SHA256 `5c27adcc4e205b6abc92010c6fb5363ba41679403dd01e86cdb083f1858878ce`. The script did **not** read any beetle source row or semantics of `CTI`, `Species richness`, `Totlab`, and did not produce ecological effects; it stopped after auditing environmental keys.

## New separate source-only physical row diagnosis before any biological access

1. Fetch only the **same official** SLU original `boreal_forest_climate_data.csv` bitstream `cac76f42-041f-489a-a568-7d92c0c7941d`, enforce 7019 bytes and SHA256 `d546273c352fb2cab97f63f35883f970baea09790348fa4c0dda3e1bc55ba776`, exact first-line 12-field semicolon header already verified.
2. Inspect **ONLY** source *file structure*, not source field cell values: count raw LF newline delimiters, whether file ends with LF, CSV grammatical **row count including first header** versus **number of data records excluding header**, and histogram of CSV field width per record. No original sample/block/plot ID values, temperature, bark, diameter, species CTI/richness/abundance, taxa, output row values, or original 3460-record beetle file read. Source data lines are parsed solely to count structure/width.
3. Report exact count with its distinction between data rows vs physical rows incl. header. Treat any discrepancy with the author's "88 rows" as a true **source catalogue semantics mismatch**, not an automatic error or permission to rescue a failed model. The 88-row numeric gate remains historically STOP.
4. If source grammar is self-consistent and response-sealed, a *separately frozen* original plot×shade nonresponse QA can use the empirically verified full data-row denominator, but cannot reclassify previously failed source-run outcome. The primary ecological test is still UNOPENED and not authorized.
5. All existing English NFI, Finland/Carpathian, PREDICTS, Thai/NEON, BALA/GEB scores unchanged. No eBird/TinyFish, no main merge.

Status `SOURCE_SWEDEN6_ORIGINAL_CLIMATE_PHYSICAL_ROW_COUNT_DIAG_ONLY`; no new biological result.
