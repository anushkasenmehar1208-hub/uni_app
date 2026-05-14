"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

export function Hero() {
  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-32 overflow-hidden">
      {/* Edge glow */}
      <div className="absolute top-0 right-0 w-[55vw] h-[100vh] pointer-events-none">
        <div
          className="absolute inset-0 blur-[80px] opacity-60"
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.05) 40%, transparent 70%)",
          }}
        />
      </div>

      {/* Dot grid background */}
      <div
        className="absolute inset-0 opacity-30 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle, rgba(255,255,255,0.08) 1px, transparent 1.5px)",
          backgroundSize: "22px 22px",
          maskImage:
            "radial-gradient(circle at 70% 50%, black 0%, black 30%, transparent 80%)",
          WebkitMaskImage:
            "radial-gradient(circle at 70% 50%, black 0%, black 30%, transparent 80%)",
        }}
      />

      <div className="relative max-w-6xl mx-auto px-6 text-center">
        {/* Eyebrow badge */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/[0.08] bg-white/[0.03] mb-8"
        >
          <Sparkles className="w-3.5 h-3.5 text-white/74" />
          <span className="text-[0.78rem] font-bold tracking-[0.18em] text-white/74 uppercase">
            Alex AI, Your Academic Mentor
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-[clamp(2.4rem,6.5vw,4.2rem)] font-medium leading-[1.04] tracking-[-0.058em] gradient-text mb-6"
          style={{
            fontFamily:
              "'Plus Jakarta Sans', 'Space Grotesk', sans-serif",
          }}
        >
          AI that teaches your full
          <br />
          university semester day by day
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.25 }}
          className="text-[1.06rem] leading-relaxed text-white/48 max-w-2xl mx-auto mb-10"
        >
          Choose your degree, get a real semester plan, and let Alex teach,
          quiz, track tasks, and help you study every day.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8"
        >
          <Link
            href="/register"
            className="group relative inline-flex items-center justify-center gap-2 bg-white text-black font-semibold text-[15px] px-7 py-3.5 rounded-full hover:scale-[1.03] transition-all duration-200 shadow-[0_0_40px_rgba(255,255,255,0.15)] hover:shadow-[0_0_60px_rgba(255,255,255,0.25)]"
          >
            Start My Study Plan
            <span className="transition-transform group-hover:translate-x-0.5">
              →
            </span>
          </Link>
          <Link
            href="#how-it-works"
            className="text-white/74 hover:text-white text-[15px] font-medium px-4 py-3.5 transition-colors"
          >
            See how it works
          </Link>
        </motion.div>

        {/* Proof chip */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-white/[0.06] bg-white/[0.02]"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
          </span>
          <span className="text-[13px] text-white/64">
            Now in early access — be one of our first 500 students
          </span>
        </motion.div>

        {/* Hero demo preview (placeholder for now, will add image) */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.8 }}
          className="relative mt-20 max-w-5xl mx-auto"
        >
          <div className="relative rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-white/[0.01] p-2 shadow-[0_30px_80px_rgba(0,0,0,0.5)]">
            <div className="aspect-[16/9] rounded-xl bg-gradient-to-br from-white/[0.04] to-black/40 flex items-center justify-center overflow-hidden">
              <div className="text-white/30 text-sm">Demo screenshot here</div>
            </div>
          </div>
          {/* Glow under preview */}
          <div className="absolute -inset-x-10 -bottom-10 h-40 bg-gradient-to-t from-emerald-500/10 to-transparent blur-3xl pointer-events-none" />
        </motion.div>
      </div>
    </section>
  );
}
