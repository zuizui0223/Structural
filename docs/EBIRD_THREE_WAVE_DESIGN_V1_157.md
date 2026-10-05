# eBird three-wave design v1.157

## Purpose

The only live source-loss candidate is the global eBird island system. Its external blocker is the official checklist-level Sampling Event Data (SED) file.

v1.157 freezes the **next response-independent decision** before that file arrives: which three-year windows can ever become burned-pilot or confirmatory windows.

No species response is opened here.

## Fixed temporal windows

The 2002–2019 analysis period is partitioned once into six non-overlapping consecutive three-year windows:

- 2002–2004
- 2005–2007
- 2008–2010
- 2011–2013
- 2014–2016
- 2017–2019

For a window, an island is support-eligible only if the v1.155 surface marks the same OBJECTID as surveyed in all three years.

A window qualifies only if at least **25 islands** satisfy this three-year support rule.

The 25-island rule is not a biological sample-size claim. It is a response-independent floor preventing a nominal three-wave window from entering the burned pilot when almost no longitudinal island support exists. The burned pilot still decides whether species-level source-loss events, endpoint classes and leverage variation are estimable.

## Pilot versus confirmatory assignment

If fewer than four windows qualify, the candidate stops before species response access.

For the qualified windows, compute

`SHA256("ebird-three-wave-v1.157|" + window_id)`

and sort ascending.

The first `max(1, n_eligible - 4)` windows become burned pilot. The rest become confirmatory.

Therefore:

- 4 eligible → 1 pilot + 3 confirmatory
- 5 eligible → 1 pilot + 4 confirmatory
- 6 eligible → 2 pilot + 4 confirmatory

The assignment cannot be changed after SED support is observed.

## Why windows, not outcome-selected years

The conservation hypothesis requires temporal ordering:

- t0: source state
- t0→t1: source loss
- t1→t2: subsequent target persistence/loss

Using fixed, non-overlapping three-year windows prevents the same annual outcome from serving simultaneously as the endpoint of one candidate window and the exposure state of another.

It also means that a failed early or late window cannot be replaced by a nearby year after species outcomes are inspected.

## What remains sealed

Even after v1.157 passes:

- species names remain unopened;
- detections remain unopened;
- nondetections are not constructed;
- annual occupancy is not constructed;
- source-loss events are not constructed;
- no t2 outcome is opened.

The next irreversible step must be a separately frozen species-response firewall.
