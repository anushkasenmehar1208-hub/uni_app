"use client";

import { type ReactNode, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Check, GraduationCap, MapPin } from "lucide-react";

type Country = {
  code: string;
  name: string;
  flag: string;
};

type Degree = {
  code: string;
  name: string;
  description: string;
  countries: string[];
};

type Semester = {
  code: string;
  name: string;
  description: string;
};

const countries: Country[] = [
  { code: "uk", name: "United Kingdom", flag: "🇬🇧" },
  { code: "us", name: "United States", flag: "🇺🇸" },
  { code: "in", name: "India", flag: "🇮🇳" },
  { code: "lk", name: "Sri Lanka", flag: "🇱🇰" },
];

const degrees: Degree[] = [
  {
    code: "cs",
    name: "Computer Science",
    description: "Algorithms, software, AI, systems",
    countries: ["uk", "us"],
  },
  {
    code: "se",
    name: "Software Engineering",
    description: "Software design, development, testing",
    countries: ["uk", "us", "lk"],
  },
  {
    code: "becs",
    name: "Business + Computer Science",
    description: "Tech and business hybrid degree",
    countries: ["lk"],
  },
  {
    code: "ps",
    name: "Physical Science",
    description: "Physics, chemistry, mathematics",
    countries: ["lk"],
  },
  {
    code: "btech-cs",
    name: "B.Tech Computer Science",
    description: "Programming, systems, AI, data structures",
    countries: ["in"],
  },
  {
    code: "btech-it",
    name: "B.Tech Information Technology",
    description: "Databases, networks, web, software systems",
    countries: ["in"],
  },
];

const semesters: Semester[] = [
  { code: "y1s1", name: "Year 1 Semester 1", description: "Just starting" },
  { code: "y1s2", name: "Year 1 Semester 2", description: "Second semester" },
  { code: "y2s3", name: "Year 2 Semester 3", description: "Third semester" },
  { code: "y2s4", name: "Year 2 Semester 4", description: "Fourth semester" },
];

const reveal = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
  transition: { duration: 0.25, ease: "easeOut" as const },
};

function OptionCard({
  title,
  description,
  eyebrow,
  selected,
  onClick,
}: {
  title: string;
  description?: string;
  eyebrow?: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className="relative min-h-[46px] w-full rounded-[11px] border px-3 py-2 text-left transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/55"
      style={{
        borderColor: selected
          ? "rgba(134,239,172,0.42)"
          : "rgba(255,255,255,0.07)",
        background: selected
          ? "linear-gradient(180deg, rgba(25,40,31,0.9) 0%, rgba(12,18,15,0.94) 100%)"
          : "rgba(255,255,255,0.025)",
      }}
    >
      <div className="flex items-center gap-2">
        <span
          className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full"
          style={{
            background: selected ? "rgba(255,255,255,0.92)" : "transparent",
            border: selected ? "0" : "1.5px solid rgba(255,255,255,0.2)",
          }}
        >
          {selected && <Check className="h-3 w-3 text-black" />}
        </span>
        {eyebrow && <span className="text-[1.05rem] leading-none">{eyebrow}</span>}
        <span className="min-w-0">
          <span
            className="block text-[0.84rem] leading-tight"
            style={{
              color: selected ? "#fff" : "rgba(220,230,240,0.82)",
              fontWeight: selected ? 700 : 500,
            }}
          >
            {title}
          </span>
          {description && (
            <span className="mt-0.5 block text-[0.74rem] leading-snug text-white/45">
              {description}
            </span>
          )}
        </span>
      </div>
    </button>
  );
}

function Section({
  icon,
  title,
  helper,
  children,
}: {
  icon?: ReactNode;
  title: string;
  helper: string;
  children: ReactNode;
}) {
  return (
    <motion.section {...reveal} className="border-t border-white/[0.06] pt-4 first:border-t-0 first:pt-0">
      <div className="mb-3 flex items-start gap-2.5">
        {icon && (
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.05]">
            {icon}
          </div>
        )}
        <div>
          <h2
            className="text-[1rem] font-extrabold leading-tight text-white"
            style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
          >
            {title}
          </h2>
          <p className="mt-1 text-[0.78rem] leading-snug text-white/55">{helper}</p>
        </div>
      </div>
      {children}
    </motion.section>
  );
}

export default function OnboardingPage() {
  const [country, setCountry] = useState("");
  const [degree, setDegree] = useState("");
  const [semester, setSemester] = useState("");
  const [loading, setLoading] = useState(false);

  const visibleDegrees = useMemo(
    () => degrees.filter((item) => item.countries.includes(country)),
    [country],
  );
  const canFinish = Boolean(country && degree && semester && !loading);

  function chooseCountry(nextCountry: string) {
    setCountry(nextCountry);
    setDegree("");
    setSemester("");
  }

  function chooseDegree(nextDegree: string) {
    setDegree(nextDegree);
    setSemester("");
  }

  async function handleFinish() {
    if (!canFinish) return;
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
      className="relative flex h-dvh min-h-screen items-center justify-center overflow-hidden px-4 py-5"
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

      <main className="relative z-[4] w-full max-w-[420px]">
        <div
          className="max-h-[calc(100dvh-40px)] overflow-y-auto overflow-x-hidden rounded-3xl px-5 py-6 sm:px-6"
          style={{
            background: "#020202",
            border: "1px solid rgba(255,255,255,0.04)",
            boxShadow:
              "0 40px 100px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.02)",
            scrollbarWidth: "thin",
            scrollbarColor: "rgba(255,255,255,0.18) transparent",
          }}
        >
          <div className="mb-5">
            <p className="mb-1 text-[0.64rem] font-bold uppercase tracking-[0.22em] text-white/55">
              Welcome
            </p>
            <h1
              className="text-[1.55rem] font-extrabold leading-tight text-white"
              style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
            >
              Set Up Alex
            </h1>
          </div>

          <div className="space-y-4">
            <Section
              icon={<MapPin className="h-4 w-4 text-white/80" />}
              title="Where do you study?"
              helper="Alex will match the setup to your curriculum."
            >
              <div className="grid grid-cols-2 gap-2">
                {countries.map((item) => (
                  <OptionCard
                    key={item.code}
                    title={item.name}
                    eyebrow={item.flag}
                    selected={country === item.code}
                    onClick={() => chooseCountry(item.code)}
                  />
                ))}
              </div>
            </Section>

            <AnimatePresence initial={false}>
              {country && (
                <Section
                  key="degree"
                  icon={<GraduationCap className="h-4 w-4 text-white/80" />}
                  title="What are you studying?"
                  helper="Choose the degree Alex should build around."
                >
                  <div className="grid gap-2">
                    {visibleDegrees.map((item) => (
                      <OptionCard
                        key={item.code}
                        title={item.name}
                        description={item.description}
                        selected={degree === item.code}
                        onClick={() => chooseDegree(item.code)}
                      />
                    ))}
                  </div>
                </Section>
              )}

              {degree && (
                <Section
                  key="semester"
                  icon={<GraduationCap className="h-4 w-4 text-white/80" />}
                  title="Which semester are you in?"
                  helper="Alex will open the workspace that matches your current semester."
                >
                  <div className="grid grid-cols-2 gap-2">
                    {semesters.map((item) => (
                      <OptionCard
                        key={item.code}
                        title={item.name}
                        description={item.description}
                        selected={semester === item.code}
                        onClick={() => setSemester(item.code)}
                      />
                    ))}
                  </div>
                </Section>
              )}

              {canFinish && (
                <motion.div
                  key="cta"
                  {...reveal}
                  className="border-t border-white/[0.06] pt-4"
                >
                  <button
                    type="button"
                    onClick={handleFinish}
                    disabled={!canFinish}
                    className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-[14px] bg-white font-bold text-black transition-all hover:brightness-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/60 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {loading ? "Opening Alex..." : "See Alex"}
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
}
