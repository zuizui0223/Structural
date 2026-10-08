# Wolfe weekday-blocked null interpretation v1.215

Wolfe et al. 2022 state that four experimental replicates were blocked by sampling day (Monday to Thursday). A hypothetical comparison that swaps heterogeneous/homogeneous outcomes only within the same patch count, matrix/corridor treatment and weekday is more conservative about day effects than completely exchangeable assignments across eight experimental units. The source documentation does NOT prove that the physical assignment of treatments was randomized within pairs.

For the original 176-row CSV, the source-ambiguous 6HoLM1 row is dropped before response semantic access. Of 175 retained source rows, 139 are in the focal 4/6-patch comparisons, with 72 pairs and five unknown planned binary outcomes. The calculation exhausts 32 possible outcome imputations.

For D discordant completed pairs and integer signed sum T, the hypothetical two-sided label-exchangeability tail is the probability that abs(2*Binomial(D,0.5)-D) is at least abs(T). It is exactly enumerable; it is NOT a verified randomization test, preregistered p-value, or adjusted for the posthoc patch-count interaction.

Independent calculations give p ranges of 0.03857–0.60724 for the overall joint-predator contrast and 0.00342–0.17957 for the six-minus-four contrast. These ranges cross 0.05. Both the finite-sample effect bounds and unadjusted p bounds are retained without postoutcome metric tuning.

The original experimental paper's heterogeneous patch-size dose differs by patch count: 2:1 at four patches and 3:1 at six. Thus the difference is not a pure patch-count effect. No biological source rescue or original mammal island-network validation has been demonstrated. GEB remains scientifically on HOLD.