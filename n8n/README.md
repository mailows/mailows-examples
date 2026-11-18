# n8n workflow template

**Placeholder.** n8n is not documented in the [Mailows MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples). This folder is an importable starting point built from n8n’s MCP Client Tool node (typeVersion 1.4, transport `httpStreamable`). Expect to adjust credentials and node versions for your n8n build.

Mailows MCP requires OAuth 2.1 with PKCE and the `resource` value `https://mcp.mailows.com`. A portal API key will not work.

## What to do

1. In n8n, **Workflows → Import from file** and choose `mailows-mcp-template.json`.
2. Open the **Mailows MCP** node:
   - Endpoint: `https://mcp.mailows.com/mcp`
   - Server Transport: **HTTP Streamable** (`httpStreamable`). Do not use SSE.
   - Authentication: **MCP OAuth2** if your n8n version offers it and it can send PKCE S256 plus the `resource` parameter. Otherwise obtain a short-lived access token out of band (see [python/oauth_headless.py](../python/oauth_headless.py)) and use **Bearer Auth**. Tokens expire; honour `expires_in`.
3. Attach the model credential on the Agent node (placeholder).
4. On the Mailows consent screen, pick the agent mailbox, grant only the scopes you need, and confirm 2FA.
5. Keep the workflow inactive until the allowlist and quotas are set. Start with `mail_health` / `mail_list_inboxes`. Do not send mail while testing.

Whether n8n’s MCP OAuth2 client sends the `resource` parameter and supports a CIMD `client_id` (an HTTPS URL, public client, no secret) has **not** been verified against Mailows. If OAuth fails with a missing `resource` or `client_id` error, use the out-of-band bearer-token path and treat n8n OAuth as not yet compatible.

The schedule trigger is set to 06:00 and is **inactive**. See [recipes/daily-research-agent.md](../recipes/daily-research-agent.md) for the digest idea this template sketches.
