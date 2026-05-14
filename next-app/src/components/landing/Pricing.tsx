"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Check, Shield } from "lucide-react";

const plans = [
  {
    name: "Pro",
    price: "3",
    period: "/month",
    description: "Everything you need to study a full semester.",
    features: [
      "Full semester plan for your degree",
      "Daily AI lessons with voice teaching",
      "Quiz any YouTube video instantly",
      "Notes, tasks, and exam tracker",
      "Unlimited chats with Alex",
    ],
    cta: "Start with Pro",
    highlight: false,
  },
  {
    name: "Max",
    price: "25",
    period: "/month",
    description: "For students who want the best AI models.",
    features: [
      "Everything in Pro",
      "Claude Opus 4 + GPT-5 access",
      "Priority response speed",
      "Advanced exam mode with custom drills",
      "Concept video generation",
    ],
    cta: "Get Max",
    highlight: true,
    badge: "Most popular",
  },
  {
    name: "Ultra",
    price: "100",
    period: "/month",
    description: "For power users who need everything.",
    features: [
      "Everything in Max",
      "Unlimited concept video generation",
      "Priority support from the team",
      "Early access to new features",
      "API access for custom integrations",
    ],
    cta: "Go Ultra",
    highlight: false,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="relative py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7 }}
          className="text-center mb-14 max-w-3xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] mb-6">
            <span className="text-[0.72rem] font-bold tracking-[0.16em] text-white/64 uppercase">
              Simple Pricing
            </span>
          </div>
          <h2 className="text-[clamp(2rem,4vw,3rem)] font-medium tracking-tight gradient-text mb-4 leading-[1.1]">
            Start at $3/month.
            <br />
            Cancel anytime.
          </h2>
          <p className="text-white/48 text-[1.05rem] leading-relaxed">
            Less than a coffee. More useful than your textbook.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-5 max-w-6xl mx-auto">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
              className={`relative p-7 rounded-2xl border ${
                plan.highlight
                  ? "border-white/[0.18] bg-gradient-to-b from-white/[0.06] to-white/[0.015]"
                  : "border-white/[0.06] bg-gradient-to-b from-white/[0.025] to-white/[0.005]"
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-white text-black text-[0.68rem] font-bold tracking-wider uppercase">
                  {plan.badge}
                </div>
              )}

              <div className="mb-4">
                <h3 className="text-[1.2rem] font-semibold text-white mb-2">
                  {plan.name}
                </h3>
                <p className="text-white/52 text-[0.92rem] leading-relaxed">
                  {plan.description}
                </p>
              </div>

              <div className="mb-6 flex items-baseline">
                <span className="text-white text-[2.6rem] font-medium tracking-tight">
                  ${plan.price}
                </span>
                <span className="text-white/48 text-[1rem] ml-1">
                  {plan.period}
                </span>
              </div>

              <Link
                href="/register"
                className={`block text-center text-[14px] font-semibold py-3 rounded-full mb-7 transition-all ${
                  plan.highlight
                    ? "bg-white text-black hover:bg-white/90 hover:scale-[1.02]"
                    : "bg-white/[0.06] text-white border border-white/[0.08] hover:bg-white/[0.1]"
                }`}
              >
                {plan.cta}
              </Link>

              <ul className="space-y-3">
                {plan.features.map((feature) => (
                  <li
                    key={feature}
                    className="flex items-start gap-2.5 text-[0.92rem] text-white/70"
                  >
                    <Check className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="mt-10 flex items-center justify-center gap-2 text-white/52 text-[0.92rem]"
        >
          <Shield className="w-4 h-4" />
          <span>30-day money-back guarantee. No questions asked.</span>
        </motion.div>
      </div>
    </section>
  );
}
