# ChatGPT

Verified from the [MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples).

In a supported workspace:

1. Turn **Developer mode** on.
2. Open **Settings / Workspace settings → Apps → Create**.
3. Enter the endpoint `https://mcp.mailows.com/mcp`, choose **OAuth** and run **Scan Tools**.
4. During the scan, ChatGPT opens the Mailows sign-in and consent flow. Pick the agent mailboxes and confirm 2FA.
5. After the tool list changes, run a new Scan / Refresh; the client may be holding an approved snapshot.

During the pilot, the operator has to confirm the exact OpenAI callback and Client ID in advance. A hosted application can use pre-registration or its own HTTPS Client ID Metadata Document.

Mailows is also listed in the ChatGPT apps directory, so some workspaces can connect it without creating a custom app. The endpoint and OAuth consent are the same.

## OpenAI Responses API (your own backend)

If you call the OpenAI Responses API yourself, your backend has to complete OAuth and pass a **short-lived MCP access token** in `authorization`. Never put a portal API key (`dmk_live_…`) or a refresh token in that field. The backend must supply `authorization` with every new request; OpenAI does not store it in the response.

```json
{
  "type": "mcp",
  "server_label": "mailows",
  "server_description": "Sending from permitted Mailows agent mailboxes",
  "server_url": "https://mcp.mailows.com/mcp",
  "authorization": "<short-lived MCP access token>",
  "allowed_tools": [
    "mail_health",
    "mail_list_inboxes",
    "mail_list_messages",
    "mail_read_message",
    "mail_send_message"
  ],
  "require_approval": "always"
}
```

`require_approval` is an **OpenAI** setting. It is not a Mailows approval queue. Mailows sends the message as soon as `mail_send_message` runs; there is no composer and no per-email confirmation on the Mailows side. If you want a human checkpoint, keep it in your client (as above) or rely on the portal allowlist, quotas, and pause / revoke.

The official manual’s snippet uses `server_label: "namailu"`; the label is yours to choose.
