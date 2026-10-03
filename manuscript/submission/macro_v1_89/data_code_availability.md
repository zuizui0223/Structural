# Data and Code Availability — journal-neutral draft v1.89

## Data availability

The global island mammal occurrence data used for the empirical core are publicly available from Dryad, dataset DOI **10.5061/dryad.hmgqnk9j2**, version 6 (selected dataset version dated 17 June 2024). The response file is `Appendix_1_presence_absence.csv`; the associated island metadata workbook is `Appendix_2-dryad.xlsx`. Exact file identities and SHA-256 fingerprints are recorded in the Structural repository.

Response-independent global island geography derives from the Weigelt island reference data distributed in the public Figshare/UvA dataset **“Island, archipelago, plate, mountain and point labeling dataset”**, DOI **10.21942/uva.22788464.v5**, version 5, licensed CC BY 4.0. Structural uses an audited safe projection of the `islanddata` reference table containing island identity, area, external-isolation, historical-connectivity, climate and related response-independent fields.

The secondary plant analysis uses the **Global Inventory of Floras and Traits (GIFT)** database version 3.2 through GIFT R package version 1.3.4 and the public GIFT API. The fresh plant confirmatory attempt terminated without an ecological score; the later endpoint-available plant analysis is explicitly nonconfirmatory and is not part of the primary mammal evidence.

The earlier 318-island mammal stress system and the local boreal beetle system are retained only under their frozen evidence classes described in the manuscript and repository provenance files.

## Code availability

All analysis contracts, response firewalls, source-feature definitions, model code, frozen-output diagnostics, figure-generation scripts and evidence-status tests are maintained in the GitHub repository **zuizui0223/Structural**.

The manuscript is tied to the frozen scientific state beginning with Structural v1.88. Before journal submission, the authors should create a permanent archival release of the exact submission commit (for example through Zenodo or an institutional repository) and replace the line below with the final permanent identifier:

> **Permanent code archive DOI: [TO BE MINTED BEFORE SUBMISSION]**

The public repository history should remain available alongside the permanent archive because the chronology of prospective contracts, terminal failures, nonconfirmatory continuations and frozen outputs is part of the reproducibility record.

## Reproducibility boundary

No new biological response is required to regenerate the submission-facing figures and reviewer-defense summaries. Figures 1–3 and Supplementary Figures S1–S2 are generated from already frozen output artifacts or committed frozen summaries. The primary response-access workflows are single-use and should not be rerun for manuscript formatting.
