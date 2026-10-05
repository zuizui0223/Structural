# eBird three-wave design v1.158

v1.157 handles acquisition of the official eBird Sampling Event Data (SED). v1.158 freezes what happens **after** that file passes the same-byte v1.156 response-independent support chain.

No species response is opened here.

## Six fixed three-year windows

The 2002–2019 period is partitioned once:

- 2002–2004
- 2005–2007
- 2008–2010
- 2011–2013
- 2014–2016
- 2017–2019

A candidate window is supported only if at least **25 identical island OBJECTIDs** are marked surveyed in all three years by the frozen v1.155 rule.

The 25-island threshold is a survey-support floor, not the biological estimability test. Species-level source-loss events, class balance and leverage variation can still fail later in the burned pilot.

## Deterministic pilot/confirmatory split

At least four of the six windows must qualify. Otherwise the candidate stops before species access.

Eligible windows are ranked by:

`SHA256("ebird-three-wave-v1.158|" + window_id)`

The first `max(1, n_eligible - 4)` become burned pilot; all remaining eligible windows become confirmatory.

Thus:

- 4 eligible → 1 pilot + 3 confirmatory
- 5 eligible → 1 pilot + 4 confirmatory
- 6 eligible → 2 pilot + 4 confirmatory

No manual reassignment is allowed.

## Why this matters

The conservation hypothesis requires:

- t0: source state;
- t0→t1: source loss;
- t1→t2: subsequent target persistence/loss.

Fixed non-overlapping windows prevent year selection after species outcomes and prevent the same annual endpoint from being recycled into an adjacent candidate window.

## What remains sealed after v1.158

Even a successful v1.158 result still has:

- zero species names opened;
- zero species detections opened;
- zero nondetections constructed;
- zero annual species occupancy states;
- zero source-loss events;
- zero t2 outcomes.

The next step must be a separately committed species-response firewall.
