# EOG → Structural paper-asset handoff (2026-11-22)

**Scientific owner: [Structural](https://github.com/zuizui0223/Structural).** EOG owns generic methods and cross-system methodological benchmarking; the stand-alone Structural paper and all ecological interpretations belong here.

## What was preserved

- **89/89 original EOG assets**, source Git blob SHA verified before any EOG cleanup.
- **70** files, mainly the manuscript, panels, source figure data and generated figures, already exist **byte-identically** in the canonical Structural tree.
- **19** alternate historical/old manuscript scripts and test files not byte-identical with current Structural code have been preserved unchanged in `archive/eog_structural_legacy_20261122/`.
- **No canonical Structural file was overwritten** to reinstate old versions. Historical source metadata and the complete immutable Git manifest are preserved.
- The old EOG methodology code, real-data comparator benchmarks, negative controls, frozen protocol receipts, and EOG-WF three independent endpoints remain intact in EOG.

## Interpretative status

A-Islands original constrained-graph concordance was **0.6177466** across 845 taxa, but **strong-reference** comparison on the Structural mainline was adverse: `C-R3=+0.0034852` log-loss (95% CI +0.0024664 to +0.0045082; lower is better). Tanzania heldout comparison was also adverse beyond the reference. The independent biological conclusion is therefore **reference-conditional**; these results do **not** prove a general predictive advantage of structural graph information.

Refer to the [Structural README](../README.md) and authoritative source-specific manuscripts. The original EOG conditional methods tests remain method evidence only, with no new scoring from this migration. Historical paper tests archived here are not automatically run against the newer Structural architecture.

## Audit

[Immutable original-source manifest](../archive/eog_structural_legacy_20261122/SOURCE_MANIFEST.json). Run `python scripts/verify_eog_structural_legacy.py` to verify all 19 historical archived files; canonical 70 were independently matched at the handoff point and may change thereafter as part of the active Structural scientific programme.
