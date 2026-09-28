#!/usr/bin/env python3
"""Prepare a short-lived Dryad bearer token for the v0.73 workflow.

Preferred mode exchanges DRYAD_CLIENT_ID + DRYAD_CLIENT_SECRET for a token.
A pre-existing DRYAD_TOKEN may be used only as an explicit fallback. The token
is written only to the GitHub Actions environment file supplied by the runner;
it is never printed or persisted in the receipt.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, build_opener


TOKEN_URL = "https://datadryad.org/oauth/token"


class DryadTokenError(RuntimeError):
    pass


def _clean_secret(value: str, name: str) -> str:
    value = str(value or "")
    if not value:
        return ""
    if "\n" in value or "\r" in value:
        raise DryadTokenError(f"{name} is malformed")
    return value


def mint_token(
    client_id: str,
    client_secret: str,
    *,
    opener=None,
) -> tuple[str, int | None]:
    client_id = _clean_secret(client_id, "DRYAD_CLIENT_ID")
    client_secret = _clean_secret(client_secret, "DRYAD_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise DryadTokenError("client credentials are incomplete")

    payload = urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }).encode("utf-8")
    request = Request(
        TOKEN_URL,
        data=payload,
        headers={
            "Content-Type": (
                "application/x-www-form-urlencoded;charset=UTF-8"
            ),
            "Accept": "application/json",
            "User-Agent": "Structural-v0.73",
        },
        method="POST",
    )
    opener = opener or build_opener()
    try:
        with opener.open(request, timeout=60) as response:
            raw = response.read()
    except Exception as exc:
        raise DryadTokenError(
            f"token request failed: {type(exc).__name__}"
        ) from None

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DryadTokenError("token response was not valid JSON") from exc

    token = _clean_secret(data.get("access_token", ""), "access_token")
    if not token:
        raise DryadTokenError("token response omitted access_token")
    token_type = str(data.get("token_type", "")).lower()
    if token_type and token_type != "bearer":
        raise DryadTokenError("token response had unexpected token_type")

    expires = data.get("expires_in")
    if expires is not None:
        if isinstance(expires, bool):
            raise DryadTokenError("token response had invalid expires_in")
        try:
            expires = int(expires)
        except (TypeError, ValueError) as exc:
            raise DryadTokenError("token response had invalid expires_in") from exc
        if expires <= 0:
            raise DryadTokenError("token response had nonpositive expires_in")

    return token, expires


def prepare_token(
    *,
    client_id: str,
    client_secret: str,
    fallback_token: str,
    github_env: Path,
    opener=None,
) -> dict:
    client_id = _clean_secret(client_id, "DRYAD_CLIENT_ID")
    client_secret = _clean_secret(client_secret, "DRYAD_CLIENT_SECRET")
    fallback_token = _clean_secret(fallback_token, "DRYAD_TOKEN")

    if bool(client_id) != bool(client_secret):
        raise DryadTokenError(
            "DRYAD_CLIENT_ID and DRYAD_CLIENT_SECRET must be supplied together"
        )

    if client_id and client_secret:
        token, expires = mint_token(
            client_id,
            client_secret,
            opener=opener,
        )
        mode = "client_credentials_minted_token"
    elif fallback_token:
        token = fallback_token
        expires = None
        mode = "preexisting_short_lived_token"
    else:
        raise DryadTokenError(
            "no Dryad credential source is configured"
        )

    github_env.parent.mkdir(parents=True, exist_ok=True)
    with github_env.open("a", encoding="utf-8") as handle:
        handle.write(f"DRYAD_TOKEN={token}\n")

    return {
        "schema": "structural.dryad_token_prepare_result.v0_73",
        "status": "token_installed_in_runner_environment",
        "mode": mode,
        "expires_in_seconds": expires,
        "token_persisted_in_receipt": False,
        "client_credentials_persisted_in_receipt": False,
        "counts_as_empirical_evidence": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-env", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    client_id = os.environ.get("DRYAD_CLIENT_ID", "")
    client_secret = os.environ.get("DRYAD_CLIENT_SECRET", "")
    fallback = os.environ.get("DRYAD_TOKEN_FALLBACK", "")

    try:
        result = prepare_token(
            client_id=client_id,
            client_secret=client_secret,
            fallback_token=fallback,
            github_env=args.github_env,
        )
    except (OSError, DryadTokenError) as exc:
        result = {
            "schema": "structural.dryad_token_prepare_result.v0_73",
            "status": "STOP",
            "reason": str(exc),
            "token_persisted_in_receipt": False,
            "client_credentials_persisted_in_receipt": False,
            "counts_as_empirical_evidence": False,
        }
        code = 2
    else:
        code = 0

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
