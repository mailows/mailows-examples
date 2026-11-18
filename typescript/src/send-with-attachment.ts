/**
 * Send one email with one attachment through the Mailows MCP server.
 *
 * Requires MCP_ACCESS_TOKEN (OAuth access token for https://mcp.mailows.com).
 * A portal API key will not work.
 */
import { createHash, randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";
import { basename } from "node:path";

import {
  Client,
  StreamableHTTPClientTransport,
  type CallToolResult,
} from "@modelcontextprotocol/client";

const MCP_URL = "https://mcp.mailows.com/mcp";
const CHUNK_SIZE = 8192;

function asObject(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function payload(result: CallToolResult): Record<string, unknown> {
  const data = asObject(result.structuredContent);
  if (result.isError) {
    throw new Error(`Tool returned an error: ${JSON.stringify(data.error ?? data)}`);
  }
  return data;
}

function firstPresent(obj: Record<string, unknown>, keys: string[]): unknown {
  for (const key of keys) {
    const value = obj[key];
    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }
  return undefined;
}

function extractUpload(prepare: Record<string, unknown>): {
  attachmentId: string;
  uploadUrl?: string;
  uploadToken?: string;
  inbandEligible: boolean;
} {
  const candidates: unknown[] = [];
  for (const key of ["files", "attachments", "uploads", "items"]) {
    const value = prepare[key];
    if (Array.isArray(value)) candidates.push(...value);
    else if (value && typeof value === "object") candidates.push(value);
  }
  if (
    candidates.length === 0 &&
    (prepare.attachment_id || prepare.upload_url || prepare.url)
  ) {
    candidates.push(prepare);
  }
  if (candidates.length === 0) {
    throw new Error(
      "Could not find an attachment entry in mail_prepare_attachment_uploads. Raw structuredContent:\n" +
        JSON.stringify(prepare, null, 2),
    );
  }
  const entry = asObject(candidates[0]);
  const attachmentId = String(
    firstPresent(entry, ["attachment_id", "id"]) ?? firstPresent(prepare, ["attachment_id"]) ?? "",
  );
  if (!attachmentId) {
    throw new Error(
      "Prepare result has no attachment_id. Raw structuredContent:\n" +
        JSON.stringify(prepare, null, 2),
    );
  }
  const inband = entry.inband_upload ?? prepare.inband_upload;
  const inbandEligible =
    typeof inband === "boolean"
      ? inband
      : Boolean(asObject(inband).eligible);
  const uploadUrl = firstPresent(entry, ["upload_url", "url", "put_url", "href"]);
  const uploadToken = firstPresent(entry, [
    "upload_token",
    "token",
    "authorization",
    "bearer",
  ]);
  return {
    attachmentId,
    uploadUrl: typeof uploadUrl === "string" ? uploadUrl : undefined,
    uploadToken: typeof uploadToken === "string" ? uploadToken : undefined,
    inbandEligible,
  };
}

async function rawPut(url: string, token: string | undefined, body: Buffer): Promise<void> {
  const headers: Record<string, string> = {
    "Content-Type": "application/octet-stream",
    "Content-Length": String(body.length),
  };
  if (token) {
    headers.Authorization = token.toLowerCase().startsWith("bearer ")
      ? token
      : `Bearer ${token}`;
  }
  const response = await fetch(url, { method: "PUT", headers, body: new Uint8Array(body) });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`PUT ${response.status}: ${text}`);
  }
}

async function uploadInChunks(
  client: Client,
  attachmentId: string,
  body: Buffer,
): Promise<void> {
  let offset = 0;
  while (offset < body.length) {
    const block = body.subarray(offset, offset + CHUNK_SIZE);
    const chunkSha = createHash("sha256").update(block).digest("hex");
    const result = payload(
      await client.callTool({
        name: "mail_upload_attachment_chunk",
        arguments: {
          attachment_id: attachmentId,
          offset,
          content_base64: block.toString("base64"),
          chunk_sha256: chunkSha,
        },
      }),
    );
    if (result.complete === true) return;
    const next = result.next_offset;
    offset = typeof next === "number" && next > offset ? next : offset + block.length;
  }
}

async function main(): Promise<void> {
  const accessToken = process.env.MCP_ACCESS_TOKEN?.trim();
  if (!accessToken) {
    throw new Error("Set MCP_ACCESS_TOKEN to a short-lived OAuth access token.");
  }
  const recipient = process.env.MAIL_TO?.trim();
  if (!recipient) {
    throw new Error("Set MAIL_TO to a recipient already on the send allowlist.");
  }
  const attachmentPath = process.env.MAIL_ATTACHMENT ?? "../python/fixtures/hello.txt";
  const body = await readFile(attachmentPath);
  const digest = createHash("sha256").update(body).digest("hex");
  const idempotencyKey = process.env.MAIL_IDEMPOTENCY_KEY ?? `examples-send-${randomUUID()}`;
  const inboxId = process.env.MAIL_INBOX_ID?.trim();

  const client = new Client(
    { name: "mailows-examples", version: "1.0.0" },
    { versionNegotiation: { mode: { pin: "2026-07-28" } } },
  );
  const transport = new StreamableHTTPClientTransport(new URL(MCP_URL), {
    authProvider: { token: async () => accessToken },
  });
  await client.connect(transport);
  try {
    console.log("mail_health:", JSON.stringify(payload(await client.callTool({ name: "mail_health", arguments: {} })), null, 2));
    console.log(
      "mail_list_inboxes:",
      JSON.stringify(payload(await client.callTool({ name: "mail_list_inboxes", arguments: {} })), null, 2),
    );

    const prepare = payload(
      await client.callTool({
        name: "mail_prepare_attachment_uploads",
        arguments: {
          idempotency_key: idempotencyKey,
          files: [
            {
              filename: basename(attachmentPath),
              content_type: process.env.MAIL_CONTENT_TYPE ?? "text/plain",
              size: body.length,
              sha256: digest,
            },
          ],
        },
      }),
    );
    const upload = extractUpload(prepare);
    console.log(`Prepared attachment_id=${upload.attachmentId}`);

    let uploaded = false;
    if (upload.uploadUrl) {
      try {
        await rawPut(upload.uploadUrl, upload.uploadToken, body);
        uploaded = true;
        console.log("Uploaded with a raw HTTPS PUT.");
      } catch (error) {
        console.log(`Raw PUT failed (${String(error)}).`);
        if (!upload.inbandEligible) throw error;
      }
    }
    if (!uploaded) {
      if (!upload.inbandEligible && !upload.uploadUrl) {
        throw new Error(
          "No upload URL and inband_upload.eligible is not true. Raw structuredContent:\n" +
            JSON.stringify(prepare, null, 2),
        );
      }
      console.log("Uploading over MCP with mail_upload_attachment_chunk.");
      await uploadInChunks(client, upload.attachmentId, body);
    }

    const sendArguments: Record<string, unknown> = {
      to: [recipient],
      subject: process.env.MAIL_SUBJECT ?? "Mailows examples: attachment test",
      text: process.env.MAIL_TEXT ?? "Hello, please find the attached sample file.\n",
      attachment_ids: [upload.attachmentId],
      idempotency_key: idempotencyKey,
    };
    if (inboxId) sendArguments.inbox_id = inboxId;

    const sent = payload(await client.callTool({ name: "mail_send_message", arguments: sendArguments }));
    console.log("mail_send_message:", JSON.stringify(sent, null, 2));
    if (sent.status !== "sent") {
      throw new Error(
        "Expected structuredContent.status == 'sent'. Reuse the same idempotency_key if you retry.",
      );
    }
    if (sent.warnings) {
      console.log("Warnings from the server (unscannable_* is not a clean scan):");
      console.log(JSON.stringify(sent.warnings, null, 2));
    }
  } finally {
    await client.close();
  }
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
