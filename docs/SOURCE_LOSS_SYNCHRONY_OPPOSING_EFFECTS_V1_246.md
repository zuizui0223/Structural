# Structural v1.246 — Opposite effects of source loss on synchrony; quantitative identifiability gate

## What prior ecology actually found

**Fox, Vasseur, Cotroneo, Guan & Simon (2017)**, *Nature Ecology & Evolution*, DOI [10.1038/s41559-017-0271-y](https://doi.org/10.1038/s41559-017-0271-y), experimentally manipulated catastrophic protist local population extinctions while leaving the culture patch available, in strongly dispersed cyclic predator–prey metapopulations. Extinctions reduced phase synchrony and could *increase* overall metapopulation persistence at high dispersal. This is the already-published spatial hydra effect. Author original Dryad DOI [10.5061/dryad.2rs23](https://doi.org/10.5061/dryad.2rs23), **dataset id 5685, published version id 5720**, contains \`data_for_Fox_et_el_2017_nature_ee.csv\` (323,814 bytes, MD5 \`a39aec4a41c5fcb301203ee56f922b89\`) and original README (1,440 bytes, MD5 \`b25b2ddd88e046ac58849a20a549e9e7\`). This metadata is source-verified; **no raw Fox outcome row was opened**. The public file-stream endpoint presents a bot-verification interstitial; it must not be passed off as accessible biological data.

**Matter & Roland (2009 online / 2010 issue)**, *Proceedings of the Royal Society B*, DOI [10.1098/rspb.2009.1520](https://doi.org/10.1098/rspb.2009.1520), experimentally removed **two adjacent Rocky Mountain Apollo butterfly subpopulations** from a network of 17. Immigration into nearby butterfly populations decreased, and the remaining network became *more* synchronized. The authors' simulations identify uneven patch carrying capacities and indirect redistribution of immigrants as possible explanations. This is also an already-published ecological effect, not Structural original evidence.

These are **distinct interventions**. The Fox experiment killed a population without destroying its patch; permanent disappearance of an occupied island's habitat and prolonged removal of a highly connected butterfly population are not the same manipulation. Protist phase resetting does not automatically transfer to long-lived island mammals, trees or the house sparrows of earlier Structural v1.230–v1.245.

## The exact *synthetic* condition under which fewer sources can help or hurt

Construct an intentionally minimal target receiving propagules from **three pre-loss sources**, each independently viable with probability 1/2 on any occasion. If a source is alive it independently establishes at the target with probability q (identical q for all donors). There is no replacement, no density dependence, no feedback, and no actual population persistence duration. Pre-loss source support:
\[
R_3(q)=1-(1-q/2)^3.
\]

Remove exactly **one** source. Surviving two sources retain the *same marginal viability probabilities* 1/2 in every case:

- Independent survivors: \`R_2,ind(q)=1-(1-q/2)^2\`, always lower than R3 because one donor opportunity was lost.
- Perfectly anti-correlated survivors: exactly one is alive at each occasion, \`R_2,anti(q)=q\`. The synchrony benefit *may* exceed the donor depletion penalty.
- Perfectly synchronized survivors: both are alive together with probability 1/2, otherwise both absent, \`R_2,sync(q)=q-q²/2\`. The same nominal source loss now strongly reduces potential recipient colonization.

The path-specific algebraic split (NOT estimated causal mediation):

\[
\underbrace{R_{2,ind}-R_3}_{-\frac18q(2-q)^2<0}
+\underbrace{R_{2,anti}-R_{2,ind}}_{+\frac14q^2}
=R_{2,anti}-R_3.
\]

The net sign switches at **\`q*=3-sqrt(5)≈0.763932\`**. At q=0.5, the loss remains detrimental even though surviving donors become asynchronous; at q=0.9, the same donor loss produces an improvement under the asynchronizing *hypothetical* change. The synchronized survivor regime is detrimental throughout q in (0,1]. This threshold is a **model-specific known-truth counterexample**, not an empirical estimate for Fox's protists, Matter & Roland's butterflies, or any island population. It establishes why **source count, average connectivity, and marginal source reliability cannot by themselves determine the sign** of colonization support following loss.

## Real ecological mechanism and the explicit distinction from Structural prior tests

Prior Structural [source-loss leverage protocol v1.123](../development/prospective_source_loss_leverage_transition_hypothesis_v1_123.json) already freezes t0→t1 source loss and *separate* t1→t2 contraction and the three-wave outcome/strong-reference conditions. It cannot retroactively use these published Fox/Matter outcomes as confirmation. Independent BALA v1.144 earlier tested structural high-leverage source-loss and got primary C−R2≈**+0.000674**, a **non-support**. We must not bury that null result or claim a new kind of hydra source term rescues it.

For any genuinely independent future system, the following must be *measured and separate*:

- Exposure **type and duration**: one-off removal of a local population while habitat remains available, versus prolonged population loss, versus irreversible habitat/island destruction.
- **Direct immigrant supply** into each existing recipient, including source and target identity and detection effort.
- **Donor co-failure / spatial synchrony** among actual viable source populations in time, using pre- and post-intervention time series, not just static island geometry.
- **Dispersal success** per live source, not inferred from a synthetic q threshold or a geospatial graph edge.
- Future **recipient colonization or persistence** with at least three censuses, independently defined observation/detection process, and time-order preserving mediation.

Strong baseline must include source count, lost-access leverage, habitat, island isolation, landscape connectivity, local demography, source abundance, temporal environmental covariance and ordinary distance. New synchronization features enter only beyond these. If one independent system does not have adequate observations, STOP and leave GEB HOLD. Source cofailure and persistence benefits are NOT directly demonstrated by the known-truth exercise.

## Result class

\`scripts/source_loss_synchrony_gate_v1_246.py\` enumerates every joint source-state and uses exact rational arithmetic. \`tests/test_source_loss_synchrony_gate_v1_246.py\` verifies donor count, unchanged marginal donor viability, joint co-failure, analytical sign thresholds, and explicit nonconfirmation. The Action writes a machine-readable artefact. **No empirical response, manuscript prediction or original sealed mammal heldout is opened.** No eBird.
