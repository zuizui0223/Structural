# Indo-Pacific atoll burned-pilot terminal stop v0.22

## Outcome

The first prospective Indo-Pacific atoll native-plant burned pilot is **terminally closed**.

The one-shot response execution began only after the corrected v0.31b/v0.42b pre-pilot freeze was merged and CI-green.

During semantic parsing of the 13 frozen pilot blocks, the router encountered a plant presence code:

    U

The frozen endpoint domain admitted only:

- `N` = native;
- `I` = introduced.

The public data article also documented plant nativeness status only as N and I before response access.

Because `U` was outside the frozen response domain, the router stopped immediately with:

    AtollPilotRouterError:
    unexpected presence code in opened pilot row: 'U'

## Evidence boundary

The failure occurred **after pilot response semantic access started**.

Therefore this corrected protocol version is consumed.

Exact evidence state:

- pilot response accessed: **true**;
- confirmatory response accessed: **false**;
- confirmatory species values parsed: **0**;
- confirmatory presence values parsed: **0**;
- effect size: **none**;
- prediction score: **none**;
- predictive-denominator contribution: **0**;
- source-pool-handoff direction scored: **no**.

The fixed pilot species universe was not completed.
The exact three-column pilot surface was not completed.
v0.32 estimability was not completed.
v0.42 response-quality survival was not completed.

## Scientific interpretation

This is **not** evidence for or against source-pool handoff.

It is an endpoint-value-domain failure:

> the burned pilot exposed a real response state that was absent from the prospectively frozen endpoint codebook.

That is different from:

- PNW/RMNP endpoint-class collapse;
- LandFrag response-quality attrition;
- a negative topology/connectivity effect.

No ecological effect was estimated here.

## No rescue

The following are prohibited after this response exposure:

- deciding post hoc what `U` means for the frozen endpoint;
- mapping `U` to native, introduced, absence, or missing and rerunning;
- changing the fixed species-support rule;
- changing pilot/confirmatory spatial blocks;
- lowering v0.32 or v0.42 gates;
- opening the unused confirmatory response as fresh evidence under a replacement protocol.

The dataset may later be discussed descriptively or used in an explicitly retrospective engineering lane, but it cannot be restored to pristine confirmation for this hypothesis.

## Execution provenance

- PR: #122
- workflow run: `36244607643`
- job: `108411348614`
- frozen parent main commit: `55190a6153f744bb3a000af8652fd22f0b37b7e6`
- v0.31b fingerprint: `ee8cccc38fb8f4602e05e97d9d875c5ad8773280460c0dafca36ac03fe5871f5`
- v0.42b fingerprint: `1b3ad5da960ceac60e594b3ed664a39835e2f49ba1f7d70bfd32ee1c54e28fc6`

The workflow's final evidence-ceiling assertion itself hit a secondary receipt-robustness bug because exception receipts did not populate every optional firewall counter. That wrapper issue does not change the scientific terminal state: the response execution step had already started, the `U` mismatch had already stopped the router, and no rerun is authorized.

## General lesson

For future categorical-response systems, "response-sealed" must include not only sealed values but a prospectively frozen **complete response-value domain** when such a codebook can be established.

If the pilot reveals an out-of-domain code after opening, that protocol version stops rather than redefining the endpoint around the observed value.
