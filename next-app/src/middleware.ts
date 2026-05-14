import { NextRequest, NextResponse } from "next/server";

const REFLEX_BACKEND_URL =
  process.env.REFLEX_BACKEND_URL || "https://backend.alexstudies.com";

// Paths owned by Next.js — everything else proxies to Reflex.
const NEXT_PATHS = [
  "/",
  "/login",
  "/register",
  "/onboarding",
];

const NEXT_PREFIXES = [
  "/api/auth/",
  "/_next/",
];

function isNextPath(pathname: string): boolean {
  if (NEXT_PATHS.includes(pathname)) return true;
  return NEXT_PREFIXES.some((p) => pathname.startsWith(p));
}

export async function middleware(req: NextRequest) {
  const { pathname, search } = req.nextUrl;

  if (isNextPath(pathname)) {
    return NextResponse.next();
  }

  // Reflex always expects /app/ (trailing slash) — mapping bare /app
  // here avoids Reflex's HTTPS-downgrading 307.
  const upstreamPath = pathname === "/app" ? "/app/" : pathname;
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
  // Run on all paths except Next.js static asset internals. The
  // middleware itself decides whether to proxy or pass through.
  matcher: [
    "/((?!_next/static|_next/image|favicon\\.ico).*)",
  ],
};
