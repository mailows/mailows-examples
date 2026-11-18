# Claude app / Desktop

Verified from the [MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples).

On an individual account, open **Customize → Connectors → Add custom connector**. On Team / Enterprise the Owner adds the server first under **Organization settings → Connectors**, and a member then chooses **Connect**.

1. Paste `https://mcp.mailows.com/mcp`.
2. If the form asks for a Client ID, use `namailu-claude-pilot`. That value is neither a secret nor your account ID. Leave the Client Secret empty.
3. Finish OAuth in the new window: pick the agent mailboxes, choose whether the app may read message content and send, and confirm 2FA.
4. Once connected, enable the connector only in the conversations where Claude is meant to work with mail.

The allowed hosted callback is exactly `https://claude.ai/api/mcp/auth_callback`.

In Claude Code the same server can be added with one command; see [claude-code.md](claude-code.md).

## Attachments from Claude

Small files can be transferred over MCP when a raw PUT is blocked (the set must be at most 256 KiB). For larger attachments, Claude uploads from its code-execution sandbox:

- Settings → Capabilities → Code execution and file creation: **Allow network egress** must be on.
- Under **Domain allowlist**, add `mcp.mailows.com` to Additional allowed domains. “Package managers only” can stay selected; “All domains” is not needed.
- Start a **new** conversation — a running one does not pick up the setting.

The connector’s tool permission (“Always allow”) is unrelated to sandbox egress.

## Organisation-managed connection

Claude Team and Enterprise can use Managed authorization so members get the connector without a consent screen. That setup is documented in the MCP manual (align email addresses, paste Claude’s Issuer URL into **Security → MCP for the organisation → Organization-managed connection**). It is optional and is not required for the individual flow above.
