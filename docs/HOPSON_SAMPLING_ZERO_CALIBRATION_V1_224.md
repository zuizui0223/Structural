# v1.224 — Could tiny volume samples alone create the observed intermittent zero counts?

This is a **retrospective observation-model sensitivity check**, motivated after all original Hopson source outcomes were already exposed in v1.222/v1.223. It **cannot be called preregistered, independent confirmation, or a colonization estimate**.

In the published experiment Euplotes was counted from stirred undiluted sample volumes of approximately 0.3 mL at visits spaced 3–4 days, and the investigators carried out source-to-target movement after sampling on treatment days (Hopson & Fox 2019; https://doi.org/10.1111/1365-2656.12905). Earlier v1.222 identified 554 zero→positive sample transitions; v1.223 found 209 one-zero spells flanked by positives. Isolated sample zeros **might** be random Poisson draws from a continuous positive abundance, or sharp biological changes, or heterogeneous mixing/detection; only a model comparison can say how plausible the *simple sampling-only explanation* is under explicitly fixed conditions.

## Full-outcome diagnostic, not event cherry-picking

Consider **every** interior sample with *both* immediately adjacent Euplotes counts positive. We include the central count whether zero or positive, so counts of central zeros can be compared with a conditional predictive benchmark. Use actual sample volumes V and neighboring counts y. Assume constant concentration across the three dates with conditional Poisson counts and a Jeffreys Gamma(1/2,0) density prior. Then

`P(Y_mid=0 | y_left, y_right) = ((V_left+V_right)/(V_left+V_right + rho*V_mid))^(y_left+y_right+0.5)`.

This is a *toy observation model* with density-scale sensitivity `rho ∈ {1.0,0.25,0.10}` at the center visit. Values 0.25 and 0.10 represent real underlying concentration dips of 75% or 90% **without requiring extinction**. We do **not** fit rho from the same zeros or assert any of these concentrations existed. The middle count does not enter its own predicted probability.

Output includes all original time blocks, treatments and 14 metapopulations; expected central zeros summed from individual conditional probabilities and fixed probability bins, and central zeros with improbably low model-predicted Pzero. Triplets overlap within jar and are **not independent**; no unadjusted binomial p-value, confidence interval, causal factor or false-negative classification is warranted. Flanking positive counts themselves are noisy indicators of latent concentration and the Poisson mixing/temporal-constancy assumptions are strong.

**Scientific inference boundary:** if observed isolated zeros greatly exceed the stationary Poisson prediction, the fixed-density sampling-only model does not adequately reproduce these sample trajectories. That would *not prove biological local extinction*: low transient abundance, prey cycles, overdispersed sampling, seasonal or synchronized environmental shocks, or immigration may all break constant-concentration assumptions. Do not call an outcome from this diagnostic rescue, realized directionality, or new independent evidence. Structural GEB remains on scientific HOLD and the sample-zero limitation must be respected in any future source-network work.
