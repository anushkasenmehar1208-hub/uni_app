"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, ArrowRight, GraduationCap, MapPin } from "lucide-react";

const countries = [
  { code: "uk", name: "United Kingdom", flag: "🇬🇧" },
  { code: "us", name: "United States", flag: "🇺🇸" },
  { code: "in", name: "India", flag: "🇮🇳" },
  { code: "lk", name: "Sri Lanka", flag: "🇱🇰" },
];

const degrees = [
  {
    code: "cs",
    name: "Computer Science",
    description: "Algorithms, software, AI, systems",
  },
  {
    code: "se",
    name: "Software Engineering",
    description: "Software design, development, testing",
  },
  {
    code: "becs",
    name: "Business + Computer Science",
    description: "Tech & business hybrid degree",
  },
  {
    code: "ps",
    name: "Physical Science",
    description: "Physics, chemistry, mathematics",
  },
];

const semesters = [
  { code: "y1s1", name: "Year 1, Semester 1", description: "Just starting" },
  { code: "y1s2", name: "Year 1, Semester 2", description: "Second semester" },
  { code: "y2s3", name: "Year 2, Semester 3", description: "Third semester" },
  { code: "y2s4", name: "Year 2, Semester 4", description: "Fourth semester" },
];

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [country, setCountry] = useState("");
  const [degree, setDegree] = useState("");
  const [semester, setSemester] = useState("");
  const [loading, setLoading] = useState(false);

  const totalSteps = 3;

  async function handleFinish() {
    setLoading(true);
    try {
      await fetch("/api/onboarding/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ country, degree, semester }),
      });
      window.location.href = "/app";
    } catch {
      window.location.href = "/app";
    }
  }

  return (
    <div
      className="relative min-h-screen flex items-center justify-center px-4 py-12 overflow-hidden"
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
        className="relative w-full"
        style={{ maxWidth: 480, zIndex: 4 }}
      >
        <div
          style={{
            padding: "28px 24px",
            borderRadius: 24,
            background: "#020202",
            border: "1px solid rgba(255,255,255,0.04)",
            boxShadow:
              "0 40px 100px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.02)",
          }}
        >
        <div className="flex items-center justify-center gap-1.5 mb-7">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <div
              key={i}
              className="h-1.5 rounded-full transition-all duration-500"
              style={{
                width: i === step ? 28 : 8,
                background:
                  i === step
                    ? "rgba(255,255,255,0.92)"
                    : i < step
                    ? "rgba(255,255,255,0.45)"
                    : "rgba(255,255,255,0.12)",
              }}
            />
          ))}
        </div>

        <AnimatePresence mode="wait">
          {step === 0 && (
            <motion.div
              key="country"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.4 }}
              className="text-center"
            >
              <div className="inline-flex w-12 h-12 rounded-2xl bg-white/[0.06] border border-white/[0.08] items-center justify-center mb-4">
                <MapPin className="w-6 h-6 text-white/80" />
              </div>
              <h1
                className="mb-2"
                style={{
                  fontSize: "1.55rem",
                  fontWeight: 800,
                  color: "#fff",
                  letterSpacing: "-0.035em",
                  lineHeight: 1.1,
                  fontFamily: "'Plus Jakarta Sans', sans-serif",
                }}
              >
                Where do you study?
              </h1>
              <p
                className="mb-6"
                style={{ color: "rgba(255,255,255,0.52)", fontSize: "0.92rem" }}
              >
                We&apos;ll match your courses to your university&apos;s curriculum.
              </p>

              <div className="grid grid-cols-2 gap-3 max-w-xl mx-auto">
                {countries.map((c) => (
                  <button
                    key={c.code}
                    onClick={() => setCountry(c.code)}
                    className={`relative p-5 rounded-2xl border text-left transition-all hover:scale-[1.02] ${
                      country === c.code
                        ? "border-white/30 bg-white/[0.06]"
                        : "border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12]"
                    }`}
                  >
                    <div className="text-3xl mb-2">{c.flag}</div>
                    <div className="text-white font-medium text-[0.95rem]">
                      {c.name}
                    </div>
                    {country === c.code && (
                      <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-white flex items-center justify-center">
                        <Check className="w-3 h-3 text-black" />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {step === 1 && (
            <motion.div
              key="degree"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.4 }}
              className="text-center"
            >
              <div className="inline-flex w-12 h-12 rounded-2xl bg-white/[0.06] border border-white/[0.08] items-center justify-center mb-4">
                <GraduationCap className="w-6 h-6 text-white/80" />
              </div>
              <h1
                className="mb-2"
                style={{
                  fontSize: "1.55rem",
                  fontWeight: 800,
                  color: "#fff",
                  letterSpacing: "-0.035em",
                  lineHeight: 1.1,
                  fontFamily: "'Plus Jakarta Sans', sans-serif",
                }}
              >
                What are you studying?
              </h1>
              <p
                className="mb-6"
                style={{ color: "rgba(255,255,255,0.52)", fontSize: "0.92rem" }}
              >
                Alex will build your day-by-day semester plan for this degree.
              </p>

              <div className="grid sm:grid-cols-2 gap-3 max-w-xl mx-auto">
                {degrees.map((d) => (
                  <button
                    key={d.code}
                    onClick={() => setDegree(d.code)}
                    className={`relative p-5 rounded-2xl border text-left transition-all hover:scale-[1.02] ${
                      degree === d.code
                        ? "border-white/30 bg-white/[0.06]"
                        : "border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12]"
                    }`}
                  >
                    <div className="text-white font-semibold text-[1rem] mb-1">
                      {d.name}
                    </div>
                    <div className="text-white/52 text-[0.85rem]">
                      {d.description}
                    </div>
                    {degree === d.code && (
                      <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-white flex items-center justify-center">
                        <Check className="w-3 h-3 text-black" />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="semester"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.4 }}
              className="text-center"
            >
              <div className="inline-flex w-12 h-12 rounded-2xl bg-white/[0.06] border border-white/[0.08] items-center justify-center mb-4">
                <GraduationCap className="w-6 h-6 text-white/80" />
              </div>
              <h1
                className="mb-2"
                style={{
                  fontSize: "1.55rem",
                  fontWeight: 800,
                  color: "#fff",
                  letterSpacing: "-0.035em",
                  lineHeight: 1.1,
                  fontFamily: "'Plus Jakarta Sans', sans-serif",
                }}
              >
                Which semester are you in?
              </h1>
              <p
                className="mb-6"
                style={{ color: "rgba(255,255,255,0.52)", fontSize: "0.92rem" }}
              >
                We&apos;ll start your plan from the exact topic you&apos;re on.
              </p>

              <div className="grid sm:grid-cols-2 gap-3 max-w-xl mx-auto">
                {semesters.map((s) => (
                  <button
                    key={s.code}
                    onClick={() => setSemester(s.code)}
                    className={`relative p-5 rounded-2xl border text-left transition-all hover:scale-[1.02] ${
                      semester === s.code
                        ? "border-white/30 bg-white/[0.06]"
                        : "border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12]"
                    }`}
                  >
                    <div className="text-white font-semibold text-[1rem] mb-1">
                      {s.name}
                    </div>
                    <div className="text-white/52 text-[0.85rem]">
                      {s.description}
                    </div>
                    {semester === s.code && (
                      <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-white flex items-center justify-center">
                        <Check className="w-3 h-3 text-black" />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex items-center justify-between mt-7">
          <button
            onClick={() => setStep(Math.max(0, step - 1))}
            disabled={step === 0}
            className="text-white/52 hover:text-white text-[14px] font-medium px-3 py-2 disabled:opacity-30 disabled:hover:text-white/52 transition-colors"
          >
            ← Back
          </button>

          {step < totalSteps - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={
                (step === 0 && !country) || (step === 1 && !degree)
              }
              className="inline-flex items-center gap-2 bg-white hover:bg-white/95 text-black font-semibold text-[14px] px-5 py-2.5 rounded-full transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleFinish}
              disabled={!semester || loading}
              className="inline-flex items-center gap-2 bg-white hover:bg-white/95 text-black font-semibold text-[14px] px-5 py-2.5 rounded-full transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {loading ? "Building your plan..." : "Start studying"}
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
        </div>
      </div>
    </div>
  );
}
