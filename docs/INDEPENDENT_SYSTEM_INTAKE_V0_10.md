# Independent system response-blind intake v0.10

## Purpose

The mechanism pipeline is executable through frozen scoring, but there is still no empirical system.

v0.10 defines how a **new independent system enters** without reopening old candidates or inspecting outcome direction.

This gate sits before v0.31.

A PASS authorizes only:

`construct_v0_31_partition_protocol_only`.

It does not open a pilot response.

## Independent arrival, not candidate hunting

The intake contract explicitly requires:

`candidate_hunt_active = false`.

The system must arrive independently of the existing A-Islands/Tanzania result direction.

Selection cannot use:

- response direction;
- connectivity result;
- a favourable published effect;
- post-outcome graph scale;
- post-outcome endpoint choice;
- post-outcome mechanism-lane choice.

## Known closed systems stay closed

The exact historical systems already consumed or disqualified in Structural cannot re-enter through the new mechanism program.

The intake validator hard-stops the known PNW, RMNP, Great Lakes and Hungary candidate identities.

This prevents a closed dataset from being relabelled as “independent”.

## Source identity and file firewall

Before semantic response access, intake freezes:

- system id;
- source id;
- source version;
- one source fingerprint;
- file-level SHA-256 values;
- file roles.

Allowed roles are:

- `safe_metadata`;
- `geometry`;
- `response`;
- `unknown`.

Every `response` and `unknown` file must have:

`opened = false`.

At least one response file must already be identified so the firewall is operational rather than aspirational.

## Reuse of existing fresh-candidate triage

v0.10 does not invent another freshness classifier.

It reuses `src/structural/candidate_triage.py`.

Therefore:

- response result already seen → STOP;
- connectivity question already published → STOP;
- no immutable source identity → STOP;
- no reproducible geometry → STOP;
- response cannot be firewalled → STOP;
- unresolved response-blind metadata → HOLD;
- complete response-blind metadata → eligible to construct v0.31.

## Mechanism lanes are requested from metadata only

A new system may request any subset of M1–M4, but each lane needs the appropriate response-blind support:

- M1 colonization → temporal transition metadata;
- M2 rescue/persistence → temporal transition metadata;
- M3 historical legacy → genetic sampling metadata;
- M4 environmental proxy → environmental predictor metadata.

This is only a statement that the lane can be designed.

It is not estimability evidence and does not authorize response access.

## Hypothesis inheritance

Every intake is bound to the already-frozen hypotheses:

- Structural v0.31 partition machinery;
- extreme-isolation/source-decoupling hypothesis v0.3;
- mechanism-discrimination framework v0.1.

A newly arriving system does not create a new favourable threshold or mechanism family.

## Next step after PASS

PASS means only:

1. construct a v0.31 burned-pilot/confirmatory partition protocol;
2. fingerprint the partitions, endpoint semantics and support gates;
3. keep all pilot and confirmatory responses sealed.

Only the normal downstream chain may later spend evidence.

## Current state

There is still no current empirical system.

`current_systems = []`.
