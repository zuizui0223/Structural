# Source-loss leverage candidate triage v1.124

## Current ordering

The preferred response-unopened pre-intake is now **Azores BALA**, followed by Azores SLAM. Finnish common eider remains the best independent retrospective stress-test lane.

No candidate is confirmatory-eligible yet.

## 1. BALA — best match to the actual hypothesis

BALA is unusually close to the v1.123 design because its core native-forest sites were deliberately revisited in three major campaigns under a common sampling protocol.

That gives a natural temporal ordering:

    BALA1 -> BALA2 -> BALA3
      t0       t1       t2

The published resource describes a repeated core of roughly 30 sites in 15 fragments across seven islands. It is a sampling-event archive with separate Event and Occurrence tables.

This is stronger than constructing arbitrary three-year windows from an annual series: the three resurvey phases already exist as part of the study design.

### Why it is still only pre-intake

The metadata contain inconsistencies that directly affect the denominator: 30 versus 31 core sites and conflicting prose date ranges for BALA2 and BALA3. These must be resolved from Event rows before any species occurrence is read.

BALA also has only one meaningful three-wave sequence. Therefore the burned pilot and confirmation cannot be split by time. The v1.126 solution is a prospectively frozen **taxon partition**, implemented through an opaque router so confirmatory event-by-taxon occurrence combinations are not summarized during pilot routing.

## 2. SLAM — strong backup

The annual SLAM archive remains attractive because sampling events are separate from occurrences and survey effort can be audited first.

Its disadvantage relative to BALA is that t0/t1/t2 windows have to be constructed from annual event coverage, and its main archive has a known taxonomic completeness gap for Pico and Terceira spiders.

## 3. Finnish Common Eider — retrospective only

The eider series has excellent scale and repeated island counts, but broad decline and spatial redistribution are already published. Some grouped-island counts were also redistributed among individual islands.

It can stress-test the hypothesis after a frozen schema audit, but it cannot provide pristine confirmation.

## The ecological question is now concrete

The target claim is no longer “configuration matters.”

It is:

> **Among species that lose the same number of occupied islands, does losing populations that carried a larger share of external source access predict more later contraction among the populations that survived the first loss event?**

BALA is the first located dataset whose original sampling design naturally separates the loss event from the later response.

## Next gate

The immediate next event is deliberately non-ecological:

> obtain the BALA raw archive → inventory members without parsing occurrences → open Event core only → reconstruct the exact repeated core panel and phase membership.

If the Event core cannot reconcile the published sampling description, BALA stops before any species-level outcome is opened.
