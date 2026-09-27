# Structural current status v0.51

## Fresh evidence

Fresh empirical denominator remains **zero**.

The pristine 5,592-island mammal system remains response-sealed on HOLD.  
The Indo-Pacific atoll plant system remains terminally closed.

## 318-island mammal stress test

The 318-island mammal lane is independent **stress-test evidence only**.

Completed before heldout response access:

- 65-island burned pilot qualified on all 65 islands;
- fixed 233-species universe;
- 244 heldout islands frozen;
- R3 and C fitted from pilot only;
- 56,852 heldout prediction rows frozen;
- prediction surface SHA-256:
  `a5fe8326172e39ca4cf1d3d7afe9b9bd679076ffc10ec08aaa7c2da2fddeaad9`.

Heldout occurrence values opened so far:

**0**

## Frozen heldout scorer

The scoring implementation is now frozen before outcome access.

It cannot fit or refit a model.

It may only:

1. verify the frozen prediction-surface SHA;
2. decode the fixed 233 species on the 244 heldout islands;
3. compute heldout R3 and C log loss;
4. compute the frozen primary:
   `mean(C−R3 | extreme q75) − mean(C−R3 | non-extreme)`;
5. run the predeclared 10,000-replicate archipelago-cluster bootstrap.

Bootstrap implementation is fixed to Python `random.Random` (MT19937), seed 20260927. Each replicate samples the eight archipelago labels eight times with replacement and includes all rows from each sampled cluster with multiplicity. Linear 2.5%/97.5% quantiles are used.

## Firewall

During heldout scoring:

- island ID column A may be opened for routing;
- only the 233 frozen species cells may be decoded on the 244 heldout islands;
- pilot-island occurrence cells remain sealed;
- out-of-scope-island occurrence cells remain sealed;
- the other 1,241 species columns remain sealed.

Any value outside the frozen binary domain 0/1 is terminal.

## Next event

After this scorer freeze is merged and CI-green, exactly one heldout stress-scoring run may open the 244 heldout islands.

Once that read begins, no rerun, refit, threshold change, source-operator change, or bootstrap change is allowed.

Whatever the result, it remains independent stress evidence rather than fresh confirmation.
