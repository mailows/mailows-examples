# TypeScript example

Sends one email with one attachment through `https://mcp.mailows.com/mcp`, same contract as the [Python example](../python/).

The [MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples) tells new clients to speak protocol revision `2026-07-28`. In 2026 that lives in the official package `@modelcontextprotocol/client`. The older `@modelcontextprotocol/sdk` 1.x package still talks the 2025 revisions, which Mailows accepts, but should not be used for a new integration.

MCP accepts OAuth access tokens only. A portal API key will not work.

## Install and run

```bash
npm install
export MCP_ACCESS_TOKEN='<short-lived OAuth access token>'
export MAIL_TO='finance@example.com'   # already on the send allowlist
export MAIL_ATTACHMENT='../python/fixtures/hello.txt'
npx tsx src/send-with-attachment.ts
```

The prepare-result field names for the raw upload URL and token are a **placeholder** (see the Python README). The script prints the raw `structuredContent` if it cannot find them.
