# ALA v1.194 terminal stop — source pairs were opened but no biological score exists

The independent ALA positive-location attempt progressed beyond its predeclared support gates (50 pairs, 10 species, 15 islands, 5 spatial blocks). That follows from the frozen code's execution order: `read_predictions` is called **only after** the external FID/species/eventDate pairs are decoded, deduplicated and counted against every support threshold.

The run then failed before scoring any ecological endpoint:

`STOP_ALA_EXTERNAL_PAIR_SCHEMA_OR_FROZEN_INPUT_DRIFT: prediction shape drift`

The direct cause is a mistaken binary-header reader: the original frozen R3/C prediction artifact stores **two header dimensions** `(4126,529)` and a `(4126,529,2)` float64 payload. The v1.194 reader expected three header integers for that file. Consequently it misread the first probability bytes as a third dimension.

**This does not support or falsify the biological hypothesis.** In particular, the ALA data were not converted to an independent ecological result. The original held-out mammal labels were never reopened; original predictions and matched nulls were never refitted. The external ALA record pairs *were* read before the technical error, however. The exact qualifying-pair count was not saved before the reader failed.

The preregistered one-shot/no-rerun rule therefore applies. Do not correct v1.194 and retry on the same ALA archive. The correct code format can be documented and tested synthetically for **future independent data**, but no new ecological claim may arise from this consumed lineage.

This is also a useful design failure mode: freeze and validate **all** scientific prediction file headers, dimensions, hashes and model comparisons **before opening any external species-by-island outcomes**.

Ecological evidence remains: one IUCN-derived island-occurrence matrix supports a within-source geographic-kNN predictive increment among the 529 sparse mapped-species layer, source identity turnover v1.181 was lower than matched random, and temporal BALA leverage was unsupported. Independent biological confirmation is not obtained.
