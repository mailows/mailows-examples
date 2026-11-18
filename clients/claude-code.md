# Claude Code

Verified from the [MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples).

```bash
claude mcp add --scope user --transport http mailows https://mcp.mailows.com/mcp
```

The official manual uses the alias `namailu` instead of `mailows`. Either works.

Then:

1. Start the OAuth sign-in from Claude Code.
2. Pick the agent mailboxes and confirm 2FA.
3. Check the tools (`mail_health` is a safe first call). Do not send mail while testing.

The hosted Claude app uses a custom connector instead of this command; see [claude-desktop.md](claude-desktop.md).
