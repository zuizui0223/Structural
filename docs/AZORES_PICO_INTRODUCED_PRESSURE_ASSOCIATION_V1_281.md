# Pico historical-loss-affected native plants occur with fewer introduced species — MOVECLIM 2013 v1.281

**2026-10-23. NEW RETROSPECTIVE CROSS-SOURCE HABITAT ASSOCIATION, not a causal intervention or pristine confirmatory system.**

## Biological question and actual result

Do the Azorean native plants fixed from Orihuela-Rivero et al. S1 as having well-supported island-level local extirpation somewhere in the archipelago concentrate in parts of Pico's *already sampled, relatively intact native vegetation* with lower introduced-plant species richness, relative to other native taxa and within coarse elevation bands?

**The precommitted sign prediction was negative, and the executed result is negative.** Source-locked [GitHub Actions run 39904415725](https://github.com/zuizui0223/Structural/actions/runs/39904415725) succeeded, including four new synthetic regression tests, 58 author-defined 10×10 m plots, 232 subplots, all 2,539 original Occurrence records and the 20 strict affected species / 24 historic loss cases. The full biological result exists only as a named aggregate-only run artifact (ID 12480152663; ZIP SHA256 a3bace7a2ffb70c8a3752c7207824b1532a59392853a9dd779809f96ce73ad4c). The exact extracted JSON has SHA256 135a4c5f598f686ce3691d79aa0a59b427036128d8e99760321dbc3d4f208a27.

**Pico (24 original 2013 plots):**
- Five affected native taxa recorded across 26 plot×taxon incidences; 49 other native taxa across 266 incidences.
- 12 strictly introduced taxa, 27 introduced plot×taxon incidences, 11/24 plots with >=1 introduced taxon.
- **19** plots had >=1 native historical-loss-affected taxon, versus **5** plots with none. Introduced species richness averaged **0.7895** versus **2.4000**, respectively: difference **−1.6105 introduced taxa/plot**, descriptive plot-level comparison.
- **Species-equal-weighted comparison**, requiring at least two affected taxa and >=5 reference taxa: mean number of introduced taxa at the occupied plots of each focal taxon, averaged across the five focal taxa = **0.7400**; corresponding average across the 49 other native taxa = **1.1882**; frozen contrast **−0.4482 introduced taxa per occupied plot**.
- Residualizing the introduced count within each of two pre-frozen, 12-plot Pico elevation halves: focal residual mean **−0.9267**, reference mean **−0.4232**, difference **−0.5035**.
- Separate max-ordinal-OTV-per-introduced-taxon sensitivity: mean introduced OTV-sum at focal occupied plots **1.7400**, reference **3.3468**. Source OTV is an *ordinal* transformed cover scale, not percentage ground cover; do not interpret its difference as percent cover.

The two contrasts estimate different descriptive statistics. Plot-group comparisons are not independent taxa, and taxon-weighted exposure means are not 54 independent experimental interventions. The elevation-halves comparison is coarse stratification, not a habitat-matched causal design.

## Full four-island negative association as descriptive sign sensitivity

The predeclared secondary plot-level contrast (mean introduced richness on at-least-one-focal-positive plots minus no-focal-positive plots) is negative in each of four observational island frames:

| Island | 10×10 m plots | Focal native taxa | Introduced plot×species positives | Focal-positive plots | Focal-positive minus negative introduced taxa/plot |
|---|---:|---:|---:|---:|---:|
| Flores | 10 | 1 | 16 | 7 | −0.0952 |
| Pico | 24 | 5 | 27 | 19 | **−1.6105** |
| São Miguel | 12 | 1 | 47 | 3 | −0.3333 |
| Terceira | 12 | 1 | 23 | 9 | −1.0000 |

**Not four independent biological confirmations.** Three islands have only *one* detected affected taxon each, which does NOT pass the prospectively frozen taxon-weighted group comparison gate, and species may recur across islands. The focal plot fractions and introduced species richness are conditional on source sampling of relatively intact vegetation and differ in habitat/elevation coverage.

## Ecological synthesis

Together with the already verified v1.279–v1.280 equal-plot-effort bound, the findings support a specific spatial-habitat **association**:

> Azorean taxa with documented historical local losses elsewhere are concentrated in sampled Pico native vegetation even at equal plot count, and within Pico they occupy plots with fewer recorded introduced taxa than the wider native assemblage; a coarse two-level elevation adjustment does not remove the difference.

The data are consistent with a native-community refugial habitat *hypothesis*, but they do not establish that external plants caused the species losses or that Pico provides viable source populations to other islands. Historic source-pool occupancy breadth and taxon range, soil/climate, survey elevation and habitat quality, land-use history, incomplete sampling, invasion co-response and local plant competitive interactions can explain the pattern.

## Evidence and next focused falsification

- Frozen, committed **before this re-access** (but the underlying same 2013 data were already outcome-exposed in v1.278): development/azores_MOVECLIM_2013_introduced_pressure_protocol_v1_281.json.
- Deterministic script and four source-free tests: scripts/azores_MOVECLIM_introduced_pressure_v1_281.py ; tests/test_azores_MOVECLIM_introduced_pressure_v1_281.py.
- Source-locked published-original script workflow: .github/workflows/azores-MOVECLIM-introduced-pressure-v1_281.yml. The run validated original source SHA256 and 58/232/2539, 20/24 plus the old 5/1/1/1 focal island counts and 746 native plot×species incidences.
- Next falsification **without changing the v1.281 estimate**: does the sign survive a fixed *native-reference-richness + continuous elevation* correction at the original plot unit? This can be a retrospective stress test but cannot count as independent validation. The needed new 2013 raw-source use requires its own declared protocol; do not invent a population rescue endpoint.

Protected original global mammal labels/BioTIME/RLS/other Macaronesia S2/S3/S4 remain unopened. GEB manuscript HOLD, zero fresh confirmatory systems, eBird excluded.
