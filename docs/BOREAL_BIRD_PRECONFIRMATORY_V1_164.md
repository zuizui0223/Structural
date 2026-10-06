# Boreal bird preconfirmatory model freeze v1.164

v1.164 is frozen before the v1.163 bird pilot is executed.

If the pilot gate passes, the exact pilot snapshot is used to fit one common R3
model, one actual-topology C model and 20 null-topology C models. No confirmatory
bird value is used in fitting, standardization or prediction.

The key comparison is deliberately narrow: R0 through R3 remain identical for
the actual and rewired candidates. Only the two graph-path occupied-source
features in C change with topology.

For every confirmatory island x fixed bird species cell, the complete prediction
row is frozen before confirmatory access: pilot occupancy count n, S_i(n), zS,
R3 probability, actual-C probability and all 20 null-C probabilities.

The primary is not an average connectivity gain. After the one permitted
confirmatory read, it uses realized presences only and asks whether the observed
topology's loss advantage over the null ensemble becomes stronger as the
pre-frozen configuration-sensitivity moderator increases.

Within each presence-bearing spatial block, cell weights sum to one. The primary
coefficient is the weighted slope beta_S from D = alpha + beta_S*zS, where
D = logloss(actual C) - mean null-C logloss. Negative beta_S is predicted.

Support requires beta_S < 0 and a 10,000-replicate spatial-block bootstrap 95%
upper bound below zero. Fewer than four presence-bearing blocks, or zero weighted
zS variance, is terminal non-estimable.

No bird result can rescue or reverse the completed beetle primary. eBird remains
disabled.
