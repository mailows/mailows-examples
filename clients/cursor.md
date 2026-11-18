# Cursor

Verified from the [MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples).

Add the server to `~/.cursor/mcp.json` (the whole account) or to `.cursor/mcp.json` in a project. Cursor opens OAuth in the browser the first time a tool is used.

```json
{
  "mcpServers": {
    "mailows": {
      "url": "https://mcp.mailows.com/mcp"
    }
  }
}
```

A copy of this snippet is in [cursor/mcp.json](cursor/mcp.json).

1. Save the file and open **Settings → MCP**.
2. Click sign-in on the Mailows server.
3. Pick the mailboxes and confirm 2FA.

Use the key `url`. Some other clients (for example Antigravity) use `serverUrl` instead — mixing the two up is a common reason a client silently fails to connect. Cursor wants `url`.
