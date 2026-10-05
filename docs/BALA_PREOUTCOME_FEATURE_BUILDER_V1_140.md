# BALA pre-outcome feature builder v1.140

This stage is deliberately prepared before the v1.138 temporal-split artifact is available.

It has **no execution authorization**.

After a successful temporal firewall, it will be bound to the exact BALA1/BALA2 byte surface and may decode only that pre-outcome surface. BALA3 remains sealed.

The builder will:

1. apply the unchanged pilot taxonomic rule;
2. reconstruct BALA1 and BALA2 island occupancy;
3. retain only taxa with at least two BALA1 sources, exactly one BALA1→BALA2 source loss, and at least one BALA2 survivor;
4. apply self-anchor exclusion for every target island;
5. compute target-specific lost-access fraction E_i;
6. compute only response-independent/lagged R2 covariates;
7. freeze all leave-one-taxon-out feature standardization and fold identities;
8. run the pre-t2 estimability gate.

No BALA3 row, taxon identity, quantity or outcome is opened here.
