"""Routing-header-exposed wrapper for the boreal bird pilot v1.161.

v1.160 learned only that the first CSV routing header is exactly "Islands".
No species name or occurrence value was parsed. This wrapper normalizes that
single known routing token to the v1.159 router's historical "Island" spelling
and delegates all biological parsing to the already-tested byte-level router.
"""
from __future__ import annotations

from structural.boreal_19island_bird_pilot_router import (
    Boreal19BirdPilotRouterError,
    RoutedBoreal19BirdPilot,
    route_bird_pilot,
)


class Boreal19BirdPilotRouterV161Error(RuntimeError):
    pass


def normalize_routing_header_only(response_csv_bytes: bytes) -> bytes:
    if not isinstance(response_csv_bytes, (bytes, bytearray)):
        raise Boreal19BirdPilotRouterV161Error("response must be bytes")
    raw = bytes(response_csv_bytes)
    bom = b"\xef\xbb\xbf"
    prefix = bom if raw.startswith(bom) else b""
    body = raw[len(prefix):]
    newline = body.find(b"\n")
    first_line = body if newline < 0 else body[:newline]
    comma = first_line.find(b",")
    if comma < 0:
        raise Boreal19BirdPilotRouterV161Error("bird CSV header has no comma")
    token = first_line[:comma].rstrip(b"\r")
    if token != b"Islands":
        raise Boreal19BirdPilotRouterV161Error(
            f"unexpected frozen routing header: {token!r}"
        )
    normalized = prefix + b"Island" + body[comma:]
    return normalized


def route_bird_pilot_v161(**kwargs) -> RoutedBoreal19BirdPilot:
    response = kwargs.pop("response_csv_bytes")
    normalized = normalize_routing_header_only(response)
    try:
        return route_bird_pilot(response_csv_bytes=normalized, **kwargs)
    except Boreal19BirdPilotRouterError as exc:
        raise Boreal19BirdPilotRouterV161Error(str(exc)) from exc
