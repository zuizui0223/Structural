> **Historical policy snapshot — superseded for current submission use.**
> Current policy record: manuscript/submission/live_policy_verification_2026-09-26.md.

# Live journal-policy verification — 2026-09-23

Target: **Ecological Informatics** (Elsevier / ScienceDirect)

This check updates the repository's submission-policy record without changing any scientific result, model, figure input, or empirical denominator.

## Verified from current official Elsevier sources

### Journal identity and scope

The current Elsevier journal page continues to describe *Ecological Informatics* as an international journal on computational ecology and ecological data science, including ecological-data modelling, uncertainty analysis, biogeography, species-distribution modelling, forecasting and quantitative environmental decision support.

Official journal page checked:

- https://shop.elsevier.com/journals/ecological-informatics/1574-9541

This remains consistent with the manuscript's current positioning as a computational-ecology / ecological-informatics paper about held-out validation, reference-conditioned structural information, uncertainty boundaries and reproducibility.

### Elsevier-wide author guidance that is currently machine-verifiable

The current Elsevier highlights guidance states:

- 3–5 highlight bullets;
- maximum 85 characters including spaces per bullet;
- Highlights are not required until the final-files stage;
- Highlights should be uploaded as a separate editable file.

Official source checked:

- https://www.elsevier.com/researcher/author/tools-and-resources/highlights

The current generic Elsevier "Your Paper Your Way" Guide for Authors also provides the following general guidance:

- Original Research Articles report complete studies and new results;
- a concise factual abstract is required;
- immediately after the abstract, provide a maximum of 6 keywords;
- graphical abstracts are optional under the generic Elsevier guidance;
- generic graphical-abstract guidance specifies a minimum image size of 531 × 1328 pixels (h × w), or proportionally larger, with preferred file types including TIFF, EPS, PDF or MS Office.

Official source checked:

- https://www.elsevier.com/subject/next/guide-for-authors

These are **Elsevier-wide/generic** requirements and do not override a journal-specific instruction if the live *Ecological Informatics* Guide for Authors differs.

## Current Elsevier generative-AI policy — reverified 2026-09-23

Elsevier's current journal policy page states that authors who use generative AI or AI-assisted tools for manuscript preparation should include a separate declaration immediately before the references, naming the tool/service, explaining the purpose, and stating that the authors reviewed/edited the output and take responsibility for the publication.

The current policy is more differentiated than the repository's older 2026-08-12 summary.

### Text/manuscript preparation

The policy permits responsible AI assistance for activities such as literature synthesis, identifying gaps, content organization, language/readability support and related manuscript-preparation tasks, subject to author oversight, disclosure where required and full human responsibility.

AI tools cannot be authors.

### Figures, images and artwork

The current policy distinguishes several categories:

- **explanatory images** (for example flow charts, decision trees, timelines and schematic conceptual illustrations): AI assistance may be permitted, with responsible-use requirements and disclosure in the figure caption and general AI declaration;
- **data visualizations** (plots, charts, graphs, heatmaps): AI assistance may be permitted only when the visual output is directly derived from the underlying data by reproducible analytical/computational/statistical methods; relevant AI use must be disclosed in Methods;
- **primary research images** (for example microscopy, histology, western blots, radiology or patient images): AI tools must not create or alter images that were not directly obtained in the research;
- **graphical abstracts**: general-purpose generative-AI image tools must not be used; Elsevier recommends dedicated scientific/professional illustration tools with appropriate publication rights;
- **cover art**: AI use may require prior permission from the journal/editor/publisher.

Official policy checked:

- https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals

The page states that the journal generative-AI policy was updated in **June 2026**.

## Consequence for the Structural manuscript

The current Structural submission figures are deterministic code-generated SVGs from frozen repository data/contracts. No generative-AI image generation or image editing is used for the manuscript figures.

Therefore:

- no AI-image caption disclosure is currently required for the committed Structural figures;
- the repository should not describe Elsevier's current policy as a blanket prohibition on all AI-assisted explanatory images or data visualizations;
- the manuscript-preparation AI declaration remains required because ChatGPT was used substantively for code review, reproducibility checks, literature triage, manuscript organization and language editing;
- any future use of generative AI on submission figures would require a fresh policy check and explicit documentation before use.

## Journal-specific Guide for Authors remains not machine-verifiable

The current Elsevier journal page exposes a link to the *Ecological Informatics* Guide for Authors on ScienceDirect, but automated retrieval of the journal-specific guide still returned HTTP 403 in this session.

Attempted journal-specific URL:

- https://www.sciencedirect.com/journal/ecological-informatics/publish/guide-for-authors

Therefore the following remain **submission-day/manual-browser gates**:

- exact article-type naming accepted by *Ecological Informatics*;
- exact manuscript/main-text length limits, if any;
- exact abstract limit;
- journal-specific keyword count;
- whether Highlights are required at initial submission or only later;
- graphical-abstract requirement/optionality for this journal specifically;
- reference style;
- figure file types, physical dimensions and minimum resolution;
- data/code statement requirements;
- single- vs double-anonymized peer-review model;
- journal-specific declaration placement or additional required declarations;
- publisher-rendered single-/double-column figure preview.

## Repository working contract after this check

Until the journal-specific guide is opened in a normal browser on the actual submission date, retain the conservative repository guards already enforced by CI:

- abstract <= 250 words;
- 3–5 Highlights;
- each Highlight <= 85 characters including spaces;
- complete submission package includes Data/Code Availability, declarations, cover letter, references and supplementary-material inventory;
- no scientific result, fingerprint, reference hierarchy, graph scale, taxon set or empirical denominator may be changed to satisfy formatting policy.

## Remaining release/submission boundary

This 2026-09-23 check **does not clear** the journal-specific live-policy gate and does not authorize final release or submission.

The remaining blockers still include:

- author list/affiliations/corresponding-author approval;
- author-contribution roles;
- funding;
- competing interests;
- ethics/permit relevance;
- originality/simultaneous-submission confirmation;
- author approval of the AI disclosure;
- creator order/software citation metadata;
- manual opening of the live *Ecological Informatics* Guide for Authors;
- publisher-rendered submission preview;
- final tag/archive DOI workflow after the human/live-policy gates clear.
