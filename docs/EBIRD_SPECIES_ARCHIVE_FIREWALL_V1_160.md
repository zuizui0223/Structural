# eBird species-archive firewall v1.160

v1.159 already reduces the entire checklist/effort side of the eBird candidate to one response-independent handoff. If that handoff passes, the next risk is accidental opening of the Dryad observed-species archive before its temporal routing is frozen.

v1.160 prevents that.

## Access ceiling

The only permitted species-archive access is the ZIP central directory of Dryad DOI `10.5061/dryad.8931zcrpc`, file `eBird-dataset.zip`.

The published Dryad record documents:

- 464.55 MB archive;
- 6,573 RData files;
- observed non-pelagic bird rows;
- future semantic columns `SCI_NAME`, `SUB_ID`, longitude, latitude and `ISLAND_ID`.

v1.160 requires exactly 6,573 RData/Rda members but does not open any one of them.

The output manifest contains only member paths, extensions, compressed/uncompressed sizes, CRC32, compression method and local-header offset.

## What remains sealed

No v1.160 operation may:

- decompress an RData member;
- deserialize an R object;
- read species names;
- read checklist IDs inside response rows;
- construct detections or nondetections;
- construct annual occupancy;
- identify source-loss events;
- inspect t2 outcomes.

Even the filename/date grammar is intentionally left unfrozen until the exact member manifest exists.

## Next gate

After a successful v1.159 handoff and v1.160 inventory are both committed, a separate revision may freeze:

1. the exact member-name date parser;
2. the mapping of member dates to the already-frozen pilot and confirmatory windows;
3. a rule that semantic access may open **pilot-year members only**;
4. the join to complete-checklist `SUB_ID` values reconstructed from the exact same official SED bytes.

Confirmatory-year species rows remain sealed through that burned-pilot step.

## External blocker

The only external input still missing is the official eBird Sampling Event Data file. Current eBird documentation states that eBird Basic Dataset requests are available to logged-in users after a project-description form and are typically approved within seven days.
