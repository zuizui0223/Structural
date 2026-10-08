# Source-response ontology audit: global mammal islands (v1.187)

## Result: the endpoint is a mapped-range proxy

The original source study (Barreto et al. 2021, *Proceedings B*, DOI 10.1098/rspb.2021.1879) generated island-by-species entries by overlaying GADM v3.6 island polygons and 2017 IUCN mammal range polygons. The authors manually examined and corrected uncertain intersections and removed ambiguous islands, invasive taxa and marine mammals. That work is a carefully curated **range-derived macroecological matrix**, not a uniform island field-survey census.

A crucial temporal complication is documented by the authors: some **historically native mammal occurrences lost through human extinction were added from other records**. The public 0/1 matrix does not supply a frozen species×island flag by which Structural previously separated these historical values from currently extant source populations.

Consequently a positive cell means **positive in the curated, IUCN-derived/augmented range matrix**, not necessarily a directly observed, presently extant population on that island. A zero is not a standardized surveyed non-detection. The numerical validation of those labels remains legitimate internally, but the biological meaning must be stated precisely.

The source paper compared richness summaries against independent regional sources and reported a high correlation (0.95 ± 0.05). That provides meaningful *richness-level* corroboration, not proof that each species×island entry or reconstructed extinct status is contemporary.

## Joint construction risk

The Structural predictor graph was generated from the same spatial island geography using region-wise symmetrized minimum-connected kNN edges. Held-out island blocks are withheld from model fitting, but **source polygons and target labels arise from one shared IUCN range-mapping process**. Neither spatial block separation nor 20 degree-/edge-length-bin-preserving rewired graphs removes this shared map-generation structure.

The supported inference is therefore:

> Geography-derived graph features incrementally predict mapped mammal positive cells beyond Euclidean-source and island-environment controls within the same curated source matrix. In the frozen 1–4 mapped-positive pilot layer, the original geographic kNN graph beats 20 matched rewired alternatives on positive-cell log loss.

It is not yet:

> Exact natural dispersal topology determines where living ultrarare mammal populations are present.

In particular, a mapped species occurring on 1–4 frozen pilot islands does not imply only 1–4 surviving global populations, nor that each mapped source is extant.

## Falsifiable independent validation

Hébert et al. 2021 (DOI 10.5061/dryad.rfj6q579r) provide species×island checklists for 204 islands in nine archipelagos assembled largely from published mammal literature, regional checklists and atlases. Some sources, especially the Gulf of California table, cite IUCN as well. Therefore the dataset is **partially independently compiled**, not demonstrably independent for every species cell.

Before decoding any checklist 0/1 values, require:

1. Immutable freeze of candidate island identities and species name matches to original ultrarare predictions; only original **4,126 held-out islands** can be scored, never pilot training islands.
2. Exact and unambiguous island identity plus species identity; no outcome-based mapping, subsampling or synonym selection.
3. Source-provenance audit, including IUCN-derived/checklist overlap and independent versus shared reference status.
4. A predeclared minimum testable coverage before any checklist response is opened.
5. Predictions (p_{R3}) and (p_C) must be reused verbatim from the frozen original run, with no refitting, graph revision or target-specific threshold search.

Fail the gate if identities cannot be linked; do not substitute species-pooled richness or subjective island names to rescue the test.

## Publication gate

The current GEB manuscript remains a draft, but **its ecological-mechanism and source-population interpretation is on scientific HOLD** until an independent species-level check qualifies. Never turn the within-map result into a measured connectivity, colonization, rescue or source-priority claim.

v1.181's adverse source-turnover result and BALA's adverse temporal source-loss test remain exactly as frozen. eBird is disabled.
