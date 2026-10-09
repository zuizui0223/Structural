# v1.232 pre-scoring site identifier column in Zhan 2024 supplement

The verified official Zhoushan supplemental DOCX (inner source SHA256 ec1d1d0a...) contains nine WordprocessingML tables. The first two tables have 40 rows; first table has 12 columns. Zhan et al. report Supplementary Table S1 as island characteristics for 39 marine-island survey sites.

Only table index 0 is eligible. First read all twelve field names from its HEADER row, then only the FIRST cell of each of 39 source site rows. Explicitly forbid any of the other 11 data cells per row, any of the other eight tables, all species-by-island 0/1 and richness/trait values, Word prose or illustrations. Source identity is checked by stable inner DOCX SHA256 before opening any text.

The purpose is geographic **site identity**, not looking for an interesting result. Even a complete 39-name list does not establish the one-to-one island crosswalk to the original 4,126 heldout nodes, independent native mammal occurrence estimates or completed detection probabilities. The five previously confirmed overlapping taxa remain name-level only; no scoring allowed. Zero overlap would have stopped direct validation, but v1.231 corrected an R period-separator error and found five.

No original mammal heldout data, ALA/Hébert replay, eBird, or GEB submission approval.