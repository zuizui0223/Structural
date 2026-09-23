# Structural v0.1.0 release preflight — 2026-09-23

## Decision

**HOLD. Do not create the final `v0.1.0` tag, GitHub Release, or final archive DOI yet.**

The scientific and repository-presentation state is frozen. The remaining blockers are human approvals and the journal-specific submission check.

This preflight does not reopen science.

## Additional archive-content gate discovered on 2026-09-23

The authoritative A-Islands raw outcome artifact was located in the source repository `zuizui0223/eog`, re-downloaded, and independently verified against committed provenance.

The current GitHub Actions artifact expires at **2026-11-10T04:42:52Z** and is not yet preserved outside GitHub Actions.

Therefore, after the human/policy HOLD is cleared, release readiness must still remain at `HOLD_ARCHIVE_CONTENT_GATES` until the verified raw artifact has been copied into the durable final archive and reverified there.

Canonical receipt:

`validation/aislands_isolation_adequacy_20260812/artifact_retention_receipt_20260923.json`

## What is already closed

- scientific content;
- A-Islands original conditional-ordering result;
- prospective A-Islands strong-reference result;
- Tanzania strong-reference result;
- frozen fingerprints and result direction;
- Figure 1–5 scientific inputs;
- presentation-v2 Figure 1/2 assets;
- repository-side visual QA;
- Structural dynamic candidate/admission status;
- v0.40 gate infrastructure;
- v0.41 canonical current status;
- Elsevier-wide policy refresh dated 2026-09-23.

## What still blocks v0.1.0

Author/human approval:

- author list and affiliations;
- corresponding author;
- contribution roles;
- funding;
- competing interests;
- ethics/permit relevance;
- originality / simultaneous submission;
- generative-AI disclosure;
- creator order and software citation metadata.

Manual journal check:

- live *Ecological Informatics* Guide for Authors in a normal browser;
- exact article-type naming;
- journal-specific abstract/keyword/length rules;
- reference style;
- data/code requirements;
- figure formats, physical dimensions and DPI;
- anonymization/peer-review model;
- publisher-rendered preview.

Release/archive:

- reserve the final archive DOI only after the human/manual gates clear;
- replace `<RELEASE_TAG>` and `<ARCHIVE_DOI>` in an identifier-only repository change;
- require full CI green;
- rebuild the final submission package;
- create `v0.1.0` at exactly the verified release commit;
- create the matching public GitHub Release/archive;
- verify DOI/tag/package provenance after publication.

## Machine-readable HOLD

The authoritative preflight object is:

`manuscript/submission/release_preflight_v0_1_0.json`

CI verifies that while status is HOLD:

- package version remains `0.1.0`;
- target tag remains `v0.1.0`;
- release/DOI placeholders remain unresolved;
- author metadata is not falsely marked complete;
- journal-specific Guide verification remains false;
- final release actions remain unauthorized;
- frozen A-Islands and Tanzania fingerprints match the submission manifest.

## Current public-release state

The GitHub Releases endpoint returned no releases during the 2026-09-23 audit.

That external observation is not used as a scientific result and is not treated as a CI invariant. The repository HOLD state itself is defined by the committed preflight object and unresolved author/manual gates.

## What happens when the human gates clear

Do **not** edit this file by simply changing HOLD to GO.

First:

1. complete author-approved metadata and declarations;
2. record the live journal-specific Guide check;
3. reserve the archive DOI;
4. make the identifier-only repository update;
5. run full CI and package rebuild;
6. create a new release-ready preflight receipt tied to that exact release candidate.

Only that later receipt may authorize the final tag/release workflow.
