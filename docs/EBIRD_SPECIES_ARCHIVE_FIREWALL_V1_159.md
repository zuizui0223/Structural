# eBird species-archive firewall v1.159

This gate is intentionally narrower than a species-response parser.

The only live candidate, global eBird islands 2002–2019, is still waiting for the official checklist-level Sampling Event Data (SED). If and only if the exact SED bytes pass v1.156 and the response-independent three-wave design passes v1.158, v1.159 permits the Dryad species ZIP to be downloaded as **opaque bytes**.

## What v1.159 reads

Only the ZIP central directory:

- member path and basename;
- extension;
- compressed and uncompressed byte counts;
- CRC32;
- compression method;
- local-header offset;
- directory flag.

The Dryad landing page documents one 464.55 MB `eBird-dataset.zip` containing 6,573 RData files. v1.159 requires exactly 6,573 RData/Rda members.

## What remains sealed

v1.159 does not decompress a member and does not deserialize RData.

Therefore it opens none of:

- species names;
- checklist submission IDs inside RData rows;
- detections;
- nondetections;
- annual occupancy;
- source-loss events;
- t2 outcomes.

It also deliberately does **not** parse dates from member names yet. The exact member manifest must first be committed. A later response-blind revision can then freeze the filename/date grammar and select only burned-pilot years before the first semantic species access.

## Why this extra step matters

The prospective eBird test needs complete-checklist nondetections from official SED and observed-species rows from Dryad to refer to the same checklist IDs. If we inspected RData contents before the temporal design and filename routing were frozen, species identities or source-loss patterns could influence which files/years are treated as pilot.

v1.159 prevents that route.

## Current external blocker

The official eBird Sampling Event Data request still has to be completed by the logged-in data user. Current eBird documentation states that Basic Dataset requests are typically approved within seven days and that Sampling Event Data can be downloaded as checklist-level details suitable for establishing absence on complete checklists.

Until the SED arrives, v1.159 is a frozen future gate only.
