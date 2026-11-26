# Ecuador Chocó experimental host logs — source-only intake and next beetle ecology test (2026-11-22)

## Current authorized decision

The Falconí-López et al. 2026 field experiment is a **candidate independent original source**, not new ecological validation yet. Do not open any beetle/OTU rows until a physical log × plot × tree-species × recovery-stage identity and exposure crosswalk is certified. This source was already analyzed in a published paper; any subsequent Structural analysis is **retrospective exploratory**, not pristine confirmatory.

Original publication: Falconí-López A. et al. (2026), *Forest Ecology and Management* 619:124102, DOI 10.1016/j.foreco.2026.124102. Publisher reports 62 plots across 7 source habitat strata (pasture 6, cacao 6, pasture early 9, cacao early 10, pasture late 8, cacao late 7, old-growth 16). Exactly five log-host types were offered per plot (310 deployed); 306 logs recovered. Original authors report 91 beetle species / 10,650 individuals, 43% recovered logs with no adult emergence, and ~96% individuals Scolytinae. Those numbers are **published findings**, not source records reprocessed by this branch.

## Reconcile inconsistent publisher Figshare URLs

- Publisher HTML data-availability text: `https://figshare.com/s/80ba8b612162e4a7ace7`
- Publisher PDF data-availability text: `https://figshare.com/s/80ba8b61262e4a7ace7`
- Treat as **two conflicting published identifiers**, not as evidence that either URL resolves to the correct files. Record HTTP status/redirect/canonical metadata for both without following unverified file downloads. A public Figshare API title search may provide **metadata only**, and an absent public API record does not prove the private-link data do not exist.
- No private token, logged-in session, credential bypass or mirror download. STOP if unavailable.

## Scientific question separate from prior art

Original authors ALREADY analyzed recovery-stage gradients in beetle abundance, species richness, host network diversity and specialization, and differences among wood densities. Do **not** claim any of those as novel Structural results.

The distinct, prospective *analysis goal* is: Does standardized host-tree identity add held-out information for (A) beetle emergence occurrence and (B) detected species composition once recovery stage is represented, and is the added value conditional on recovery stage?

The core ecological contrast is **colonization/emergence gate versus conditional assembly**, not 'more trees → more beetles'. A positive result would be incremental within-one-landscape predictive evidence only; it could not identify dispersal, resource supply outside the placed logs, microclimate causality, population persistence, or cross-biome generality.

## Required original nonresponse admission (must PASS before opening species)

1. Original immutable source version, license, file names, sizes/hashes and author codebook; archive GET permission and whether downloaded files are public. Metadata-only checks may report filenames and lengths but never species/log values.
2. Unique physical plot IDs (62 published) and one-to-one valid log ID per deployed `plot × host_tree`, recovered/missing log frame (310 vs 306); do not silently infer which four logs were lost.
3. Exact labels for seven habitat strata, date/wood-exposure/emergence-chamber effort for recovered logs; missing traps/exposure cannot become observed zero emergences.
4. Original biological row key to log ID, source taxon identity level and possible duplicate specimen rows, ***only after*** predeclared sample-frame gate.
5. Only if plot identities and stage balance support heldout evaluation, freeze plot-level train/test predictions and two-part target ontology **before** biological row access. Repeated logs from the same plot are not independent forests. Block definitions cannot be chosen based on observed beetles.

## Future comparison if admissible (NOT yet scored)

- Y1: recovered-log adult-emergence indicator (observed true no-emergence counts vs structural missing distinguishable); primary scoring e.g. heldout log loss under *leave-one-plot-out*, with plot-equal weighting and no leakage across the five log hosts.
- Y2: species composition conditional on at least one emergence, using one frozen species/OTU resolution and a predeclared zero/detection policy, with per-plot heldout multivariate proper score.
- E0: original recovery stage + predeclared nonresponse plot context/effort.
- E1: E0 + five-level offered host-tree identity (or a separately frozen density operator, but not both searched).
- E2: E1 + host-tree × recovery-stage interaction, with shrinkage specified before scoring; difference E1→E2 must not be selected because of a favorable Y1 or Y2 result.
- Report beetle richness/total counts and Scolytinae share as **diagnostics only**; 96% ambrosia-beetle dominance makes abundance-only interpretation especially vulnerable. If Y1/Y2 source completeness fails, report only a method/data HOLD.

**Evidence boundary:** This new source is not comparable by pooled effect size to Finland142 Host_tree guild, Germany Chiu host-identity species-composition, Slovakia trophic guild non-support, NEON canopy-height non-support, or BETA-FOR99 OTU beta. Existing frozen scoring and BALA/GEB/mammal evidence untouched. No eBird or TinyFish. Draft PR #469 only; no submission or main-branch merge.
