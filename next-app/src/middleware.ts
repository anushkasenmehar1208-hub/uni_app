import { NextRequest, NextResponse } from "next/server";

const REFLEX_BACKEND_URL =
  process.env.REFLEX_BACKEND_URL || "https://backend.alexstudies.com";

const REFLEX_PATHS = [
  "/app",
  "/auth",
  "/stripe",
  "/_event",
  "/_upload",
  "/api/payment",
  "/api/profile",
];

function isReflexPath(pathname: string): boolean {
  return REFLEX_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
}

export async function middleware(req: NextRequest) {
  const { pathname, search } = req.nextUrl;

  if (!isReflexPath(pathname)) {
    return NextResponse.next();
  }

  // Reflex always expects /app/ (trailing slash). Map bare /app to /app/
  // before forwarding so we never hit Reflex's HTTPS-downgrading 307.
  let upstreamPath = pathname;
  if (pathname === "/app") {
    upstreamPath = "/app/";
  }

  const upstream = `${REFLEX_BACKEND_URL}${upstreamPath}${search}`;

  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("content-length");

  const upstreamRes = await fetch(upstream, {
    method: req.method,
    headers,
    body:
      req.method === "GET" || req.method === "HEAD" ? undefined : req.body,
    redirect: "manual",
    // @ts-expect-error: Node fetch supports duplex for streaming
    duplex: "half",
  });

  const resHeaders = new Headers(upstreamRes.headers);
  resHeaders.delete("content-encoding");
  resHeaders.delete("content-length");
  resHeaders.delete("transfer-encoding");

  return new NextResponse(upstreamRes.body, {
    status: upstreamRes.status,
    statusText: upstreamRes.statusText,
    headers: resHeaders,
  });
}

export const config = {
  matcher: [
    "/app",
    "/app/:path*",
    "/auth/:path*",
    "/stripe/:path*",
    "/_event/:path*",
    "/_upload/:path*",
    "/api/payment/:path*",
    "/api/profile/:path*",
  ],
};
