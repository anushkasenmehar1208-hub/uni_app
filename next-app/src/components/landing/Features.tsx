"use client";

import { motion } from "framer-motion";
import { BookOpen, Mic, ListChecks, Brain, Youtube, FileText } from "lucide-react";

const features = [
  {
    icon: BookOpen,
    eyebrow: "Daily Lessons",
    title: "A real semester plan built around your degree",
    description:
      "Choose your university and major — Alex builds a day-by-day plan with the right topics, in the right order, for your full semester.",
  },
  {
    icon: Youtube,
    eyebrow: "Auto Quizzes",
    title: "Watch any YouTube lesson, get a quiz instantly",
    description:
      "Drop any YouTube link — Alex reads the transcript and builds a quiz so you actually remember what you watched.",
  },
  {
    icon: Mic,
    eyebrow: "Voice Teaching",
    title: "Talk to Alex like a real tutor",
    description:
      "Ask questions out loud. Alex explains concepts, breaks down problems, and walks you through anything you don't understand.",
  },
  {
    icon: ListChecks,
    eyebrow: "Smart Tracker",
    title: "Tasks, exams, and progress in one place",
    description:
      "Alex remembers what you've studied, what's coming up, and what needs review. No more scattered notes or forgotten deadlines.",
  },
  {
    icon: Brain,
    eyebrow: "Exam Mode",
    title: "Study smarter before every exam",
    description:
      "Alex generates practice problems, flashcards, and summaries tailored to your upcoming exams. Spaced repetition built in.",
  },
  {
    icon: FileText,
    eyebrow: "Notes & Recall",
    title: "Your notes, organized and searchable",
    description:
      "Upload notes, get them organized automatically. Ask Alex to find that one thing your professor said in week 3 — instantly.",
  },
];

export function Features() {
  return (
    <section id="how-it-works" className="relative py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7 }}
          className="text-center mb-16 max-w-3xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] mb-6">
            <span className="text-[0.72rem] font-bold tracking-[0.16em] text-white/64 uppercase">
              Built for students
            </span>
          </div>
          <h2 className="text-[clamp(2rem,4vw,3rem)] font-medium tracking-tight gradient-text mb-4 leading-[1.1]">
            Everything you need to study,
            <br /> in one place
          </h2>
          <p className="text-white/48 text-[1.05rem] leading-relaxed">
            Six tools that work together — built around how real students actually study.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.6, delay: i * 0.08 }}
                className="group relative p-6 rounded-2xl border border-white/[0.06] bg-gradient-to-b from-white/[0.025] to-white/[0.005] hover:from-white/[0.04] hover:to-white/[0.01] hover:border-white/[0.12] transition-all duration-300"
              >
                <div className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center mb-5 group-hover:bg-white/[0.1] transition-colors">
                  <Icon className="w-5 h-5 text-white/80" />
                </div>
                <div className="text-[0.7rem] font-bold tracking-[0.16em] text-white/40 uppercase mb-2">
                  {feature.eyebrow}
                </div>
                <h3 className="text-[1.1rem] font-semibold text-white mb-2 leading-snug">
                  {feature.title}
                </h3>
                <p className="text-[0.92rem] text-white/52 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
