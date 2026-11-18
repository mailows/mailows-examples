#!/usr/bin/env python3
"""Send one email with one attachment through the Mailows MCP server.

Requires MCP_ACCESS_TOKEN (OAuth access token for https://mcp.mailows.com).
A portal API key will not work.

The prepare-result field names for the raw upload URL and token are not
fully spelled out in the MCP manual (it shows $UPLOAD_URL / $UPLOAD_TOKEN).
This script tries a short list of obvious keys and prints the raw tool
payload if it cannot find them.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

MCP_URL = "https://mcp.mailows.com/mcp"
CHUNK_SIZE = 8192  # original bytes, as documented for mail_upload_attachment_chunk


def _payload(result: Any) -> dict[str, Any]:
    """Prefer structured_content; fall back to a parsed text block."""
    is_error = bool(getattr(result, "is_error", None) or getattr(result, "isError", False))
    data = getattr(result, "structured_content", None)
    if data is None:
        data = getattr(result, "structuredContent", None)
    if data is None:
        content = getattr(result, "content", None) or []
        texts: list[str] = []
        for block in content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                texts.append(text)
            elif isinstance(block, dict) and "text" in block:
                texts.append(str(block["text"]))
        joined = "\n".join(texts).strip()
        if joined:
            try:
                data = json.loads(joined)
            except json.JSONDecodeError:
                data = {"text": joined}
        else:
            data = {}
    if not isinstance(data, dict):
        data = {"value": data}
    if is_error:
        error = data.get("error") or data
        raise RuntimeError(f"Tool returned an error: {error!r}")
    return data


async def call(client: Client, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    result = await client.call_tool(name, arguments or {})
    return _payload(result)


def _first_present(obj: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return obj[key]
    return None


def _extract_upload(prepare: dict[str, Any]) -> dict[str, Any]:
    """Best-effort mapping of the prepare result.

    Documented: attachment_id, inband_upload.eligible, and (in the curl
    example) an upload URL plus a bearer token for a raw PUT.
    """
    candidates: list[Any] = []
    for key in ("files", "attachments", "uploads", "items"):
        value = prepare.get(key)
        if isinstance(value, list):
            candidates.extend(value)
        elif isinstance(value, dict):
            candidates.append(value)
    if not candidates and ("attachment_id" in prepare or "upload_url" in prepare or "url" in prepare):
        candidates.append(prepare)

    if not candidates:
        raise RuntimeError(
            "Could not find an attachment entry in mail_prepare_attachment_uploads. "
            "Raw structuredContent follows so you can map the fields:\n"
            + json.dumps(prepare, indent=2)
        )

    entry = candidates[0]
    if not isinstance(entry, dict):
        raise RuntimeError(f"Unexpected prepare entry: {entry!r}")

    attachment_id = _first_present(entry, "attachment_id", "id") or _first_present(
        prepare, "attachment_id"
    )
    upload_url = _first_present(entry, "upload_url", "url", "put_url", "href")
    upload_token = _first_present(entry, "upload_token", "token", "authorization", "bearer")
    inband = entry.get("inband_upload") or prepare.get("inband_upload") or {}
    eligible = False
    if isinstance(inband, dict):
        eligible = bool(inband.get("eligible"))
    elif isinstance(inband, bool):
        eligible = inband

    if not attachment_id:
        raise RuntimeError(
            "Prepare result has no attachment_id. Raw structuredContent:\n"
            + json.dumps(prepare, indent=2)
        )
    return {
        "attachment_id": attachment_id,
        "upload_url": upload_url,
        "upload_token": upload_token,
        "inband_eligible": eligible,
        "raw": prepare,
    }


async def _put_bytes(url: str, token: str | None, body: bytes) -> None:
    headers = {"Content-Type": "application/octet-stream", "Content-Length": str(len(body))}
    if token:
        bearer = token if str(token).lower().startswith("bearer ") else f"Bearer {token}"
        headers["Authorization"] = bearer
    async with httpx2.AsyncClient(timeout=httpx2.Timeout(30.0, read=300.0)) as http:
        response = await http.put(url, headers=headers, content=body)
        response.raise_for_status()


async def _upload_in_chunks(client: Client, attachment_id: str, body: bytes) -> None:
    offset = 0
    while offset < len(body):
        block = body[offset : offset + CHUNK_SIZE]
        chunk_sha = hashlib.sha256(block).hexdigest()
        result = await call(
            client,
            "mail_upload_attachment_chunk",
            {
                "attachment_id": attachment_id,
                "offset": offset,
                "content_base64": base64.b64encode(block).decode("ascii"),
                "chunk_sha256": chunk_sha,
            },
        )
        if result.get("complete") is True:
            return
        next_offset = result.get("next_offset")
        if isinstance(next_offset, int) and next_offset > offset:
            offset = next_offset
        else:
            offset += len(block)
    # Final call may already have set complete; if not, one empty finish is not documented,
    # so we stop once the original bytes are consumed.


async def main() -> int:
    token = os.environ.get("MCP_ACCESS_TOKEN", "").strip()
    if not token:
        print("Set MCP_ACCESS_TOKEN to a short-lived OAuth access token.", file=sys.stderr)
        return 1

    recipient = os.environ.get("MAIL_TO", "").strip()
    if not recipient:
        print("Set MAIL_TO to a recipient already on the send allowlist.", file=sys.stderr)
        return 1

    attachment_path = Path(os.environ.get("MAIL_ATTACHMENT", "fixtures/hello.txt"))
    if not attachment_path.is_file():
        print(f"Attachment not found: {attachment_path}", file=sys.stderr)
        return 1

    body = attachment_path.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    # Derive the key from this run. In production, derive it from a business event
    # (for example invoice-2026-0042) and reuse it on retries.
    idempotency_key = os.environ.get("MAIL_IDEMPOTENCY_KEY") or f"examples-send-{uuid.uuid4()}"
    inbox_id = os.environ.get("MAIL_INBOX_ID", "").strip() or None
    subject = os.environ.get("MAIL_SUBJECT", "Mailows examples: attachment test")
    text = os.environ.get(
        "MAIL_TEXT",
        "Hello, please find the attached sample file.\n",
    )

    send_arguments: dict[str, Any] = {
        "to": [recipient],
        "subject": subject,
        "text": text,
        "idempotency_key": idempotency_key,
    }
    if inbox_id:
        send_arguments["inbox_id"] = inbox_id

    async with httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx2.Timeout(30.0, read=300.0),
    ) as http_client:
        transport = streamable_http_client(MCP_URL, http_client=http_client)
        async with Client(transport) as client:
            health = await call(client, "mail_health")
            print("mail_health:", json.dumps(health, indent=2))

            inboxes = await call(client, "mail_list_inboxes")
            print("mail_list_inboxes:", json.dumps(inboxes, indent=2))

            prepare_args: dict[str, Any] = {
                "idempotency_key": idempotency_key,
                "files": [
                    {
                        "filename": attachment_path.name,
                        "content_type": os.environ.get("MAIL_CONTENT_TYPE", "text/plain"),
                        "size": len(body),
                        "sha256": digest,
                    }
                ],
            }
            prepare = await call(client, "mail_prepare_attachment_uploads", prepare_args)
            upload = _extract_upload(prepare)
            attachment_id = upload["attachment_id"]
            print(f"Prepared attachment_id={attachment_id}")

            uploaded = False
            if upload["upload_url"]:
                try:
                    await _put_bytes(upload["upload_url"], upload["upload_token"], body)
                    uploaded = True
                    print("Uploaded with a raw HTTPS PUT.")
                except Exception as exc:  # noqa: BLE001 — fall back if the sandbox blocks egress
                    print(f"Raw PUT failed ({exc!r}).")
                    if not upload["inband_eligible"]:
                        print(
                            "inband_upload.eligible is not true, so the chunk fallback "
                            "is not offered for this set.",
                            file=sys.stderr,
                        )
                        raise
            if not uploaded:
                if not upload["inband_eligible"] and not upload["upload_url"]:
                    print(
                        "No upload URL and inband_upload.eligible is not true. "
                        "Raw structuredContent:\n" + json.dumps(prepare, indent=2),
                        file=sys.stderr,
                    )
                    return 1
                print("Uploading over MCP with mail_upload_attachment_chunk.")
                await _upload_in_chunks(client, attachment_id, body)

            send_arguments["attachment_ids"] = [attachment_id]
            sent = await call(client, "mail_send_message", send_arguments)
            status = sent.get("status")
            print("mail_send_message:", json.dumps(sent, indent=2))
            if status != "sent":
                print(
                    "Expected structuredContent.status == 'sent'. "
                    "Inspect the payload above before retrying; reuse the same idempotency_key.",
                    file=sys.stderr,
                )
                return 1
            warnings = sent.get("warnings")
            if warnings:
                print("Warnings from the server (unscannable_* is not a clean scan):")
                print(json.dumps(warnings, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
