export const dynamic = "force-dynamic";
export const runtime = "nodejs";
// The pipeline takes ~30–90s of LLM work; lift the default 10s cap.
export const maxDuration = 300;

import { NextRequest, NextResponse } from "next/server";

const REFLEX_BACKEND_URL =
  process.env.REFLEX_BACKEND_URL || "https://backend.alexstudies.com";

// Forward multipart/form-data from the browser to the Python backend's
// /api/exam-forecast endpoint. The browser never talks to OpenRouter
// directly — Python owns the model keys and the pipeline.
export async function POST(req: NextRequest) {
  const upstreamUrl = `${REFLEX_BACKEND_URL}/api/exam-forecast`;

  const headers = new Headers();
  // Preserve Content-Type (with the multipart boundary) and forward
  // auth/cookie context so the Python side can identify the user if
  // we ever choose to gate the endpoint. Strip Host so fetch sets its
  // own.
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const auth = req.headers.get("authorization");
  if (auth) headers.set("authorization", auth);
  const cookie = req.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, {
      method: "POST",
      headers,
      body: req.body,
      // @ts-expect-error: Node fetch supports duplex for streaming bodies
      duplex: "half",
    });
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return NextResponse.json(
      { ok: false, error: `Backend unreachable: ${message}` },
      { status: 502 },
    );
  }

  // Stream the JSON response back unchanged. The Python side already
  // formats success/error payloads, including ok/error fields.
  const respHeaders = new Headers(upstream.headers);
  respHeaders.delete("content-encoding");
  respHeaders.delete("content-length");
  respHeaders.delete("transfer-encoding");

  return new NextResponse(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: respHeaders,
  });
}
