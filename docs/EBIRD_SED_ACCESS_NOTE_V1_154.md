# eBird Sampling Event Data access note v1.154

## Status

The current eBird confirmatory candidate is not blocked because official checklist-level sampling-event data do not exist.

Cornell Lab's official eBird documentation states that:

- the eBird Basic Dataset (EBD) is available to logged-in users after a data-access request;
- the download workflow offers **Sampling Event Data** in addition to observation-level EBD data;
- each Sampling Event Data row corresponds to an individual checklist;
- checklist-level data can be used to establish species non-detection/absence when checklist completeness semantics are satisfied;
- complete checklists and effort metadata are the features that make robust non-detection inference possible.

Official sources:

- https://support.ebird.org/en/support/solutions/articles/48000838205-download-ebird-data
- https://cornelllabofornithology.github.io/ebird-best-practices/intro.html

## Revised interpretation of the HOLD

The repository's current status

`HOLD_OFFICIAL_SAMPLING_EVENT_DATA_NOT_PRESENT`

should be read operationally:

> the required official SED file is not currently present in the Structural evidence workspace.

It should **not** be read as:

> Cornell does not provide such a dataset.

The HOLD is therefore potentially resolvable without redesigning the scientific question.

## Required next action

A user with an eBird account should:

1. sign in to eBird;
2. submit/confirm the EBD data-access request for the declared research use;
3. select/download the matching **Sampling Event Data** release together with the EBD release;
4. preserve the exact release date/version and raw file hashes;
5. provide the untouched SED/EBD files to the Structural workflow;
6. run the already-frozen response-independent checklist/effort audit before any species-level response semantics are opened.

## Firewall boundary

No species response should be inspected merely to decide whether SED is adequate.

The first audit should use only checklist/event fields required to establish:

- checklist identity;
- date/time;
- spatial location;
- protocol;
- duration/distance/observer effort where available;
- complete-checklist semantics;
- temporal coverage;
- island assignment;
- whether enough repeated sampling units exist for the frozen t0/t1/t2 design.

Only after this response-independent denominator is shown to be estimable should a new species-response protocol be authorized.

## Why this matters scientifically

This is the cleanest currently identified route to an independent test of occupancy-dependent isolation because eBird can separate two quantities that the global mammal snapshot cannot:

1. **colonization / appearance** on an island between periods;
2. **persistence / disappearance** from an island between periods.

That distinction directly tests the new synthesis:

> topology-specific source information may be stronger for assembly/colonization than for subsequent persistence after source loss.

The BALA contraction null therefore supplies the persistence-side boundary, while an admissible eBird transition analysis could test the colonization-side prediction without reusing the mammal response.
