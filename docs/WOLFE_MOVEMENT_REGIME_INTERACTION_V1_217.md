# Wolfe v1.217 — movement-regime dependence is not monotone (posthoc)

**Evidence class:** retrospective/post-outcome, prompted by the already observed four-versus-six patch-size-heterogeneity reversal in v1.212. Neither the focal regime comparison nor its direction was preregistered. Wolfe et al. (2022, Oecologia, DOI 10.1007/s00442-022-05178-9) previously investigated experimental movement effects; do not advertise this as a first demonstration of corridor costs.

Using exactly the author source Git blob (SHA-1 `e78003d425b646b390ae02e36c007892c1c70926`), apply the existing v1.212 exclusion of ambiguous `6HoLM1` **before reading its response**, preserve day-21 within-metacommunity joint guild positivity and 4 intended replicates per arm, and compute heterogeneous minus homogeneous separately within each of 9 movement regimes and 4/6-patch treatment. Matrix categories are **none / low-mortality / high-mortality transfer**; corridor categories are **none / low-frequency / high-frequency local dispersal**. Never interpret matrix “low” as low transport. Average equal-weight across the three matrix regimes for each corridor frequency. Bound each missing binary outcome adversarially and report no sampling CI or p-value.

Six-patch results, percentage-point heterogeneity contrast:

| Local corridor frequency | Observed-only | All-missing lower | All-missing upper |
| --- | ---: | ---: | ---: |
| None | +33.33 | +16.67 | +33.33 |
| Low | +33.33 | +33.33 | +33.33 |
| High | 0.00 | −8.33 | +8.33 |

Exploratory posthoc difference in heterogeneity contrasts between **low and high local corridor frequency** at six patches: **+33.33 pp observed**, finite missingness sensitivity **[+25.00,+41.67] pp**. This difference is between two independently allocated groups of microcosms; the difference bounds are sharp for their unknown binary outcomes but **do not quantify sampling/randomization uncertainty**. The higher local-frequency experiment did not exhibit the observed positive joint-guild heterogeneity contrast. This neither establishes a causal damaging effect of corridors nor demonstrates homogenization. Authors already noted that predation/transfers can offset rescue.

Especially important falsifier: in the **6-patch, matrix-none, corridor-none** cell, joint-guild positive microcosms were **1/4 heterogeneous vs 0/4 homogeneous**. Hence a positive observed heterogeneity contrast is *possible even without experimental inter-patch dispersal*. The presence of a contrast alone cannot identify colonization/rescue as its mechanism. This single cell is tiny; the difference is not a reliable ecological effect estimate.

The old v1.212 equal-weight 9-regime bounds must be reproduced exactly by the Python workflow, else STOP. The patch-count manipulation is not orthogonal to size distribution (4He=16/16/8/8 versus 4Ho=12 each; 6He=12/12/12/4/4/4 versus 6Ho=8 each). No within-patch organism trajectories, propagule flux, immigration or mortality can be identified from the terminal CSV. A future experiment must independently cross heterogeneity *dose* with patch count and local transfer, track within-patch extinction/colonization, and verify assigned experimental randomization and replication. This is a **mechanism-discrimination hypothesis**, not evidence sufficient to change the original GEB scientific HOLD.
