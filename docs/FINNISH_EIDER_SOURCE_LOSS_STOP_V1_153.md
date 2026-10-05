# Finnish common eider source-loss lane — terminal schema stop v1.153

The Finnish common-eider dataset remains valuable ecological context, but it cannot support an auditable Structural source-loss leverage stress test from the public archive as currently released.

## What the response-free audits established

Zenodo resolves the concept DOI to one concrete version containing exactly one 2.23 MB tab-delimited file. A header-only audit opened no data rows and found exactly 11 columns:

`Eider_pairs, lnSize, Year, Lon, Lat, Land, WTE, Forcov, Island_ID, Year_f, pos2`.

Thus:

- `pos2` is present inside the mixed response/covariate table;
- there is no separate spatial file;
- there is no row-level grouped-island redistribution flag;
- there is no survey-effort or surveyed/not-surveyed flag in the table.

## Why the lane stops

The published methods state that some counts reported for groups of islands were redistributed to individual islands, affecting about 6.2% of observations per year. For a source-loss analysis, island identity is the event itself. A redistributed count can therefore create or remove an apparent occupied source island.

Because the only public table has no row-level flag identifying those redistributed observations, Structural cannot prospectively exclude them without examining response-value patterns or acquiring an external reconstruction key. Both would violate the frozen retrospective gate.

The dataset is therefore stopped **before any row-level response value is semantically opened for the Structural source-loss analysis**.

## What this stop does not mean

It does not imply that the published eider analysis is invalid. The published study asked a different question and explicitly described the redistribution procedure.

It means only that the released table is not sufficiently provenance-rich for the narrower Structural question:

> did loss of a particular occupied island source precede a later contraction elsewhere?

That question requires exact island-level state transitions whose provenance is auditable.

## Current conservation evidence after the stop

- ultrarare mammals show prospective topology-specific occurrence information in one geographic system;
- a response-free mammal diagnostic shows that nominal source count and source leverage are not equivalent;
- the independent BALA three-wave test did **not** validate source leverage as a general predictor of later contraction;
- Finnish eider cannot provide an auditable retrospective source-loss test from the current public archive.

The conservation claim therefore remains deliberately narrow: source configuration can matter for occurrence, but source-leverage ranking is not validated for management prioritization.
