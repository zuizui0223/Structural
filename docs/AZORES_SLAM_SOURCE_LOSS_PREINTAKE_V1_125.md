# Azores SLAM source-loss pre-intake v1.125

## Why this system is different

The Azores SLAM archive is the first candidate found in this search where **sampling events and species occurrences are separate data objects**.

That matters for the v1.123 source-loss hypothesis. We can inspect when and where standardized sampling occurred without first reading which species were present. The intended sequence is therefore:

> archive inventory → Event-core coverage audit → freeze eligible islands/plots/years and temporal routing → freeze taxon universe and endpoint → only then parse focal occurrence rows.

This preserves a substantially cleaner response boundary than an occurrence-only archive.

## Metadata-level design

The archive reports 42 SLAM traps distributed across seven Azorean islands: Flores, Faial, Pico, Graciosa, Terceira, São Miguel and Santa Maria. Sampling was approximately quarterly, around March, June, September and December, over the long-term programme beginning in 2012.

The Darwin Core Archive separates an Event core from an Occurrence extension. The public metadata currently report 893 Event rows. They give two inconsistent counts for the occurrence extension—14,922 in the Data Records section and 14,924 in the methods text. That discrepancy becomes a **pre-response integrity check**, not something to hand-wave away.

## Response firewall

Before the focal occurrence protocol is frozen, only the following may be inspected:

- archive filenames, sizes and hashes;
- metadata XML;
- Event identity;
- island/locality;
- plot/trap identity;
- event date;
- response-independent coordinates;
- sampling-protocol fields.

Taxon identity, abundance and occurrence fields in the Occurrence extension remain unopened for Structural source-leverage analysis.

The Event core is therefore treated as sampling geometry/effort, not as ecological response.

## Araneae must not silently become absences

The main archive explicitly omits spider records from Pico and Terceira because those records were published in separate datasets. That creates a dangerous asymmetry: a blank spider record in the main archive on those islands is **not evidence of absence**.

The primary v1.125 universe therefore excludes Araneae unless the companion spider archives are merged under a separate, frozen pre-response crosswalk.

The same principle applies to higher taxa intentionally outside the SLAM taxonomic target: they are not candidates for a zero-filled occurrence matrix merely because no row appears.

## Three-time-window rule

No calendar years are selected yet.

The Event-only audit must first determine which island-years meet one common sampling-completeness rule. The current pre-intake proposes a deterministic next rule:

1. identify consecutive three-year windows using only Event rows;
2. require the same minimum event completeness in every retained island-year;
3. require at least three islands in a window;
4. among eligible **non-overlapping** windows, assign the earliest to the burned pilot and the latest to confirmation;
5. if two disjoint eligible windows do not exist, stop.

This prevents selecting a convenient period after looking at which taxa declined.

The provisional minimum is at least three standardized sampling occasions per island-year, with four preferred. The final rule can only be tightened or clarified from the Event schema before any focal occurrence parse; it cannot be chosen using species outcomes.

## Endpoint ceiling

Even if the later test succeeds, the endpoint is:

> **subsequent loss of observed occurrence/use within the standardized sampled forest network.**

It is not whole-island extinction unless an independent observation model justifies that stronger interpretation.

## Why this candidate is promising

Compared with the current alternatives:

- it has repeated standardized sampling rather than opportunistic presence records;
- survey-event information can be audited separately from species outcomes;
- many arthropod taxa can potentially supply repeated species-level transition events;
- multiple islands provide a natural spatial source context.

The weaknesses are equally concrete: only seven islands, incomplete taxonomic coverage, habitat-specific plots, possible missing sampling years, and the need to aggregate plot events to island-level source states without inventing surveyed zeros.

For that reason v1.125 is only a **pre-intake**, not a result and not a confirmatory admission.
