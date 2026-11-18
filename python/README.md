# Python examples

These scripts talk to `https://mcp.mailows.com/mcp` with the official Python MCP SDK (`mcp` 2.x) over Streamable HTTP. The Mailows server itself runs `mcp==2.0.0` and the wire contract is protocol revision `2026-07-28`. A new client must not send `Mcp-Session-Id`.

MCP accepts OAuth access tokens only. A portal API key will be refused.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set `MCP_ACCESS_TOKEN` to a short-lived access token for the resource `https://mcp.mailows.com`. You can mint one with the helper below, or copy it from a client that has already finished OAuth (do not commit it).

```bash
cp ../.env.example ../.env   # then edit; or export the variables
python oauth_headless.py start
# Open the printed URL, sign in, copy the full redirect URL from the address bar
python oauth_headless.py exchange --redirect-url '<PASTE_FULL_REDIRECT_URL>'
export MCP_ACCESS_TOKEN="$(python -c 'import json; print(json.load(open(".mcp-token.json"))["access_token"])')"
```

`oauth_headless.py` follows the “signing in from a server without a browser” walkthrough in the [MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples). Placeholders you must replace:

- `MAIL_MCP_CLIENT_ID` — the HTTPS URL of your Client ID Metadata Document, or a pre-registered Client ID. The example default `https://agent.example/oauth/client.json` is **not** registered.
- `MAIL_MCP_REDIRECT_URI` — must match the document (or the pre-registered client) character for character. The example uses `http://127.0.0.1:27890/callback`.

Publish a CIMD document at that HTTPS URL before you start. A minimal document is in the manual; Dynamic Client Registration is off.

The helper writes `.mcp-token.json` (mode 0600, gitignored) and does not print the tokens. Honour `expires_in` from the token response when you refresh; do not hard-code a lifetime. The manual’s token-exchange snippet and its metadata table disagree on access-token lifetime (10 minutes vs 24 hours), so the response field is the source of truth.

## Send a message with an attachment

```bash
export MAIL_TO='finance@example.com'          # already on the send allowlist
export MAIL_ATTACHMENT='./fixtures/hello.txt'
python send_with_attachment.py
```

The script:

1. Calls `mail_health` and `mail_list_inboxes`.
2. Prepares the file with `mail_prepare_attachment_uploads` (`size` and SHA-256 of the original bytes, plus a shared `idempotency_key`).
3. Prefers a raw HTTPS PUT to the one-time upload URL. If that is blocked and `inband_upload.eligible` is true, it falls back to `mail_upload_attachment_chunk` in 8 KiB blocks.
4. Calls `mail_send_message` with the returned `attachment_ids` and the same `idempotency_key`.

**Placeholder:** the exact JSON field names for the prepare result’s upload URL and upload token are not fully spelled out in the manual (the curl example uses `$UPLOAD_URL` and `$UPLOAD_TOKEN`). The script looks for several obvious keys and prints the raw `structuredContent` if it cannot find them, so you can map the fields without guessing in production.

Leave `MAIL_INBOX_ID` empty when the grant has a single mailbox. The recipient must already be on the mailbox send allowlist. A Free agent may have at most one recipient per message. Total attachments: at most 10 files and 10 MiB of original bytes.
