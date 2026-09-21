# Retrospective connectivity pilots v0.6

## Status

This lane is **development only**. None of the systems below counts as fresh evidence for the current Structural paper or as confirmatory evidence for the typed-connectivity programme.

The reason is simple: their publications and repository metadata expose the biological outcomes. The v0.4/v0.5 fresh-admission firewall would therefore stop them at `response_accessed=true`.

They remain useful for a different purpose: exercising real-data adapters and checking whether the v0.1–v0.3 objects can represent actual connectivity studies without silently collapsing operator semantics.

## Primary pilot — Davis et al. 2026 / Heliconia tortuosa

Dataset DOI: **10.5061/dryad.3ffbg7b08**

This is the strongest engineering match currently identified because one fragmented tropical landscape contains all three representation levels needed by the new ladder:

1. **structural geometry**
   - habitat amount/configuration;
   - structural connectivity metrics;
2. **process model**
   - hummingbird-movement-informed functional connectivity;
   - gap-crossing probabilities and movement scales;
3. **realized biological endpoint**
   - contemporary pollen-mediated genetic outcomes.

The pilot operator is fixed as **pollinator-mediated pollen flow**.

The development task is not to ask whether the published conclusion is true again. It is to determine whether the source files can be mapped cleanly onto:

    current ecological reference
        → structural geometry
        → pollen-process connectivity
        → contemporary pollen-mediated endpoint

without using outcome-driven feature selection.

### Adapter questions

Before fitting anything, inspect only schema/provenance needed to answer:

- What is the exact patch/population identifier?
- Which variables are current-state reference variables?
- Which metrics are structural geometry?
- Which are movement-informed process-model metrics?
- Which genetic variables are endpoints rather than predictors?
- Which spatial scale/rule produced each connectivity metric?
- Are years repeated within patches?
- What is the correct held-out ecological unit?
- Can the published analysis outputs be ignored while reconstructing a clean development table?

No result from this pilot can be promoted to fresh confirmation.

## Secondary pilot — Noreen et al. 2016 / Koompassia malaccensis

Dataset DOI: **10.5061/dryad.663fb**

This system is useful for a different reason: the same urban-fragmented tree population contains **realized pollen and seed dispersal operators** inferred by parentage.

It can test whether the software and reporting surface keep:

- pollen flow;
- seed dispersal;

as separate operators rather than averaging them into one generic connectivity variable.

Its three-patch design is too small for a strong general predictive benchmark, and the published outcomes are already visible. Therefore it is an operator-bookkeeping pilot, not a portability confirmation.

## Tertiary boundary pilot — Delnevo 2026 / Conospermum undulatum

Dataset DOI: **10.5061/dryad.95x69p907**

This provides recent paternity data across fragmented and non-fragmented urban populations. It is retained as a fragmentation-boundary example, but the dataset abstract already reveals the main pollen-isolation result. It is not fresh.

## Development order

The v0.6 order is fixed:

1. Davis schema/provenance adapter audit;
2. freeze a retrospective adapter contract;
3. build a typed analysis table without post-hoc candidate search;
4. run the v0.3 ladder only as an engineering replay;
5. optionally use Koompassia to exercise two realized operators in one system;
6. keep all outputs labelled `counts_as_fresh_evidence=false`.

## Why this matters

Published datasets are still useful even when they cannot provide response-blind confirmation.

They can falsify software assumptions:

- an endpoint may not align with the declared ecological unit;
- a process metric may actually be a structural proxy;
- movement semantics may differ between files;
- multiple operators may share a label but not a life-cycle role;
- scale choices may already depend on the published outcome.

Finding such problems now strengthens the future fresh protocol without consuming a fresh biological endpoint.

## Promotion boundary

A future result may count as fresh only from a new protocol that passes v0.5 **before its response is opened**.

Retrospective success cannot be converted into fresh evidence later.
