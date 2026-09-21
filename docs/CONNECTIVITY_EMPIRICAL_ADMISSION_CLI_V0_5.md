# Connectivity empirical admission CLI v0.5

The v0.4 response-blind admission contract is now executable.

## Usage

    python scripts/check_connectivity_empirical_protocol.py path/to/protocol.json

Exit codes:

- 0 — qualified for the next response-blind source/schema freeze stage;
- 1 — invalid JSON/schema/type;
- 2 — valid protocol object but scientific STOP.

A qualified decision is **not** outcome-access authorization. It only means the candidate contains the minimum frozen information required to continue the prospective pipeline.

## Examples

Qualified synthetic example:

    python scripts/check_connectivity_empirical_protocol.py examples/connectivity_empirical_protocol_qualified_v0_5.json

STOP example:

    python scripts/check_connectivity_empirical_protocol.py examples/connectivity_empirical_protocol_stop_v0_5.json

The STOP fixture has response_accessed=true and must never be promoted by repairing other fields.

## Operational sequence

    candidate metadata
        → v0.5 CLI admission
        → source/schema verification
        → immutable protocol freeze
        → one-shot outcome authorization
        → held-out scoring
        → v0.3 state ladder
        → portability test if independently declared

This keeps protocol qualification separate from biological outcome interpretation.
