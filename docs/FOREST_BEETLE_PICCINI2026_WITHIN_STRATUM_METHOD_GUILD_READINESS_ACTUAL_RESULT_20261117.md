# Piccini 2026 3-layer beetle source: author site/stand nesting PASS, trap effort and functional guild response NOT YET ELIGIBLE (2026-11-17)

## Final result — new original field method evidence only

Original German Piccini 2026 field source [GRO.data DOI 10.25625/H8EMJS](https://doi.org/10.25625/H8EMJS), paper [DOI 10.1111/1365-2664.70472](https://doi.org/10.1111/1365-2664.70472). Latest corrected **source-only original CI [#43901051028](https://github.com/zuizui0223/Structural/actions/runs/43901051028) SUCCESS**, original source metadata and MD5 checks PASS, tests PASS. Artifact **14242105684**, workflow artifact ZIP SHA256 **59f6fdee1e8f1887ca41544e8ff42f206f241053938434c28352603247ba72c5**. The estimator selected only original site/stand/plot/stratum/period/method fields; no original species name, feeding-guild category, abundance, native/exotic response, wood resource or beetle functional score was accessed or exported. The result is a SOURCE-METHOD classification, NOT evidence of a new ecological effect.

| Original source method data (author name identity) | Actual anonymous result | Interpretation |
| --- | ---: | --- |
| Original checksum verified method rows | **22,414 / 22,414** | Source response rows, NOT trap/sample opportunities |
| Named parent sites / forest stand types / plot labels / stratum labels | **8 / 5 / 40 / 3** | Hierarchical design; a parent site is a geographical blocking unit |
| Site×stand×stratum cells / plot×stratum pairs | **120 / 120** | Complete named combinations in positive-record source |
| Plot labels nested across incompatible parent-site or stand identity | **0 / 0** | Author method IDs consistent at this resolution |
| Source plot×stratum×period label combinations | **628** | Tokens NOT calendar years or equal effort |
| Source strata-positive-record rows (anonymous sorted) | **2,899 / 3,670 / 15,845** | NOT independent trapping units, abundance or biodiversity |
| Source plot×period positive-recorded context counts by stratum (sorted) | **159 / 196 / 273** | NOT an exhaustive list of zero-capture traps |
| Original safe generic trap-like field names | **trap / trapid / trapid** | Two distinct original headers normalize to trapid; role identification ambiguous |
| Distinct recorded labels across those three source fields, sorted | **8 / 320 / 557** | NOT 8, 320, 557 independent trap deployments; semantic hierarchy unverified |
| Original method field / sampling effort field / sample ID field matched to explicit generic header | **0 / 0 / 0** | No field-defined trap-days, duration or complete zero-event denominator |
| Original taxon header / feeding-guild header / abundance header | **present / present / present** | Header presence does not certify taxon↔guild mapping or fitness for analysis |
| Newly scored beetle guild effect / p / beta / host wood effect | **0** | No biology opened or regressed |

The three source trap-like columns were all nonmissing in the positive-recorded rows, with distinct label counts 8, 320, 557 respectively. At the plot×stratum level each source trap-like column had between 2 and 8 distinct recorded labels (median 3), but a record list can omit no-capture traps and cannot be interpreted as complete effort. One field reuses a small label vocabulary across all plot strata; another has repeated labels across plot strata, while the 557-label field does not reuse its labels across plot strata. **Do not select the 557-label field as the actual unique trap unit merely because its values are distinct.** The original author codebook must establish physical trap, vial, sampling unit and period mapping.

### Test chronology and implemented repair boundary

1. New prespec: [within-stratum original trap/guild header readiness protocol](FOREST_BEETLE_PICCINI2026_WITHIN_STRATUM_METHOD_GUILD_READINESS_PRESPEC_20261117.md), committed before source run.
2. First source-only run [#43900661963](https://github.com/zuizui0223/Structural/actions/runs/43900661963) performed no biology but returned **SOURCE_STOP_HEADER_SHAPE_OR_DUPLICATION**, because new code wrongly required all 17 normalized header strings unique, even unrelated nonselected fields. The existing original 8-site/5-stand/40-plot model was not affected.
3. [Source-only correction prespec](FOREST_BEETLE_PICCINI2026_METHOD_HEADER_SCOPE_FIX_20261117.md) recorded the error before repair. The second synthetic-only run failed because of newline escaping in the new test code; there was no original source read or ecological score in that failed run.
4. The corrected [CI #43901051028](https://github.com/zuizui0223/Structural/actions/runs/43901051028) passed synthetic duplicate-nonselected versus duplicate-selected controls, full source retrieval with published MD5, and original method-only audit. **Scientific status:** SOURCE_TRAP_ID_ROLE_UNRESOLVED_OR_MULTIPLE. The test executed successfully but the source is not yet eligible for a clean trap-effort-adjusted biological effect. Original author site×stand×stratum nesting remains verified.

### Why the STOP is scientifically appropriate

- The source lacks a uniquely named actual trap unit and explicit trap-day/complete sampling-opportunity field. Even though the paper states field sampling methods, 22,414 source records are detected biological rows, not the 2019 pitfall and 2019/2021 FIT deployment ledger.
- Three different trap-like source headers cannot be merged or interpreted by their column cardinalities. The 2026 article reports different sampling years and collection methods across strata and four storm-associated changed plots, so stand/plot identity cannot prove same physical canopy tree at every time.
- The original German field paper already analyzed tree identity, stratum and feeding guild patterns. A renewed positive stand×guild association in this same dataset is **not independent ecological replication** or novel causal evidence.
- Published feeding-guild classes cannot be identified with Finland/Burner Host_tree broadl/conifer/both without verified functional trait definitions. An abundance header alone does not establish complete zero-event effort.

## Decision: what is now ready and what stays sealed

**READY:** 8 parent sites × 5 stand types, 40 author-defined plot labels and 120 plot×stratum positive-recorded panels, with source checksum and known nested site IDs. **NOT READY:** actual trap/sample incidence grain, zero-capture sampling opportunity and trap-day denominator, taxon↔feeding-guild semantic mapping, 2019–2021 storm plot replacement crosswalk.

**Next discriminating source-only requirement:** the original authors' codebook of the three trap-like columns and an independent list of all installed/captured/zero-capture trap×period units (or a documented effort-standardization rule). Validate unique physical trap keys and source period/year mapping WITHOUT opening biological response values; otherwise stop this 2026 network and prioritize a distinct forest survey with explicitly measured host trees, trap effort and functional species guilds. This is not a prompt to re-run alternate thresholds on the same exposed biology.

Original Finland142 deadwood Hellinger² +0.00024237 (conditional p=.0150), original three-country Host_tree trait-label D+.091059 (conditional p=.000333), PREDICTS +.0942, Thai original 18-station paired beetle excess, NEON non-support, BALA 7-island temporal positives and GEB mapped-mammal scientific HOLD all frozen unchanged. **No new original mammal/forest species heldout read**, no eBird/TinyFish, PR #469 Draft unmerged.
