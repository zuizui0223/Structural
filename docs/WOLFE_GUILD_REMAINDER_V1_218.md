# Wolfe v1.218 — Did high corridor collapse both guilds, or prevent shared retention?

**Post-outcome / posthoc, not preregistered.** This deliberately follows v1.217, a narrower subgroup selected after the v1.212 full analysis. Wolfe et al. 2022 (*Oecologia*, DOI 10.1007/s00442-022-05178-9) already report predator feeding-specialism differences; do not claim new discovery of opposing predator responses.

## Fixed observed guild counts, 6-patch heterogeneous landscapes

Across all three matrix regimes, with each microcosm counted once:

| Corridor | observed n / intended 12 | Stentor G | Specialist-any S | Same-microcosm G and S |
|---|---:|---:|---:|---:|
| Low | 12 / 12 | 7 | 5 | 4 |
| High | 11 / 12 | 2 | 6 | 0 |

All four possible G,S states of the one high/heterogeneous missing microcosm give low-minus-high proportion differences **G [+33.33,+41.67] pp**, **S [-16.67,-8.33] pp**, **joint [+25.00,+33.33] pp**. Therefore the result is *not* general extinction of both guilds in high frequency; the generalist is the limiting marginal in this descriptive comparison. Do **not** interpret this as an identified causal corridor loss, dispersal-mediated competitive exclusion, or actual per-patch disappearance.

## Descriptive association decomposition

Within every 6-patch heterogeneity x corridor x matrix cell (4 intended independent microcosms) compute

`P(G AND S) = P(G) P(S) + [P(G AND S) - P(G) P(S)]`.

Average each component across 3 matrix treatments, then take 6-patch heterogeneous low-minus-high local corridor. Exhaustively enumerate **4^2 = 16** missing G,S assignments in two separate six-patch high-corridor arms (the second, high/homogeneous missing unit matters for the heterogeneity-interaction sensitivity only).

| Difference, low − high | Sharp missingness sensitivity (percentage points) |
|---|---:|
| Joint G and S | +25.00 to +33.33 |
| Product of guild marginal retention | +16.67 to +20.83 |
| Residual binary co-presence covariance | +8.33 to +14.58 |

**Important:** The component intervals are marginal bounds and cannot be added independently; the extrema may come from different missing-state completions. Positive covariance-component contrast means observed within-arm co-retention differed beyond the product of the observed guild marginals in these tiny cells. It does *not* establish a biologically interacting predator pair, facilitation, anti-association beyond sampling noise, or a causal corridor effect. Both components may vary randomly in only 3–4 experimental microcosms per stratum.

A different sensitivity asks how the **heterogeneity advantage** itself differs between low and high corridors; sharp missing-state J bound: **+25.00 to +41.67 pp** (v1.217). Mechanistic route discrimination would require repeated patch-specific G/S abundance, within-patch contacts, randomized corridor regimes verified by weekday, and factorial separation of patch count, small-patch absolute area and size CV. No such transition/flux data are present.

Original global mammal graph and heldout scores are unopened; eBird off; GEB scientific HOLD persists.
