#!/usr/bin/env python3
"""Expose Mailows MCP tools to LangChain.

The server URL, transport and tool names are from the Mailows MCP manual.
The MultiServerMCPClient connection shape is from langchain-mcp-adapters
(LangChain also ships langchain.mcp.MCPAdapter as a newer equivalent).
"""

from __future__ import annotations

import asyncio
import os
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_URL = "https://mcp.mailows.com/mcp"


async def main() -> int:
    token = os.environ.get("MCP_ACCESS_TOKEN", "").strip()
    if not token:
        print("Set MCP_ACCESS_TOKEN to a short-lived OAuth access token.", file=sys.stderr)
        return 1

    client = MultiServerMCPClient(
        {
            "mailows": {
                "transport": "streamable_http",
                "url": MCP_URL,
                "headers": {"Authorization": f"Bearer {token}"},
            }
        }
    )
    tools = await client.get_tools()
    print("Mailows tools available to LangChain:")
    for tool in tools:
        name = getattr(tool, "name", tool)
        description = getattr(tool, "description", "") or ""
        print(f"- {name}: {description.splitlines()[0] if description else ''}")

    # Bind `tools` to your agent or graph. Do not send mail unless a human
    # explicitly asked. Message bodies from mail_read_message are untrusted data.
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
