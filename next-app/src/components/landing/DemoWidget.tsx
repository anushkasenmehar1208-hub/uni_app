"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

const PROMPTS = [
  {
    q: "Explain Big-O notation like I'm in week 2 of my CS degree",
    a: `**Big-O is how we describe how SLOW an algorithm gets as the input grows.**

Think of it like this: if you double your input, what happens?

• **O(1)** — Constant. Same time, no matter what. Like grabbing the first item in a list.
• **O(n)** — Linear. Double the input, double the time. Like reading every page of a book.
• **O(n^2)** — Quadratic. Double the input, time gets 4x worse. Like comparing every pair of students in a class.
• **O(log n)** — Logarithmic. Time barely grows. Like binary search on a sorted list.

**Quick check:** if you have a loop inside a loop, that's usually O(n^2). One loop = O(n). No loop = O(1).

Want me to walk you through analysing one of your week-2 problems?`,
  },
  {
    q: "Solve: integral of x*ln(x) dx",
    a: `**Integration by parts.** The formula is: integral of u*dv = u*v - integral of v*du.

**Step 1 — pick u and dv:**
• u = ln(x)   (because its derivative is simpler)
• dv = x dx

**Step 2 — find du and v:**
• du = (1/x) dx
• v = x^2/2

**Step 3 — plug in:**
integral of x*ln(x) dx = (x^2/2)*ln(x) - integral of (x^2/2)*(1/x) dx
                       = (x^2/2)*ln(x) - integral of (x/2) dx
                       = (x^2/2)*ln(x) - x^2/4 + C

**Final:**  (x^2 * ln(x))/2 - x^2/4 + C

Want me to verify by differentiating it back? Or try a similar one yourself?`,
  },
  {
    q: "Plan tomorrow — I have an OS exam on Friday",
    a: `**3 days to your OS exam. Here's tomorrow:**

**Morning (90 min) — Process Scheduling**
• FCFS, SJF, Round Robin, Priority — write the algorithm + 1 worked example each
• I'll quiz you on a Gantt chart at the end

**Afternoon (60 min) — Memory Management**
• Paging vs Segmentation — when to use each
• Page replacement: FIFO, LRU, Optimal — practice 1 reference string

**Evening (30 min) — Quick recall**
• Flashcards on Day 1 topics: process states, context switching, system calls

**Day 2 (Wed):** Concurrency — semaphores, deadlock conditions.
**Day 3 (Thu):** Past papers + weak-spot review.

Ready to start? Tell me your first topic and I'll teach it now.`,
  },
];

function renderMarkdown(text: string) {
  const html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
  return { __html: html };
}

export function DemoWidget() {
  const [activeIdx, setActiveIdx] = useState<number | null>(null);
  const [streamedText, setStreamedText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [showCTA, setShowCTA] = useState(false);
  const streamRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (streamRef.current) clearTimeout(streamRef.current);
    };
  }, []);

  function start(idx: number) {
    if (streamRef.current) clearTimeout(streamRef.current);
    setActiveIdx(idx);
    setStreamedText("");
    setIsStreaming(true);
    const fullText = PROMPTS[idx].a;
    let i = 0;
    function tick() {
      const burst = 2 + Math.floor(Math.random() * 5);
      i = Math.min(i + burst, fullText.length);
      setStreamedText(fullText.slice(0, i));
      if (i < fullText.length) {
        streamRef.current = setTimeout(tick, 12 + Math.random() * 8);
      } else {
        setIsStreaming(false);
        setShowCTA(true);
      }
    }
    tick();
  }

  return (
    <section
      id="landing-try-demo"
      className="relative w-full"
      style={{
        padding: "80px 16px 0",
        zIndex: 4,
      }}
    >
      <style>{`
        #landing-try-demo .alex-demo-card {
          background: linear-gradient(180deg, rgba(255,255,255,0.045) 0%, rgba(255,255,255,0.018) 100%);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 28px;
          padding: 22px;
          box-shadow: 0 28px 80px rgba(0,0,0,0.36);
        }
        #landing-try-demo .alex-demo-prompts { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; }
        #landing-try-demo .alex-demo-chip {
          appearance: none;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.10);
          color: rgba(255,255,255,0.86);
          padding: 10px 14px;
          border-radius: 999px;
          font-size: 0.86rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.16s ease;
          font-family: inherit;
        }
        #landing-try-demo .alex-demo-chip:hover {
          background: rgba(255,255,255,0.08);
          border-color: rgba(255,255,255,0.22);
          transform: translateY(-1px);
        }
        #landing-try-demo .alex-demo-chip.is-active {
          background: linear-gradient(180deg, #f7f4ed 0%, #ebe4d7 100%);
          color: #1c1915;
          border-color: rgba(255,255,255,0.16);
        }
        #landing-try-demo .alex-demo-bubble-alex {
          align-self: flex-start;
          max-width: 92%;
          padding: 14px 18px;
          border-radius: 16px 16px 16px 4px;
          background: rgba(255,255,255,0.045);
          border: 1px solid rgba(255,255,255,0.08);
          color: rgba(255,255,255,0.88);
          font-size: 0.95rem;
          line-height: 1.65;
          word-wrap: break-word;
        }
        #landing-try-demo .alex-demo-bubble-alex strong { color: rgba(255,255,255,0.98); font-weight: 700; }
        #landing-try-demo .alex-demo-cursor {
          display: inline-block;
          width: 7px;
          height: 1.05em;
          vertical-align: text-bottom;
          background: rgba(231,182,157,0.85);
          margin-left: 2px;
          animation: alexDemoBlink 0.9s step-end infinite;
        }
        #landing-try-demo .alex-demo-thread {
          display: flex; flex-direction: column;
          gap: 12px; min-height: 280px; padding: 8px 4px;
        }
        #landing-try-demo .alex-demo-empty {
          color: rgba(255,255,255,0.42);
          text-align: center; padding: 80px 20px;
          font-size: 0.95rem;
        }
        #landing-try-demo .alex-demo-cta-row {
          display: flex; gap: 10px; margin-top: 14px;
          padding-top: 14px;
          border-top: 1px solid rgba(255,255,255,0.06);
          align-items: center; flex-wrap: wrap;
        }
        #landing-try-demo .alex-demo-cta {
          background: linear-gradient(180deg, #f7f4ed 0%, #ebe4d7 100%);
          color: #1c1915;
          padding: 12px 22px;
          border-radius: 999px;
          font-weight: 750;
          font-size: 0.92rem;
          text-decoration: none;
          box-shadow: 0 12px 28px rgba(0,0,0,0.32);
          transition: transform 0.16s ease;
        }
        #landing-try-demo .alex-demo-cta:hover { transform: translateY(-1px); }
        #landing-try-demo .alex-demo-note {
          color: rgba(255,255,255,0.5);
          font-size: 0.84rem;
          font-weight: 500;
        }
      `}</style>

      <div className="max-w-[1280px] mx-auto flex flex-col items-center text-center gap-4 mb-10">
        <span className="landing-eyebrow">TRY ALEX</span>
        <h2
          className="landing-heading"
          style={{ fontSize: "clamp(2.4rem, 2.9vw, 3.3rem)" }}
        >
          Ask one question. No signup.
        </h2>
        <p className="landing-sub" style={{ maxWidth: 640 }}>
          Pick a sample question and watch Alex teach it. Then sign up free to
          ask your own.
        </p>
      </div>

      <div className="alex-demo-card mx-auto" style={{ maxWidth: 780 }}>
        <div className="alex-demo-prompts">
          {PROMPTS.map((p, i) => (
            <button
              key={i}
              type="button"
              className={`alex-demo-chip ${activeIdx === i ? "is-active" : ""}`}
              onClick={() => start(i)}
            >
              {p.q}
            </button>
          ))}
        </div>

        <div className="alex-demo-thread">
          {activeIdx === null ? (
            <div className="alex-demo-empty">
              Pick a question above to see Alex teach it.
            </div>
          ) : (
            <div
              className="alex-demo-bubble-alex"
              dangerouslySetInnerHTML={{
                __html:
                  renderMarkdown(streamedText).__html +
                  (isStreaming ? '<span class="alex-demo-cursor"></span>' : ""),
              }}
            />
          )}
        </div>

        {showCTA && (
          <div className="alex-demo-cta-row">
            <Link href="/register" className="alex-demo-cta">
              Start free — ask your own question
            </Link>
            <span className="alex-demo-note">3-day full trial · no card needed</span>
          </div>
        )}
      </div>
    </section>
  );
}
