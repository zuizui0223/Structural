# Wolfe v1.216: does heterogeneous habitat change both guild marginals, or excess co-presence?

**This is explicitly posthoc**: the exploratory decomposition question arose *after inspecting v1.212 and v1.215 numerical outcomes*. It is not a response-blind preregistration. No new independent ecological evidence is implied.

For each 4-/6-patch × matrix × corridor treatment arm define G = generalist Stentor present, S = any specialist Didinium/Dileptus present and J = G AND S present in the same experimental metacommunity at day 21. Then the exact algebraic identity within a cell is `P(J)=P(G)P(S)+Cov(G,S)`. The second term is a **descriptive cross-microcosm binary covariance**, NOT evidence that predator guilds directly facilitate or inhibit each other.

Exclude `6HoLM1` from all outcome values before analysis, as in v1.212. The immutable source contains 176 rows; 175 retained source rows, of which 139 are focal 4/6 patch microcosms. With four planned independent replicates per treatment cell, five missing/ambiguous units remain. Enumerate **4^5 = 1,024** joint (G,S) combinations, not only 2^5 joint-J choices, to constrain covariance correctly. Compute equal-weight contrasts across 18 strata and separately by four and six patches, then their difference. There are no p-values and no sampling confidence intervals in this exploratory decomposition.

The prior independent in-chat computation found overall hetero-homo contrasts (worst-to-best five-unit completion):
- Joint guild retention **+0.04167 to +0.11111**.
- Product of guild marginals **+0.02083 to +0.06944**.
- Within-arm covariance component **+0.01736 to +0.06250**.
- Six-minus-four *marginal-product* contribution **+0.17361 to +0.27083**, but covariance-contribution difference **−0.02778 to +0.06250**.

These component ranges must NOT be added independently: their extremes need not arise under the same assignment. Although both components contribute positively to the *overall* joint retention pattern under all missing guild states, stronger within-treatment guild association in six versus four patches is **not** supported robustly. The cross-patch-count contrast is principally compatible with changing individual guild retention, not a uniquely demonstrated cross-guild facilitation mechanism.

The treatments also differ in heterogeneity dose (4He patch-size ratio 2:1 vs 6He 3:1); even these endpoint decompositions cannot estimate a pure patch-number mechanism, propagule production, local recolonization, rescue or causal predator interactions. The original Structural mammal ecology and GEB submission status remain HOLD.