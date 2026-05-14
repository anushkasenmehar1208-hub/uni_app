"use client";

import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import { useState } from "react";

const faqs = [
  {
    question: "Is this just ChatGPT in a different wrapper?",
    answer:
      "No. Alex AI is built specifically around your university semester. ChatGPT doesn't know what you're studying next week, what your exam covers, or how your degree is structured. Alex builds a day-by-day plan around your real semester, tracks what you've learned, and adapts as you go.",
  },
  {
    question: "Which universities and degrees are supported?",
    answer:
      "We currently support Computer Science, Software Engineering, and BECS programs in the UK, US, India, and Sri Lanka — with more degrees being added every week. If your degree isn't listed yet, you can request it during signup.",
  },
  {
    question: "Can I cancel anytime?",
    answer:
      "Yes. Cancel anytime from your account settings. You'll keep access until the end of your billing period, and you'll never be charged again. We also offer a 30-day money-back guarantee — no questions asked.",
  },
  {
    question: "Will Alex actually help me get better grades?",
    answer:
      "Alex isn't a magic shortcut — it's a tool. If you use it daily for 10-15 minutes, you'll be ahead of most of your classmates because you'll have a structured plan, instant explanations when you're stuck, and quizzes to make sure things stick.",
  },
  {
    question: "What about exam time?",
    answer:
      "Exam mode generates practice problems, flashcards, and concise summaries for whatever exam is coming up. Built-in spaced repetition means you'll actually remember things during the exam — not just the night before.",
  },
  {
    question: "Is my data private?",
    answer:
      "Yes. Your study data is yours. We don't sell it, train AI models on it, or share it with anyone. You can export or delete everything anytime.",
  },
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" className="relative py-24 md:py-32">
      <div className="max-w-3xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] mb-6">
            <span className="text-[0.72rem] font-bold tracking-[0.16em] text-white/64 uppercase">
              FAQ
            </span>
          </div>
          <h2 className="text-[clamp(2rem,4vw,3rem)] font-medium tracking-tight gradient-text leading-[1.1]">
            Questions, answered
          </h2>
        </motion.div>

        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <motion.div
              key={faq.question}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="rounded-2xl border border-white/[0.06] bg-white/[0.015] overflow-hidden"
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between gap-4 p-5 text-left hover:bg-white/[0.02] transition-colors"
              >
                <span className="text-white font-medium text-[1.02rem] leading-snug">
                  {faq.question}
                </span>
                <Plus
                  className={`w-5 h-5 text-white/60 flex-shrink-0 transition-transform ${
                    open === i ? "rotate-45" : ""
                  }`}
                />
              </button>
              <div
                className={`grid transition-all duration-300 ${
                  open === i
                    ? "grid-rows-[1fr] opacity-100"
                    : "grid-rows-[0fr] opacity-0"
                }`}
              >
                <div className="overflow-hidden">
                  <div className="px-5 pb-5 text-white/56 text-[0.96rem] leading-relaxed">
                    {faq.answer}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
