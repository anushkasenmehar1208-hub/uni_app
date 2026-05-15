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
  "/api/onboarding/",
  "/_next/",
];

function isNextPath(pathname: string): boolean {
  if (NEXT_PATHS.includes(pathname)) return true;
  return NEXT_PREFIXES.some((p) => pathname.startsWith(p));
}

export async function middleware(req: NextRequest) {
  const { pathname, search, origin } = req.nextUrl;

  // After Next.js /onboarding redirects here with ?onboarded=1, look up
  // the user's saved scope via our status endpoint and redirect to the
  // workspace route server-side. This bypasses Reflex's race condition
  // where rx.LocalStorage hasn't synced when on_load fires — by the time
  // we redirect, the URL is final and the auth token loads cleanly.
  if (pathname === "/app" && req.nextUrl.searchParams.has("onboarded")) {
    const cookie = req.cookies.get("_auth_token")?.value;
    if (cookie) {
      try {
        const statusRes = await fetch(`${origin}/api/onboarding/status`, {
          headers: { Authorization: `Bearer ${cookie}` },
        });
        if (statusRes.ok) {
          const data = (await statusRes.json()) as {
            memory?: {
              is_started?: boolean;
              selected_year?: string;
              selected_semester?: string;
            };
          };
          const m = data.memory;
          if (m?.is_started && m.selected_year && m.selected_semester) {
            const y = m.selected_year.match(/\d+/)?.[0];
            const s = m.selected_semester.match(/\d+/)?.[0];
            if (y && s) {
              return NextResponse.redirect(
                new URL(`/s/y${y}s${s}`, origin)
              );
            }
          }
        }
      } catch {
        // Fall through to normal proxy if the lookup fails.
      }
    }
  }

  if (isNextPath(pathname)) {
    return NextResponse.next();
  }

  // Reflex page routes all want a trailing slash; without one the
  // backend 307s to add it, which combined with Next.js's default
  // trailingSlash:false strip becomes an infinite loop. Static assets
  // (anything with a file extension) keep their literal path.
  const hasExtension = /\.[a-zA-Z0-9]+$/.test(pathname);
  const upstreamPath =
    !hasExtension && !pathname.endsWith("/") ? `${pathname}/` : pathname;
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

  // Reflex generates Location headers using the request Host, which is
  // backend.alexstudies.com under our proxy. Rewrite to the original
  // request origin so redirects stay on alexstudies.com. Edge runtime
  // rejects relative Locations, so we keep the URL absolute.
  const loc = resHeaders.get("location");
  if (loc) {
    const requestOrigin = req.nextUrl.origin;
    const rewritten = loc.replace(
      /^https?:\/\/backend\.alexstudies\.com/i,
      requestOrigin
    );
    if (rewritten !== loc) resHeaders.set("location", rewritten);
  }

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
