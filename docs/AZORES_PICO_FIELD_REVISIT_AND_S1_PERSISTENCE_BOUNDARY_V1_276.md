# Pico field evidence, source identity and limits of local-persistence inference (v1.275–v1.276)

**Verified 2026-10-22. Main decision: retain source-confirmed island-year positives; no same-location population persistence or colonization mechanism inferred.**

## Why this was necessary

Macaronesia S1 (original CSIC DOI `10.20350/digitalCSIC/17024`) has 24 strict Well-supported island extirpation cases for 20 Azorean taxa. Independently dated PRIBES field observations at four islands in 2019–24 documented 12 of those 20 affected taxa elsewhere, with seven appearing on two or more surveyed islands. On Pico, 11 of the 20 are documented by field observations, of which eight appear in two or more calendar years, two in three or more. These are *positive observational records*, not standardized annual site occupancy, individual fate or demographic rescue. See original validated runs [four-island v1.271/v1.273](https://github.com/zuizui0223/Structural/actions/runs/39417672322) and [Pico multi-year v1.274](https://github.com/zuizui0223/Structural/actions/runs/39418418784).

## Exact original Pico Event-only site audit (not new biological outcomes)

The original Pico PRIBES v1.7 dataset (DOI `10.15468/vk4y7k`, fixed SHA256 `82406dbcb48e188cca6bca116437b951a80f613faadf44a173ddd5d9b92e4a02`) comprises 2,801 Event-core rows with author-proven M/D/YYYY dates: 171 in 2020, 1,603 in 2021, 898 in 2022, 129 in 2024.

Original Event-core fields **do not include author `locationID`**. All 2,801 Event records have valid geographic coordinates and declared samplingProtocol fields, but there is **no source-defined permanent site key**. Event identifiers cannot substitute for repeated sites. Without opening any biological Occurrence extension records, a pre-frozen matching audit found:

| Physical repeat proxy | Separate locations with original Event rows in at least two calendar years |
|---|---:|
| Source-defined author locationID | **not provided** |
| Exact lat/lon rounded to five decimals | 5 |
| Rounded to four decimals | 20 |
| Rounded to three decimals | 30 |

This large precision dependence shows that merging sample locations changes apparent site-level longitudinal support. Five repeated GPS coordinates do **not** imply five species, five viable source populations, or even five validated permanent plots. Source coordinates have non-empty uncertainty fields; precision does not override original positional uncertainty. Source-only six-test regressions and all original 2,801 dated event checks passed in [run 39713271468](https://github.com/zuizui0223/Structural/actions/runs/39713271468).

## Species × same GPS × year was not scored

An explicitly post-outcome exploratory follow-up frozen in `development/azores_Pico_spatial_recurrence_protocol_v1_276.json` defined a primary outcome: among the eight affected taxa with positives in two or more Pico survey years, how many have positives at the *same* GPS coordinate to five decimals in two or more years? GPS4/3 are sensitivity checks only.

The original-source re-download failed with `urllib timeout` **twice** in [run 39713929210](https://github.com/zuizui0223/Structural/actions/runs/39713929210) (initial run and identical rerun). Synthetic test regressions passed after fixing a Python syntax error, but the original observation join was **not executed**. The result is **unknown, not zero**. No source SHA, matching rule or ecology endpoint was changed to get a favorable result. No additional uncontrolled URL polling should be used to replace this scientific evidence.

## Ecological conclusions still permitted

- Real dated field observations of historically local-loss-affected taxa elsewhere within the same archipelago are stronger direct occurrence evidence than the inherited 2010 nominal checklist `present` flag.
- Positive records in multiple years on Pico are evidence of repeated island-level detection, **not verified stationary populations**; the original published Event keys do not establish fixed-plot resampling.
- Across the full four-island scope, failure to record an affected taxon at its historically lost island is **not a surveyed absence or confirmatory local extinction**, because habitats, protocols, locality coverage and dates differ by island.
- Pre-loss donor abundance/viability, directed inter-island movement, establishment, genetic parentage, rescue effects, and a complete historical at-risk species × island denominator remain unmeasured.

For Structural, preserve the supported static occupancy-specific *predictive* result separately from biological rescue. Avoid extrapolating a causal conservation leverage ranking from these observational occurrences. Historic/extant list mismatches must remain data-provenance warnings, not inferred ecological recolonization.

**Main manuscript boundary:** no new confirmatory system admitted; GEB scientific HOLD; Macaronesia S2/S3/S4, earlier mammal, BioTIME and RLS protected outcomes remain unopened; eBird unused.

## Reproduction and frozen outputs

- Original Event-only study contract: `development/azores_Pico_event_site_revisit_protocol_v1_275.json`.
- Executed physical evidence + stopped biology receipt: `development/azores_Pico_site_revisit_inference_freeze_v1_276.json`.
- Regression-tested code: `scripts/azores_Pico_event_site_revisit_v1_275.py`, `scripts/azores_Pico_spatial_positive_recurrence_v1_276.py`.
- GitHub Actions site physical audit [success](https://github.com/zuizui0223/Structural/actions/runs/39713271468); species × site join [source timeout after tests](https://github.com/zuizui0223/Structural/actions/runs/39713929210).
