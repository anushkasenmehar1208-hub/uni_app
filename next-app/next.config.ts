import type { NextConfig } from "next";

const REFLEX_BACKEND_URL =
  process.env.REFLEX_BACKEND_URL || "https://alexstudies.com";

const nextConfig: NextConfig = {
  // Use standalone output for a much smaller Docker image on Railway.
  output: "standalone",

  // Proxy all paths the existing Reflex app owns so Next.js can sit
  // in front of the same domain without breaking the app, auth, or
  // payment flows. Next.js keeps: /, /login, /register, /onboarding,
  // /api/auth/* (new). Reflex keeps everything else.
  async rewrites() {
    return [
      // Reflex serves the actual app
      {
        source: "/app/:path*",
        destination: `${REFLEX_BACKEND_URL}/app/:path*`,
      },
      // Google OAuth lives on Reflex
      {
        source: "/auth/:path*",
        destination: `${REFLEX_BACKEND_URL}/auth/:path*`,
      },
      // Stripe webhooks live on Reflex
      {
        source: "/stripe/:path*",
        destination: `${REFLEX_BACKEND_URL}/stripe/:path*`,
      },
      // Reflex WebSocket for state hydration
      {
        source: "/_event/:path*",
        destination: `${REFLEX_BACKEND_URL}/_event/:path*`,
      },
      // Reflex serves user-uploaded media
      {
        source: "/_upload/:path*",
        destination: `${REFLEX_BACKEND_URL}/_upload/:path*`,
      },
      // Reflex API endpoints (NOT /api/auth/* — those are Next.js)
      {
        source: "/api/payment/:path*",
        destination: `${REFLEX_BACKEND_URL}/api/payment/:path*`,
      },
      {
        source: "/api/profile/:path*",
        destination: `${REFLEX_BACKEND_URL}/api/profile/:path*`,
      },
    ];
  },
};

export default nextConfig;
