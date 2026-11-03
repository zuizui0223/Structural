# BALA JBI v1.348 — Word submission packaging and final editorial gates

**Status: anonymous Word material assembled locally, visually verified; GitHub source-free reproducibility build SUCCESS. Manuscript has NOT been submitted.** This note does not permit reopening the original BALA Event/Occurrence source. The science status remains v1.347 with the v1.346 geographic-uncertainty correction.

## What is now materially ready

- **Anonymous editable main text in DOCX**, 13 A4 pages at current typesetting, with 278-word six-heading structured abstract, Introduction/Materials and Methods/Results/Discussion, References, Data accessibility statement, all three figure legends and **three embedded original-source-free figures**. Header contains only nonidentifying short title. No internal developer notes, names, source GitHub owner/PR links or unpublished author declarations appear in reviewer manuscript text.
- **Separate editable Supplemental Table S1 DOCX**, one landscape A4 page, 5-row uncertainty table with all seven-island t intervals and 128 sign-flip p-values. Formula renders as Word equation, not escaped Markdown. The non-significant observed Beetle mean (Δ spatial Simpson −0.1753, interval [−0.4399,+0.0893], p=0.1875) is fully retained. The paired Beetle-minus-Spider interval crosses zero. S1 should NOT be mistaken for confirmatory island independence.
- **Original v1.347 source-free 14-row island×guild CSV and 3 figures (PNG and SVG)** retained. A blinded standalone script rederives three descriptive figures and exact 128 island-effect sign flips solely from 14 island-guild numbers, without original taxonomic Event/Occurrence data.
- **Strict document QA:** all 13+1 pages rendered and visually inspected; one orphan legend page was repaired by putting all Figure legends on a separate page; Word metadata and custom properties removed. Both documents passed the DOCX accessibility audit with no high/medium/low issues. The new source-free archive includes SHA256 checksum manifest and documents' exact verification.
- **Review packaging provenance:** source GitHub Actions #41564544223 artifact #13197924191, ZIP SHA256 `b1a491af11f884d9215d070f6baf30115a123c7dfbf53b7b354763b590662224`; original source field ZIP SHA256 `4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2`. The new text-based [reproducible Word builder](../scripts/bala_jbi_blinded_word_sourcefree_v1_348.py) and [workflow](../.github/workflows/bala-jbi-blinded-word-sourcefree-v1_348.yml) read **only the existing v1.347 source-free artifact**, not the original field source.

## Current Journal of Biogeography (JBI) requirements checked

Current [Wiley JBI author instructions](https://onlinelibrary.wiley.com/page/journal/13652699/homepage/forauthors.html) are decisive over earlier old ScholarOne instructions: Free Format is accepted; Research Article structured abstract must be ≤300 words; main text should be ≤6,000 words; paper title ≤115 characters and short running title <40; **double-anonymous main Word file with embedded figures plus separate supporting information**, while a **separate author title page** is required. Cover letter is optional according to current guidance. Reference formatting is free at initial submission but source bibliographic accuracy remains mandatory. Do not infer publication from uploaded files. Submission portal is https://authors.wiley.com/journal/jbi.

The current anonymous abstract is 278 words, title shorter than 115 characters, manuscript main text within 6,000-word target, 3 figures and 9 semicolon-separated keywords. The editorial work-up does **not** resolve provenance ethics or whether the novelty of this reanalysis is sufficiently broad for JBI.

## Outstanding blockers (cannot be invented by AI)

1. **Authorship and primary-data custodians:** Verify the contributor list and discuss reanalysis novelty/overlap with published 2024 BALA data descriptor and 2026 BALA original analysis. Confirm written or documented author agreements per journal ethics.
2. **Separate actual title page:** Correct author names, affiliations, corresponding author ORCID, approved biosketch and contributing roles, plus funding and acknowledgement text.
3. **Research ethics and declarations:** Confirm archival fieldwork permit provenance, conflicts, funding. Do not state field permits or author approvals without the custodian.
4. **Reviewer-accessible reproducibility:** A blinded source-free summary-level script is now packaged. Full original source processing pipelines already exist in the BALA PR but need an anonymized review-access repository/archive; no DOI or reviewer link is fabricated.
5. **Scientific editorial ceiling:** Positive, replicated source-observed temporal turnover excess in 7/7 island means, but only 4/7 original beetle island spatial signs are negative. Seven-island conditional t95 confidence interval and the post hoc sign flip include zero for the Beetle spatial mean; significant cross-taxonomic/causal homogenization cannot be claimed. Island diversity is within one archipelago, not seven independent archipelago experiments.

## Exact current progress

- Source-free Figure/Markdown package (v1.347): CI #41564544223 **SUCCESS**, 9 tests.
- Seven-island source-free uncertainty (v1.346): CI #41563482126 **SUCCESS**, 5 tests.
- New v1.348 Word conversion: local DOCX render/visual QA **PASS**, separate GitHub workflow `bala-jbi-blinded-word-sourcefree-v1_348.yml` created. Check the latest CI result before describing it as successful.
- Original biological source scorers v1.314 / v1.316 / v1.318 **SEALED**, original source values reopened **0**. GEB mammal manuscript remains SCIENTIFIC HOLD, 0 new pristine confirmatory systems, eBird not used.

**Decision:** Move forward with real author contributions and blinded full-code access. Do NOT reopen original BALA source or claim that the manuscript was submitted.