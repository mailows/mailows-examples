# Client setup

Paste only the MCP server address into the client. Credentials stay with Mailows. Sign-in opens `https://id.namailu.cz`; you never paste a password or a portal API key into the client.

The official [MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples) uses `namailu` as a local server alias. In this repository we use `mailows`. Either name is fine — it is only a label in your config. The URL has to be exactly:

```
https://mcp.mailows.com/mcp
```

Transport is Streamable HTTP. Authentication is OAuth 2.1 with PKCE. Typical scopes:

```
mcp:mail.read mcp:mail.messages.read mcp:mail.send
```

Do not use an “API key” or “Bearer token” mode, and do not add a custom HTTP header, in these hosted or desktop clients. A static portal API key is for the REST API at `https://api.mailows.com` and is refused by MCP.

| Client | File |
| --- | --- |
| Claude app / Desktop | [claude-desktop.md](claude-desktop.md) |
| Claude Code | [claude-code.md](claude-code.md) |
| Cursor | [cursor.md](cursor.md) |
| ChatGPT | [chatgpt.md](chatgpt.md) |
| Codex (CLI, Desktop, IDE) | [codex.md](codex.md) |

The manual also documents Gemini CLI, Antigravity, Hermes and OpenClaw. Those are omitted here; the same URL and OAuth flow apply.
