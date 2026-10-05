# BALA t2 scoring implementation v1.141

This file freezes the final scorer before any BALA1/BALA2 confirmatory features are known and before any BALA3 taxon or quantity is opened.

It does **not** authorize BALA3 access.

At the eventual one-shot execution:

- only MF tokens needed to identify frozen eligible taxa are inspected first;
- organismQuantity is decoded only for rows belonging to those frozen taxa;
- BALA3 island occupancy is reconstructed under the already-frozen pitfall surveyed-zero rule;
- leave-one-taxon-out R2 and C models are fitted under the v1.139 design;
- the primary is equal-weight taxon-macro C−R2 log loss;
- secondary leverage-direction summaries cannot rescue a failed primary.

The scorer therefore cannot be changed after BALA1/BALA2 feature counts or leverage values are observed.
