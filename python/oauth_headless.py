#!/usr/bin/env python3
"""Two-step OAuth for a machine that has no browser.

Follows the walkthrough in the Mailows MCP manual (PKCE S256, resource
https://mcp.mailows.com, token endpoint at https://id.namailu.cz/token).

Placeholders:
  MAIL_MCP_CLIENT_ID      HTTPS URL of your CIMD document, or a pre-registered id
  MAIL_MCP_REDIRECT_URI   Must match the document / registration exactly

The default client_id below is an example from the manual, not a working client.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import stat
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

AUTHORIZE_URL = "https://id.namailu.cz/authorize"
TOKEN_URL = "https://id.namailu.cz/token"
RESOURCE = "https://mcp.mailows.com"
SCOPES = "mcp:mail.messages.read mcp:mail.read mcp:mail.send"

# Placeholders — replace with your CIMD URL (or pre-registered Client ID)
# and an exact redirect_uri listed in that document.
DEFAULT_CLIENT_ID = "https://agent.example/oauth/client.json"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:27890/callback"

STATE_PATH = Path(os.environ.get("MAIL_MCP_OAUTH_STATE", "oauth-state.json"))
TOKEN_PATH = Path(os.environ.get("MAIL_MCP_TOKEN_FILE", ".mcp-token.json"))


def _client_id() -> str:
    return os.environ.get("MAIL_MCP_CLIENT_ID", DEFAULT_CLIENT_ID)


def _redirect_uri() -> str:
    return os.environ.get("MAIL_MCP_REDIRECT_URI", DEFAULT_REDIRECT_URI)


def _write_private(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def cmd_start(_: argparse.Namespace) -> int:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )
    state = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode().rstrip("=")
    client_id = _client_id()
    redirect_uri = _redirect_uri()

    # Persist the verifier. The code often comes back in a later process.
    _write_private(
        STATE_PATH,
        {
            "verifier": verifier,
            "state": state,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "created_at": int(time.time()),
        },
    )

    url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "resource": RESOURCE,
            "scope": SCOPES,
        }
    )
    print("Open this URL in a browser, sign in, pick mailboxes and confirm 2FA.")
    print("Copy the URL as code (do not paste it through a renderer that turns & into &amp;).")
    print()
    print(url)
    print()
    print(f"PKCE state written to {STATE_PATH} (mode 0600).")
    print("If you are not on the same machine as the callback, tick")
    print('"I am signing in from a server without a browser" on the consent screen.')
    print("Then run: python oauth_headless.py exchange --redirect-url '<FULL_URL>'")
    return 0


def cmd_exchange(args: argparse.Namespace) -> int:
    if not STATE_PATH.exists():
        print(f"Missing {STATE_PATH}. Run the start command first.", file=sys.stderr)
        return 1
    saved = json.loads(STATE_PATH.read_text())
    returned = urllib.parse.urlparse(args.redirect_url)
    query = urllib.parse.parse_qs(returned.query)
    if "code" not in query:
        print("The redirect URL has no code= parameter.", file=sys.stderr)
        return 1
    returned_state = (query.get("state") or [None])[0]
    if returned_state and returned_state != saved["state"]:
        print("state parameter does not match the saved value. Aborting.", file=sys.stderr)
        return 1

    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": query["code"][0],
            "redirect_uri": saved["redirect_uri"],
            "client_id": saved["client_id"],
            "code_verifier": saved["verifier"],
            "resource": RESOURCE,
        }
    ).encode()
    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request) as response:
        token = json.load(response)

    expires_in = int(token.get("expires_in") or 0)
    token["expires_at"] = time.time() + expires_in
    token["resource"] = RESOURCE
    _write_private(TOKEN_PATH, token)
    try:
        STATE_PATH.unlink()
    except OSError:
        pass

    print(f"Token saved to {TOKEN_PATH} (mode 0600). Not printed.")
    print(f"expires_in={expires_in}s. Refresh with the saved refresh_token before expiry.")
    print("Export MCP_ACCESS_TOKEN from the access_token field when you run the other scripts.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("start", help="Print the authorization URL and save the PKCE verifier")
    ex = sub.add_parser("exchange", help="Exchange the redirect URL for tokens")
    ex.add_argument(
        "--redirect-url",
        required=True,
        help="The full URL shown in the browser after consent (includes code, state, iss)",
    )
    args = parser.parse_args()
    if args.command == "start":
        return cmd_start(args)
    return cmd_exchange(args)


if __name__ == "__main__":
    raise SystemExit(main())
