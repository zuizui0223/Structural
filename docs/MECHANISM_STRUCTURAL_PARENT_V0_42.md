# Mechanism Structural parent requirement v0.42

For newly arriving systems, a mechanism lane may no longer use the historical v0.38 Structural queue as its production parent.

Production mechanism admission must match exactly one entry in the v0.42 live queue and therefore inherit both the exact v0.32 raw-pilot replay and the frozen response-quality contract.

The historical v0.38 queue remains accepted only for explicitly marked synthetic/provenance replay. This preserves the existing mechanism test chain without allowing future systems to bypass v0.42.

A valid v0.42 parent still authorizes no mechanism response, no mechanism claim and no TTF handoff. It only allows the existing lane-specific mechanism qualification process to continue.
