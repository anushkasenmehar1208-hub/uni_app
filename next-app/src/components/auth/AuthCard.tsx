"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface AuthCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function AuthCard({ title, children, footer }: AuthCardProps) {
  return (
    <div
      className="relative min-h-screen w-full overflow-hidden"
      style={{ background: "#000000" }}
    >
      <div
        aria-hidden
        className="fixed pointer-events-none"
        style={{
          top: 0,
          right: "-20vw",
          width: "55vw",
          height: "100vh",
          background:
            "radial-gradient(ellipse at center, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.06) 45%, transparent 75%)",
          filter: "blur(60px)",
          zIndex: 0,
        }}
      />
      <div
        aria-hidden
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(circle, rgba(255,255,255,0.055) 0.75px, transparent 0.95px) 0 0 / 18px 18px",
          opacity: 0.22,
          zIndex: 1,
        }}
      />
      <div
        aria-hidden
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(circle, rgba(255,255,255,0.09) 1px, transparent 1.8px) 0 0 / 22px 22px",
          opacity: 0.55,
          WebkitMaskImage:
            "radial-gradient(circle at 84% 52%, rgba(0,0,0,1) 0%, rgba(0,0,0,0.55) 38%, transparent 70%)",
          maskImage:
            "radial-gradient(circle at 84% 52%, rgba(0,0,0,1) 0%, rgba(0,0,0,0.55) 38%, transparent 70%)",
          zIndex: 2,
        }}
      />

      <div
        className="relative flex flex-col items-center justify-center min-h-screen px-4 py-8"
        style={{ zIndex: 3 }}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="w-full"
          style={{ maxWidth: 430 }}
        >
          <div
            className="relative"
            style={{
              padding: "32px 28px 28px",
              borderRadius: 24,
              background: "#111111",
              border: "1px solid rgba(255,255,255,0.1)",
              boxShadow:
                "0 40px 100px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.04)",
            }}
          >
            <Link
              href="/"
              className="flex items-center justify-center mb-7"
              style={{ textDecoration: "none", gap: 12 }}
            >
              <div
                className="flex items-center justify-center flex-shrink-0"
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 12,
                  background: "#ffffff",
                  boxShadow: "0 4px 16px rgba(255,255,255,0.1)",
                }}
              >
                <span style={{ color: "#000", fontWeight: 800, fontSize: 22 }}>
                  A
                </span>
              </div>
              <div>
                <div
                  style={{
                    color: "#ffffff",
                    fontSize: "1.125rem",
                    fontWeight: 700,
                    fontFamily: "'Space Grotesk', 'Plus Jakarta Sans', sans-serif",
                    lineHeight: 1.2,
                  }}
                >
                  Alex AI
                </div>
                <div
                  style={{
                    color: "rgba(255,255,255,0.5)",
                    fontSize: "0.875rem",
                    lineHeight: 1.3,
                    marginTop: 1,
                  }}
                >
                  {title}
                </div>
              </div>
            </Link>

            {children}

            {footer && (
              <div
                className="text-center"
                style={{
                  marginTop: 20,
                  color: "rgba(255,255,255,0.4)",
                  fontSize: "0.875rem",
                }}
              >
                {footer}
              </div>
            )}
          </div>
        </motion.div>

        <AuthLegalFooter />
      </div>
    </div>
  );
}

function AuthLegalFooter() {
  const linkStyle: React.CSSProperties = {
    color: "rgba(255,255,255,0.35)",
    fontSize: "0.72rem",
    textDecoration: "none",
    whiteSpace: "nowrap",
  };
  const sep = (
    <span style={{ color: "rgba(255,255,255,0.15)", fontSize: "0.72rem" }}>
      ·
    </span>
  );
  return (
    <div className="text-center px-4" style={{ marginTop: 40 }}>
      <div className="flex items-center justify-center flex-wrap gap-3">
        <Link
          href="/return-policy"
          style={linkStyle}
          className="hover:!text-white transition-colors"
        >
          Refund &amp; Cancellation
        </Link>
        {sep}
        <Link
          href="/privacy-policy"
          style={linkStyle}
          className="hover:!text-white transition-colors"
        >
          Privacy Policy
        </Link>
        {sep}
        <Link
          href="/terms"
          style={linkStyle}
          className="hover:!text-white transition-colors"
        >
          Terms
        </Link>
        {sep}
        <Link
          href="/support"
          style={linkStyle}
          className="hover:!text-white transition-colors"
        >
          Support
        </Link>
      </div>
      <p
        style={{
          color: "rgba(255,255,255,0.25)",
          fontSize: "0.7rem",
          marginTop: 10,
          letterSpacing: "0.02em",
        }}
      >
        © {new Date().getFullYear()} Alex AI. All rights reserved.
      </p>
    </div>
  );
}
