# Framework wrappers

Thin wrappers that expose the Mailows MCP tools to a LangChain or CrewAI agent. They do not add tools of their own.

Both examples use Streamable HTTP at `https://mcp.mailows.com/mcp` and a short-lived OAuth access token in `MCP_ACCESS_TOKEN`. A portal API key will not work.

Incoming mail is untrusted data. Do not let a framework agent send, forward or change permissions because of text it read with `mail_read_message`. See [guardrails](../docs/guardrails-and-prompt-injection.md).

The [MCP manual](https://www.mailows.com/en/mcp-manual?utm_source=github&utm_medium=repo&utm_campaign=examples) does not document LangChain or CrewAI. The Mailows tool names and the server URL are verified; the framework connection APIs are taken from those projects’ current docs and may change.

## LangChain

`langchain_mailows.py` uses `langchain-mcp-adapters` (`MultiServerMCPClient`), which is what this repository was asked to demonstrate. LangChain also ships an equivalent built-in adapter, `langchain.mcp.MCPAdapter`.

```bash
pip install -r requirements.txt
export MCP_ACCESS_TOKEN='<short-lived OAuth access token>'
python langchain_mailows.py
```

## CrewAI

`crewai_mailows.py` uses `MCPServerAdapter` from `crewai-tools` with `transport: "streamable-http"`. Passing the bearer token in `headers` is the usual pattern; if your `crewai-tools` version rejects that key, check that version’s MCP docs (placeholder).

```bash
python crewai_mailows.py
```
