# Codex (CLI, Desktop, IDE)

Verified from the [MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples).

Codex shares this configuration between the CLI, the desktop app and the IDE on the same host.

```bash
codex mcp add mailows --url https://mcp.mailows.com/mcp
```

Or by hand in `~/.codex/config.toml`:

```toml
[mcp_servers.mailows]
url = "https://mcp.mailows.com/mcp"
auth = "oauth"
scopes = ["mcp:mail.read", "mcp:mail.messages.read", "mcp:mail.send"]
oauth_resource = "https://mcp.mailows.com"
```

Then:

1. Save the server into `~/.codex/config.toml` (the `codex mcp add` command does this for you).
2. Run `codex mcp login mailows`.
3. Pick the mailboxes in the browser and confirm 2FA.

The official manual uses the alias `namailu` in the `codex mcp add` example and in the TOML table name. Either alias works; keep the `url`, `auth`, `scopes` and `oauth_resource` values exactly as above.

Check your Codex version’s compatibility matrix before public use, as the manual recommends.
