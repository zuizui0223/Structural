# BELongDead author alias/log naming source gate — executed result (2026-11-17)

## Actually completed

The original Biodiversity Exploratories source catalogue identifies BExIS 13930/tag3 (Alias numbers), 16846/tag1 (Changes in log naming), 16427/tag2 (Subplot naming) and 16390/tag1 (Instrumentation 2009/10). [Official catalogue](https://www.biodiversity-exploratories.de/en/projects/arthropods-i-land-use-above-ground-arthropod-diversity-and-arthropod-affected-processes/).

A separately committed [source-only prespec](FOREST_BELONGDEAD_AUTHOR_ALIAS_NAMING_SOURCE_GATE_PRESPEC_20261117.md) was frozen before the runtime. [Actual GitHub Actions #44102672012 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/44102672012). Synthetic source-value-redaction test PASS, exact original publisher metadata/rights and dictionary checks PASS. Original CI artifact #14335919340, ZIP SHA256 0cb1ec459ec3848341c1c081e64d77262ad43fdd1370b53d8f7df92624c5ba8e. Each of the four official publisher dataset, published-tag metadata and DataStatistic dictionary endpoints returned HTTP200, with recognizable open license.

The publisher DataStatistic dictionaries may describe the LATEST file version; byte-level agreement with the original published tag is not yet verified. The source data files/rows were NOT downloaded or parsed. Only original field names and descriptions were inspected transiently in the runner. Source names, identity labels, original field values and numerical statistics were NOT exported.

## Safe original variable-dictionary results

| Author source | Publisher field count | Predeclared method-name/description lexical families | Strict current decision |
| --- | ---: | --- | --- |
| 13930/tag3 – Alias numbers | 5 | 0 alias, 0 log, 0 plot, 0 trap, 0 effort pattern matches | Dictionary-only HOLD; abbreviated field codes may still be informative |
| 16846/tag1 – Changes in log naming | 12 | 8 log/stem, 3 plot/subplot, 1 year/time, 0 trap, 0 explicit effort | Potential LOG identifier provenance, not a TrapID alias |
| 16427/tag2 – Subplot naming | 7 | 3 plot/subplot, 3 log/stem, 0 trap, 0 explicit effort | Subplot identity candidate only |
| 16390/tag1 – Instrumentation 2009/10 | 13 | 2 trap/instrument, 2 plot, 2 log, 3 year/time, 0 explicit effort | Method field candidate only; instrument is not guaranteed trap occasion |

Zero lexical matches DO NOT demonstrate that aliases are absent, because original author naming can use abbreviations or languages outside the prespecified scanner.

## Specific current scientific boundary

The original BELongDead 31123 beetle source contains 30 physical forest plots / 379 experimental logs / 13 offered wood host types. Its 31124 author complete-log table has exactly 15 extra six-field method keys not in 31123, although 15/15 match their parent log×host×year context. These 15 TrapID keys are STILL NOT RECONCILED. A dataset titled Alias numbers or Changes in log naming cannot itself prove that the 31124-specific TrapID tokens refer to 31123 trap occasions. The 2009/10 instrumentation record does not establish per-trap effort through 2017.

Separate original source BExIS24546 matches ambient deadwood at all 30 physical plots in 2012, but deadwood DWV uses m3 and m3/ha across different author-defined strata. No raw-unit pooling, year alignment or causal wood supply inference is justified by today's method gate.

The next scientifically justified SOURCE-ONLY step is separately precommitting a narrowly scoped first-line and exact published-tag header audit of 16846 and 16390. Explicit author semantic field definitions, rather than filename or fuzzy field matching, would then determine whether a valid log/trap/time crosswalk can be frozen. Capture-incidence inference still separately requires all deployment opportunities, including empty catches.

## Protected results and implementation

Prior Finnish deadwood Host_tree heldout gain +0.00024237; Chiu one-German-forest host identity heldout gain +0.019699892 (6/6 parent plots, p=.03125); Piccini German floor guild gain direction +11.7% but p=.09375 unsupported; PREDICTS forest turnover +0.0942 and NEON height guild p=.1759 unchanged. No cross-country hostwood×feeding-guild confirmation was added.

Source runner: analysis/forest_macro_global/belongdead_author_alias_naming_source_gate.py. Workflow: .github/workflows/forest-belongdead-author-alias-naming-source-gate.yml.

Verification: 4/4 original publisher variable dictionaries accessed; original 31124 TrapID keys resolved 0/15; new organism outcome reads 0; newly scored ecological effects 0; independent external-country feeding-guild replication 0. BALA and mammal GEB sealed; no eBird, TinyFish, main merge, author communication or PR merge. PR #469 remains Draft.
