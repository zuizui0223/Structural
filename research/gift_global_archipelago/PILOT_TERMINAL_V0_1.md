# GIFT global archipelago burned pilot — terminal v0.1

## Decision

**TERMINAL STOP — NON-ESTIMABLE.**

The prospectively frozen GIFT 3.2 global-archipelago study opened only the three burned-pilot archipelago/list surfaces. The nine confirmatory archipelagos remain unopened and are not authorized for response access under this protocol version.

This is the intended role of the burned-pilot gate: reject a design that cannot support the frozen species-wise block-validation contract before confirmatory evidence is spent.

## Evidence spent

Burned-pilot workflow run: `35971291333`  
Preserved artifact: `10795879443`

The pilot opened 83 frozen pilot `list_ID` values and queried **zero confirmatory lists**. It fitted **zero models**, produced **no effect size**, **no prediction score**, and contributed **zero predictive evidence**.

Frozen raw pilot response:
- rows: **30,808**
- SHA-256: `6e63a66daae6a0107c9dca2c2336d2cea6a52cf28c6104689dfadd05195930e3`

The exact confirmatory list surface remained sealed:
`8bd8d48e7b63f6dbee7d7cfd421dad2e1215c4601fec9190f51465b15beb8a71`.

## Implementation correction

The first pilot implementation treated missing `questionable` / `quest_native` flags as if they positively marked an occurrence as questionable. That was inconsistent with the frozen response semantics.

The correction is purely interpretive and uses the **same already-open raw pilot response**:

- a questionable flag is active only when it is explicitly `1`;
- missing or `0` means the row is not positively flagged as questionable;
- no additional checklist request was made for the correction;
- the terminal PASS/STOP direction did not change.

Regression tests now guard this rule.

## Corrected estimability audit

| Burned-pilot archipelago | Islands | Species with presence | Estimable species | Gate |
| --- | ---: | ---: | ---: | --- |
| NW Aegean Sea Islands | 17 | 2,449 | **559** | PASS |
| Tuvalu | 17 | 37 | **5** | **FAIL** |
| Leeward Islands | 23 | 2,341 | **569** | PASS |

Frozen archipelago gate: at least **50 species** with at least 3 of 4 estimable spatial folds.

The study-level pass rule required **all three pilot archipelagos** to pass, with support for both the extreme and non-extreme regimes. Tuvalu failed decisively (5 < 50), so the study protocol terminates before confirmatory response access.

Across the pilot, 4,827 species × archipelago pairs were checked and 1,133 met the frozen estimability rule.

## What is not allowed now

Under this v0.1 protocol, do **not**:

- replace Tuvalu with a more favourable pilot archipelago;
- reduce the 50-species archipelago gate;
- weaken the 5/5 training-class gate;
- change the global q75 isolation threshold;
- change 25/50/125/250 km graph radii;
- weaken R3;
- lower the minimum archipelago size;
- reopen or query any of the nine confirmatory archipelago list surfaces.

Any later global-island study must be a genuinely new independent protocol justified without using the unopened confirmatory outcomes.

## Geological moderator status at closure

Roeble et al. (2024) Supplementary Data 3 was frozen before pilot access:
- source XLSX SHA-256: `fdca6086440c721e2766c3b73b96969c401b1a267a0cf9590c912d369d5e8597`;
- crosswalk fingerprint: `15dcfb61f2dd2f069d1908c9b93a2edc57e2b3709fd0e2561fe72378099f2002`.

Six confirmatory archipelagos had sufficient quantitative geology coverage. The continuous external oceanic-fraction moderator was design-estimable, whereas a pure continental-vs-oceanic categorical contrast was not (3 pure continental, 0 pure oceanic, 3 mixed). Because the Structural/GIFT estimability gate failed first, none of these confirmatory geology hypotheses are tested.

## Durable state

Future CI must replay only response-blind metadata/universe/protocol fingerprints and validate `pilot_terminal_receipt_v0_1.json`. It must **not query the pilot checklists again**.

Terminal receipt:
`research/gift_global_archipelago/pilot_terminal_receipt_v0_1.json`
