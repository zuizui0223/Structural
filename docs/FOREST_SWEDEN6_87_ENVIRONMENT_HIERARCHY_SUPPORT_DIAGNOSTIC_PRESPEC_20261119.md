# Sweden SLU original 87 environmental observations: diagnose coverage, do NOT chase eligibility (2026-11-19)

## Already failed gates, never retroactively overwritten

1. [#44454005463](https://github.com/zuizui0223/Structural/actions/runs/44454005463) stopped because original species header has 7 rather than README-stated 6 fields.
2. [#44454288129](https://github.com/zuizui0223/Structural/actions/runs/44454288129) diagnosed the original 7-field semicolon header in a separately frozen header-only source; corrected full three-file header gate #44454611956 passed.
3. [#44454981572](https://github.com/zuizui0223/Structural/actions/runs/44454981572) original climate nonresponse QA stopped because README-stated "88 rows" actually includes one header. [#44455179126](https://github.com/zuizui0223/Structural/actions/runs/44455179126) independently confirmed **87 data records**; byte and CSV width checks.
4. New source-only 87-row [#44455503628](https://github.com/zuizui0223/Structural/actions/runs/44455503628), artifact #14497666560 SHA256 `bbd04b5b9b392544579db679cc19415b3e3fa230d3c6402e2649dbc5e4711d9a`, returned **`SLU_CLIMATE87_PLOT_SHADE_AUTHOR_SOURCE_NONRESPONSE_ADMISSION_STOP`**. The problem is therefore **not only header/row counting**: some original block/plot/shade eligibility criteria remain unfulfilled. No CTI/richness/abundance or original beetle row was accessed.

This is the third related method-gate hurdle. **Do not try a fourth unreasoned change.** Diagnose actual source nonresponse support with original frozen climate 7019B SHA256 `d546273c352fb2cab97f63f35883f970baea09790348fa4c0dda3e1bc55ba776`.

## One original nonbiological accounting-only check

Recompute the unchanged original climate nonresponse parser's 87-row diagnostic and **export only** its complete anonymous source support counts: actual 6 blocks, unique plots, plot×shade keys, missing nominal 90 cells, minimum number of plots per block, minimum number of shade levels per original plot, per-block row/plot/shade counts, and numeric environment `Mikrotemp, Makrotemp, Bark, Diameter, Regional climate, Aspect` missingness and within-block variation. No original plot locality IDs, raw source field rows, coordinates, taxon/CTI/richness/totalab or beetle values exported. This is a **diagnostic of input sufficiency**, not a different ecological hypothesis or new source admission threshold.

Report the exact named failed gate(s) versus the **previously locked** conditions of 6 blocks / 30 plots / 87 triplets / exactly 3 missing nominal cells / min 4 plots per block / min 2 shades per plot; do not relax any. If a source group genuinely violates fixed scientific support, mark the planned six-block matched environmental model **HOLD/NOT ELIGIBLE**, even though publisher had described 30 plots. No positive/no-effect biological claim, no new endpoint until independently justified data.

Keep all earlier GitHub PR #469 frozen PREDICTS, Finland142, Carpathian116, Thailand, England NFI, NEON, BALA, GEB; no eBird/TinyFish, no main merge.
