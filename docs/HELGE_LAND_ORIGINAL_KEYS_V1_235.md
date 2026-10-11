# v1.235 — Existing author ID, Year_ID and Year_ID_Location as alternative crosswalks

v1.233 found 0 exact natal known ID+year+island breeder records among 172 observed migrant recruits. v1.234 found 753 inconsistent hatch years out of 771 superficially overlapping producer-ID rows. This might reflect the producer table's ID namespace, which also contains Year_ID and Year_ID_Location; it does **not** license retrospectively fabricating a name conversion.

Before reading any offspring production fields, evaluate exactly the three **source-defined** candidate strings (ID, Year_ID, Year_ID_Location), preserving published verbatim labels. For every row, demand uniqueness of recorded nest-year/island in the original mark-resight file, agreement between original nest year and producer Least_hatchyear, and consistency of producer-year and adult observed destination island. Report all candidates, including negatives, never select an output-advantageous join. Row index from the R export is excluded to avoid off-by-one ID corruption.

A row-level match is merely a possible **identity link**, not an already observed immigrant's reproductive success. Producer and presence outcomes are previously published, the same Helgeland archipelago is not two independent replicates, and Structural's confirmatory estimability rules remain unchanged.
