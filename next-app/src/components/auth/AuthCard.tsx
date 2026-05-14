"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface AuthCardProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}

export function AuthCard({ title, subtitle, children, footer }: AuthCardProps) {
  return (
    <div className="relative min-h-screen flex items-center justify-center px-4 py-12 bg-[#0a0a0c] overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute top-1/4 right-0 w-[50vw] h-[80vh] blur-[100px] opacity-50"
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(255,255,255,0.12) 0%, transparent 70%)",
          }}
        />
        <div
          className="absolute inset-0 opacity-25"
          style={{
            backgroundImage:
              "radial-gradient(circle, rgba(255,255,255,0.05) 1px, transparent 1.5px)",
            backgroundSize: "20px 20px",
            maskImage:
              "radial-gradient(circle at 50% 50%, black 0%, transparent 70%)",
            WebkitMaskImage:
              "radial-gradient(circle at 50% 50%, black 0%, transparent 70%)",
          }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="relative w-full max-w-[440px]"
      >
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2.5 justify-center mb-8"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-white to-white/70 flex items-center justify-center shadow-[0_8px_30px_rgba(255,255,255,0.15)]">
            <span className="text-black font-bold text-base">A</span>
          </div>
          <span className="text-white font-semibold text-[17px] tracking-tight">
            Alex AI
          </span>
        </Link>

        {/* Card */}
        <div className="relative rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.03] to-white/[0.01] backdrop-blur-xl p-7 md:p-9 shadow-[0_30px_80px_rgba(0,0,0,0.4)]">
          <div className="mb-7 text-center">
            <h1 className="text-[1.7rem] font-medium text-white mb-1.5 tracking-tight">
              {title}
            </h1>
            <p className="text-white/52 text-[0.95rem]">{subtitle}</p>
          </div>

          {children}
        </div>

        <div className="mt-6 text-center text-white/52 text-[0.92rem]">
          {footer}
        </div>
      </motion.div>
    </div>
  );
}
