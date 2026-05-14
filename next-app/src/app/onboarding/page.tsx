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
    <div className="relative min-h-screen flex items-center justify-center px-4 py-12 bg-[#0a0a0c] overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute top-1/4 right-0 w-[50vw] h-[80vh] blur-[100px] opacity-40"
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(255,255,255,0.12) 0%, transparent 70%)",
          }}
        />
      </div>

      <div className="relative w-full max-w-2xl">
        {/* Progress indicator */}
        <div className="flex items-center justify-center gap-2 mb-10">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <div
              key={i}
              className={`h-1 rounded-full transition-all duration-500 ${
                i < step
                  ? "w-8 bg-white"
                  : i === step
                  ? "w-12 bg-white"
                  : "w-8 bg-white/10"
              }`}
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
              <div className="inline-flex w-14 h-14 rounded-2xl bg-white/[0.06] border border-white/[0.08] items-center justify-center mb-6">
                <MapPin className="w-6 h-6 text-white/80" />
              </div>
              <h1 className="text-[2rem] font-medium text-white mb-2 tracking-tight">
                Where do you study?
              </h1>
              <p className="text-white/52 mb-10">
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
              <div className="inline-flex w-14 h-14 rounded-2xl bg-white/[0.06] border border-white/[0.08] items-center justify-center mb-6">
                <GraduationCap className="w-6 h-6 text-white/80" />
              </div>
              <h1 className="text-[2rem] font-medium text-white mb-2 tracking-tight">
                What are you studying?
              </h1>
              <p className="text-white/52 mb-10">
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
              <div className="inline-flex w-14 h-14 rounded-2xl bg-white/[0.06] border border-white/[0.08] items-center justify-center mb-6">
                <GraduationCap className="w-6 h-6 text-white/80" />
              </div>
              <h1 className="text-[2rem] font-medium text-white mb-2 tracking-tight">
                Which semester are you in?
              </h1>
              <p className="text-white/52 mb-10">
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

        {/* Navigation */}
        <div className="flex items-center justify-between mt-10 max-w-xl mx-auto">
          <button
            onClick={() => setStep(Math.max(0, step - 1))}
            disabled={step === 0}
            className="text-white/52 hover:text-white text-[14.5px] font-medium px-4 py-2.5 disabled:opacity-30 disabled:hover:text-white/52 transition-colors"
          >
            ← Back
          </button>

          {step < totalSteps - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={
                (step === 0 && !country) || (step === 1 && !degree)
              }
              className="inline-flex items-center gap-2 bg-white hover:bg-white/95 text-black font-semibold text-[14.5px] px-6 py-3 rounded-full transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleFinish}
              disabled={!semester || loading}
              className="inline-flex items-center gap-2 bg-white hover:bg-white/95 text-black font-semibold text-[14.5px] px-6 py-3 rounded-full transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {loading ? "Building your plan..." : "Start studying"}
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
