# Structural — When higher-order donor failure reaches a recipient
Date: 2026-10-19

## Status and source
**Exact mathematical extension; no new empirical validation.**
This note extends the four-donor construction in PR #454 at commit
`4651e279e63855cae5359e0c2fef540b57546950`, specifically
`scripts/higher_order_donor_cutset_known_truth_v1_246.py`
(Git blob `707ea8372fc16e4e3957009022628f54dc08639f`).
The original distribution, eligibility graph, all source moments and historical results are unchanged.

The relevant recent work is not all on main: PR #450 contains the Hopson re-detection/prey analysis; #451 contains the Helgeland observed-movement analysis and its negative year-alignment diagnostic; #454 contains the higher-order donor counterexample; #457 contains Gawecka first-sampled-positive ordering. These are different evidence classes, not independent confirmations of one ecological mechanism. Reading main alone misses them.

## Revised biological question
When does the joint availability of donor populations change a receiving island's chance of establishment beyond donor number, pairwise synchrony and geography, **after accounting for whether available donors can actually send successful colonists**?

Neither few occupied pilot islands nor geographical graph reachability directly measures remaining global populations, movement, establishment or demographic rescue. The earlier mammal occupancy strata compare different species; they do not follow the same species through range contraction.

## 1. Keep the original nontrivial contrast
There are four binary potentially available donors X1,...,X4.
Recipient A is accessible from donors {1,2,3}; B from {1,2,4}.

For s in {-1,+1}, the original joint laws are
p_s(x) = 1/16 + s/32 [(-1)^(x1+x2+x3) - (-1)^(x1+x2+x4)].

Both worlds have:
- every marginal availability = 1/2;
- all six pairwise joint availabilities = 1/4;
- the same complete global donor-count distribution (1,4,6,4,1)/16;
- the same accessible-source sets.

With certain effective delivery from an available donor, local complete-source-failure risks are:
s=-1: A=1/16, B=3/16; s=+1: A=3/16, B=1/16.
These are model probabilities, not measured island extinction risks.

## 2. Add movement and establishment, rather than assuming them
Fix a time window and an initially unoccupied, habitable receiving patch.
Let q_j be the probability that available donor j supplies at least one successfully establishing colonist within that window.

Conditional on the donor-state vector and fixed q_j, donor-specific success events are assumed independent. One successful donor suffices. Dormant residents, seedbanks, state-dependent q, correlated transport shocks and subsequent demographic persistence are outside this calculation.

The probability of no successful establishment is exactly:
Q_i = E[ product over j in S_i of (1-q_j X_j) ].

This is a standard product expansion applied to the existing construction, not a claim to have invented a probability identity.

For three eligible donors:
Q = 1 - sum_j q_j E[X_j]
      + sum_{j<k} q_j q_k E[X_j X_k]
      - q_1 q_2 q_3 E[X_1 X_2 X_3].

If first- and second-order moments match between worlds, only the last term can distinguish them. Its magnitude is multiplied by the product of the three donor-to-recipient success probabilities.

## 3. Equal success probabilities: an exact cubic attenuation
For all q_j=q:
Q_A(s,q) = (1-q/2)^3 + s q^3/16;
Q_B(s,q) = (1-q/2)^3 - s q^3/16.

Therefore the absolute receiver-risk gap is q^3/8.
The ordering reverses between worlds for every q>0, but its magnitude need not be ecologically large. At q=0 both risks equal 1 and there is no ranking.

| Assumed q | Lower no-establishment risk | Higher no-establishment risk | Gap, percentage points |
|---|---:|---:|---:|
| 0.10 | 0.8573125 | 0.8574375 | 0.0125 |
| 0.25 | 0.6689453125 | 0.6708984375 | 0.1953125 |
| 0.50 | 0.4140625 | 0.4296875 | 1.5625 |
| 0.75 | 0.2177734375 | 0.2705078125 | 5.2734375 |
| 0.90 | 0.1208125 | 0.2119375 | 9.1125 |
| 1.00 | 0.0625 | 0.1875 | 12.5 |

The earlier threefold contrast is the q=1 endpoint. At q=0.5, the risk ratio is 55/53, about 1.0377, not threefold.

**Prediction for testing, not a field finding:** under these assumptions, very weak effective dispersal/establishment suppresses a third-order source-dependence effect even when the potential-donor contrast is large. The largest observable higher-order signal need not occur at the most externally isolated islands. No mapping from distance to q has been estimated.

This is not a general claim that all connectivity effects scale as q^3. First-order donor supply enters at order q and pairwise dependence at order q^2; the cubic claim concerns the residual contrast after those moments have been matched.

## 4. Unequal success probabilities can remove the ranking reversal
Allow q1,q2,q3,q4 to differ, keeping each fixed between the two worlds:
Q_A = (1-q1/2)(1-q2/2)(1-q3/2) + s q1 q2 q3/16;
Q_B = (1-q1/2)(1-q2/2)(1-q4/2) - s q1 q2 q4/16.

Write their difference as D_s = delta + s T, where
delta = (1-q1/2)(1-q2/2)(q4-q3)/2,
T = q1 q2 (q3+q4)/16.

Strict ranking reversal occurs if and only if |delta| < T.
Equality gives a tie in one world, not strict reversal.

For (q1,q2,q3,q4)=(0.5,0.5,0.5,0.6):
- s=-1: A=0.4140625, B=0.403125;
- s=+1: A=0.4296875, B=0.384375.

A has the higher risk in BOTH worlds. Unequal effective establishment can overwhelm the higher-order reversal. Thus the original idealized priority reversal cannot be transported to field management without measuring the donor-to-recipient success process.

## 5. Next empirical design: requirements that follow from this result
The independent unit is a species-by-network time series or separately replicated landscape, not each donor triple or each island-by-species cell treated as independent.

Before recipient outcomes:
1. Fix recipient habitat availability, time window, accessible donor identities and spatial/temporal holdouts independently of future arrivals.
2. Obtain repeated donor-state observations with effort/detection information. Record directional transfers and establishment separately where possible; do not substitute kNN edges, range polygons or first detections for q.
3. Estimate the reference source-state law and success probabilities on training windows only. The reference must account for individual and pairwise donor behavior, global donor-count distribution, habitat, distance, local resources and shared environmental effects.
4. Test the remaining local higher-order dependence against an independent future establishment endpoint. Estimate q and its uncertainty, rather than choosing a favorable q or a pilot-occupancy threshold after results.
5. Evaluate practical effect size and predictive calibration, with whole-network/whole-time-block replication and the existing v0.31/v0.42 admission chain.

The two-year goby release cannot estimate a within-system temporal third-order source-failure distribution from one transition alone. Rail repeated surveys document detection and temporal occupancy but published aggregate isolation summaries do not, by themselves, supply the complete source-specific directional establishment process. Neither is admitted here.

This does not reopen Hopson, Helgeland, BALA, SW Finland, the mammal holdout, eBird or the failed Fox file routes. None of the published experiments establishes this exact higher-order residual contrast.

## 6. Verification completed in this session
- Both exact 16-state source laws: normalization, nonnegativity, all four marginals, all six pairs and the complete count distribution checked.
- Four symbolic equal-q identities independently simplified to zero residual.
- 1,024 exact comparisons: two worlds x two recipients x all 4^4 q vectors with entries in {0,0.1,0.5,1}; direct product expectations agree with separate enumeration of all 2^3 delivery outcomes for each donor state.
- Three unequal-q examples checked against the strict reversal criterion.
- No new biological records opened; no empirical q or demographic effect estimated.
- This is local exact-arithmetic verification, NOT a new full-repository CI or field validation result.

Machine-readable full result SHA256:
`a4b6ba141f7745db24f1546691b33875aa88bc012c0f2e870e506e43888795d0`.

## Sources and prior-art boundary
- Existing exact source construction: PR #454, pinned commit above.
- Fox et al. (2017), https://doi.org/10.1038/s41559-017-0271-y, already demonstrated synchrony-mediated spatial hydra effects. That phenomenon is prior art, not a new result here.
- Gawecka et al. (2025), https://doi.org/10.1111/ele.70254, already investigated configuration and food-web effects on recovery. PR #457 is a separate retrospective observation-order analysis, not this hypothesis's confirmation.
- Tidewater goby metadata: https://doi.org/10.5061/dryad.vdncjsxs9.
- Rail repeat-survey metadata: https://doi.org/10.5061/dryad.8w9ghx3h8.

GEB scientific HOLD remains unchanged. New confirmatory systems admitted: zero.
