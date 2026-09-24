# GIFT global archipelago study — pre-response design

Status: **response sealed**. This branch is a separate prospective macro-study and does not alter the frozen Structural manuscript or create a new Structural gate version.

## Frozen design boundary

- data release: GIFT 3.2;
- target: native Angiosperm incidence on individual islands;
- quality filters: `complete_taxon=TRUE`, `complete_floristic=TRUE`, `native_indicated=TRUE`, `suit_geo=TRUE`, public lists only;
- closed-system exclusion: A-Islands v1.0 overlap is determined from verified geometry only; any contaminated GIFT archipelago path is removed before response access;
- archipelago grouping: full non-null GIFT `arch_lvl_1/2/3` path;
- minimum final archipelago size: 16 predictor-complete islands;
- primary isolation metric: GIFT `dist`;
- H1 extreme-isolation rule: global upper 25% of the complete frozen eligible-island universe; 70% and 80% thresholds are non-rescuing sensitivity analyses;
- spatial validation: four deterministic MST blocks within each archipelago;
- graph radii: 25, 50, 125 and 250 km, inherited from the frozen A-Islands design;
- model: one species model per archipelago, deterministic ridge logistic regression (lambda=1), with 5/5 training-class gates;
- inference replication unit: archipelago, not fold and not species.

## Evidence firewall

GIFT's checklist API returns complete list contents and does not provide a server-side `work_ID` response filter. Therefore a species-hash split cannot provide a strict response firewall.

The evidence split is instead **archipelago/list-surface based**:

- burned pilot: one response-blind extreme-only group, one paired-regime group and one non-extreme-only group;
- confirmatory: every other frozen eligible archipelago;
- pilot and confirmatory `list_ID` surfaces must be disjoint;
- burned pilot may compute only species × archipelago × block estimability counts;
- pilot effect sizes, fitted comparisons and prediction scores are forbidden;
- confirmatory lists remain unopened until the pilot gate passes.

## Hypotheses

**H1 primary.** Candidate-minus-R3 held-out loss is more favourable on globally extreme-isolation islands. Archipelagos are resampled as intact clusters for inference.

**H2 primary.** The extreme-regime topology increment becomes less favourable as the archipelago's fraction of GIFT `GMMC=1` islands increases.

**H3 secondary confirmatory.** The H1 contrast differs by the predeclared GIFT dispersal-syndrome grouping. Missing trait values affect H3 only.

**M4.** Current climate and standard island-isolation/environmental context are supplied in the frozen strong reference. A residual topology increment is not interpreted as proof that every environmental alternative has been excluded.

## Hard boundary

No checklist/species-composition endpoint may be opened until the metadata census, A-Islands exclusion, intake, predictor-complete universe, M4 metadata audit and study-protocol fingerprint all replay exactly on the same pre-response commit.
