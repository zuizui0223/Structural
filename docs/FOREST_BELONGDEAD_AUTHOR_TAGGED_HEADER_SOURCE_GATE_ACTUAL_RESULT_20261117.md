# BELongDead author source original published tag file integrity and schema: actual result, 2026-11-17

## Completion

[Executed GitHub Actions #44103777457](https://github.com/zuizui0223/Structural/actions/runs/44103777457) was source-only: the precommitted synthetic redaction test and both original publisher tagged-CSV header checks passed. Artifact #14337097673, ZIP SHA256 53c0ebd5da79f56930cd5cb82cb93a7e30e7f2e74c077c601733f78caaa537b2.

The script first independently SHA-verified original publisher /api/dataset and published-tag /api/metadata against the prior four-dataset source audit, verified public rights, then downloaded ONLY two specifically allowed publisher original tagged files. Their first physical CSV header lines were semantically parsed; **all subsequent bytes were streamed for SHA256 and never parsed or exported**. This is a source authenticity / first-header-only result, not an organism test.

| Source / exact publisher tagged file | Original file bytes | Exact tagged original file SHA256 | Header fields | Strict original first-header lexical families |
| --- | ---: | --- | ---: | --- |
| 16846/tag1 Changes in log naming | **46,011** | a542009e4551b7dfbe24e86cae7554ecc20be089bff3507342e2cef118635d30 | **12** | **7 log/stem**, 3 plot/subplot; 0 trap/instrument and 0 explicit effort/zeros |
| 16390/tag1 Instrumentation 2009/2010 | **31,707** | 0769ae05c165efa3bbfec22de9c510b80e9f09ed22a641a95be3907507306e32 | **13** | 2 trap/instrument, 2 plot/subplot, 1 log/stem; **0 explicit effort/zeros** |

Source dictionary lexical family counts from the previous run were 8 log, 3 plot, 1 year for 16846 and 2 trap/instrument, 3 date/year, 2 plot for 16390, but those match *dictionary name PLUS description*, not just original tagged CSV headers. This is why dictionary counts and original header-only counts are not identical; it is NOT schema inconsistency. Both tagged header field counts match the previously observed corresponding original publisher dictionary counts (12, 13). The original dictionary may reflect latest rather than tagged original, so author field definitions still require exact version verification.

### What is genuinely resolved

- Original licensed files for two method-source candidates are obtainable at the **published tag**, without alternate transports or authorization workarounds.
- Both exact original tagged file fingerprints and first-column counts are frozen, so future methods work can reference original source versions rather than changing latest.
- The raw original source beyond the first header was not parsed: no published old/new mapping, individual plot/log/trap IDs, beetle species/capture records or stand wood values were read or exported.
- Original BExIS31123 vs 31124 **15 unmatched trap IDs remain unresolved**. The 16846 original file is explicitly LOG-naming-related and has zero trap-pattern header candidates; it cannot be treated as a TrapID alias table. The 16390 file has two trap/instrument-pattern columns but describes 2009/10 instrumentation, and neither original header identifies a zero-catch/deployment frame through 2017.
- **No new biological effect**, no host-resource feeding-guild country/biome replication and no permission to reopen 31123 species outcomes were created.

The earlier original 13930/tag3 author Alias numbers and 16427/tag2 Subplot naming records remain publisher-dictionary-only checks; original tagged source files were not opened. Their title alone cannot establish trap aliases.

## Decision / next input

Author-source methods still need an **explicit semantic mapping between original 31123/31124 TrapID tokens and the actual log×year deployment/zero-capture opportunities**. Further header-word matching, blind conversion of ID strings or within-dataset outcome subset changes would not solve that identified source limitation. If a published author-original field mapping is discovered later, freeze it independently before any original method-row crosswalk; otherwise classify BELongDead hostwood×guild effect scientifically NOT IDENTIFIABLE.

Scripts: analysis/forest_macro_global/belongdead_author_tagged_header_source_gate.py and analysis/forest_macro_global/belongdead_author_alias_naming_source_gate.py. Two workflows: .github/workflows/forest-belongdead-author-tagged-header-source-gate.yml and .github/workflows/forest-belongdead-author-alias-naming-source-gate.yml. Source prespecs and actual results frozen on Draft PR #469 only; main unchanged.

Prior Finnish 142-site +0.00024237, Steigerwald Chiu 6-plot host identity +0.019699892 (6/6 p=.03125), Germany Piccini 8-site directional +11.7% p=.09375 unsupported, PREDICTS +0.0942, NEON CHM p=.1759 unsupported, long-term BALA and GEB historical holdouts all unchanged and sealed. No eBird or TinyFish.
