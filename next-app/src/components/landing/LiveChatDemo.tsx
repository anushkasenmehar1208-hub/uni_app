"use client";

import Image from "next/image";
import { useState } from "react";

interface Msg {
  role: "user" | "assistant";
  text: string;
}

const INITIAL: Msg[] = [
  {
    role: "assistant",
    text: "Today, start with your hardest subject. I can make a 30-minute plan, explain the topic, and quiz you after.",
  },
];

function reply(prompt: string): string {
  const t = prompt.toLowerCase().trim();
  if (!t || /\b(hi|hello|hey)\b/.test(t))
    return "Today, start with your hardest subject. I can make a 30-minute plan, explain the topic, and quiz you after.";
  if (/(semester|syllabus|planner|today|study today)/.test(t))
    return "Today, start with your hardest subject. I can make a 30-minute plan, explain the topic, and quiz you after.";
  if (/(price|pricing|plan|pro|free|cost)/.test(t))
    return "You can start free. Pro is for daily studying when Alex becomes part of your routine.";
  if (/(voice|speak|talk|mentor|call)/.test(t))
    return "You can speak or type while Alex explains topics and keeps notes and tasks in one place.";
  if (/(quiz|test|practice)/.test(t))
    return "Alex can make quick quizzes so you can check whether the topic actually stuck.";
  if (/(notes|tasks|todo)/.test(t))
    return "Alex helps save notes, track tasks, and keep your study flow organized.";
  if (/(models|deepseek|claude|chatgpt|teach)/.test(t))
    return "Alex focuses on teaching your semester day by day, not making you choose tools.";
  return "Alex helps you study better every day with planning, teaching, quizzes, notes, voice, and tasks.";
}

export function LiveChatDemo() {
  const [messages, setMessages] = useState<Msg[]>(INITIAL);
  const [input, setInput] = useState("");
  const [sendCount, setSendCount] = useState(0);
  const locked = sendCount >= 5;

  function send() {
    const text = input.trim();
    if (!text || locked) return;
    const userMsg: Msg = { role: "user", text };
    const assistantMsg: Msg = locked
      ? { role: "assistant", text: "Hello again. Demo limit reached, but the full Alex AI chat lives inside the app." }
      : { role: "assistant", text: reply(text) };
    setMessages((m) => [...m, userMsg, assistantMsg]);
    setInput("");
    setSendCount((c) => c + 1);
  }

  return (
    <section id="landing-live-chat-demo" className="w-full text-white/90">
      <style>{`
        #landing-live-chat-demo .lc-layout {
          display: grid;
          grid-template-columns: minmax(260px, 360px) minmax(320px, 1fr);
          gap: 48px;
          align-items: center;
          width: 100%;
        }
        #landing-live-chat-demo .lc-orbit-wrap {
          display: flex; flex-direction: column;
          align-items: center; justify-content: center;
          gap: 18px; min-height: 340px;
        }
        #landing-live-chat-demo .lc-orbit {
          position: relative; width: 230px; height: 230px;
        }
        #landing-live-chat-demo .lc-ring {
          position: absolute; inset: 18px; border-radius: 999px;
          border: 1px solid rgba(255,255,255,0.08);
          box-shadow: 0 0 40px rgba(255,255,255,0.03) inset;
        }
        #landing-live-chat-demo .lc-ring::after {
          content: ""; position: absolute; inset: 22px;
          border-radius: 999px;
          border: 1px dashed rgba(255,255,255,0.08);
        }
        #landing-live-chat-demo .lc-core {
          position: absolute; left: 50%; top: 50%;
          transform: translate(-50%, -50%);
          width: 104px; height: 104px; border-radius: 999px;
          display: flex; align-items: center; justify-content: center;
          background: radial-gradient(circle at center, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0.04) 58%, transparent 100%);
          border: 1px solid rgba(255,255,255,0.08);
          backdrop-filter: blur(20px);
          box-shadow: 0 20px 60px rgba(0,0,0,0.35);
          text-align: center; padding: 14px; overflow: hidden;
        }
        #landing-live-chat-demo .lc-core-logo {
          position: absolute; inset: 18px;
          width: calc(100% - 36px); height: calc(100% - 36px);
          object-fit: contain; opacity: 0.14;
          pointer-events: none;
        }
        #landing-live-chat-demo .lc-core span {
          position: relative; z-index: 1; font-size: 0.95rem;
          line-height: 1; color: rgba(255,255,255,0.9);
          font-weight: 700;
        }
        #landing-live-chat-demo .lc-orbit-note {
          max-width: 300px; text-align: center;
          color: rgba(255,255,255,0.54);
          font-size: 0.95rem; line-height: 1.7;
          margin: 0;
        }
        #landing-live-chat-demo .lc-chat {
          position: relative; min-height: 340px;
          display: flex; flex-direction: column;
          justify-content: center; gap: 18px;
        }
        #landing-live-chat-demo .lc-panel {
          width: 100%; max-width: 560px; padding: 18px;
          border-radius: 24px;
          background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
          border: 1px solid rgba(255,255,255,0.08);
          backdrop-filter: blur(24px);
          box-shadow: 0 24px 70px rgba(0,0,0,0.28);
          display: flex; flex-direction: column; gap: 16px;
        }
        #landing-live-chat-demo .lc-eyebrow {
          font-size: 0.76rem; text-transform: uppercase;
          color: rgba(255,255,255,0.42);
          margin-bottom: 2px; font-weight: 700;
        }
        #landing-live-chat-demo .lc-title {
          font-size: clamp(1.8rem, 3vw, 2.8rem);
          line-height: 1.02;
          color: rgba(255,255,255,0.95);
          margin: 0 0 12px 0; font-weight: 600;
          max-width: 580px;
        }
        #landing-live-chat-demo .lc-sub {
          font-size: 1rem; line-height: 1.75;
          color: rgba(255,255,255,0.56);
          margin: 0; max-width: 560px;
        }
        #landing-live-chat-demo .lc-messages {
          display: flex; flex-direction: column; gap: 12px;
          min-height: 132px; max-width: 520px;
        }
        #landing-live-chat-demo .lc-bubble {
          width: fit-content; max-width: min(100%, 420px);
          padding: 12px 16px; border-radius: 20px;
          font-size: 0.96rem; line-height: 1.5;
          backdrop-filter: blur(18px);
          box-shadow: 0 20px 44px rgba(0,0,0,0.22);
        }
        #landing-live-chat-demo .lc-bubble--assistant {
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.08);
          color: rgba(255,255,255,0.92); align-self: flex-start;
        }
        #landing-live-chat-demo .lc-bubble--user {
          background: rgba(255,255,255,0.14);
          border: 1px solid rgba(255,255,255,0.08);
          color: rgba(255,255,255,0.95); align-self: flex-end;
        }
        #landing-live-chat-demo .lc-composer {
          display: flex; align-items: center; gap: 10px;
          width: 100%; padding: 10px; border-radius: 999px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          box-shadow: 0 22px 60px rgba(0,0,0,0.26);
        }
        #landing-live-chat-demo .lc-input {
          flex: 1; border: none; outline: none;
          background: transparent;
          color: rgba(255,255,255,0.92);
          font-size: 0.96rem; padding: 0 8px;
        }
        #landing-live-chat-demo .lc-input::placeholder { color: rgba(255,255,255,0.34); }
        #landing-live-chat-demo .lc-send {
          border: none; outline: none; cursor: pointer;
          border-radius: 999px; padding: 11px 18px;
          color: #09090b; font-size: 0.9rem; font-weight: 700;
          background: linear-gradient(180deg, #f5f5f5 0%, #e8e8ea 100%);
          box-shadow: 0 12px 32px rgba(0,0,0,0.22);
          transition: transform 0.18s ease;
        }
        #landing-live-chat-demo .lc-send:hover { transform: translateY(-1px); }
        #landing-live-chat-demo .lc-send:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
        #landing-live-chat-demo .lc-meta {
          display: flex; gap: 14px; flex-wrap: wrap;
          color: rgba(255,255,255,0.36);
          font-size: 0.82rem;
        }
        @media (max-width: 920px) {
          #landing-live-chat-demo .lc-layout {
            grid-template-columns: 1fr; gap: 22px;
          }
          #landing-live-chat-demo .lc-orbit-wrap,
          #landing-live-chat-demo .lc-chat { min-height: auto; }
          #landing-live-chat-demo .lc-orbit { width: 210px; height: 210px; }
        }
      `}</style>

      <div className="lc-layout">
        <div className="lc-orbit-wrap">
          <div className="lc-orbit" aria-hidden>
            <div className="lc-ring" />
            <div className="lc-core">
              <Image
                src="/a_logo.png"
                alt=""
                width={68}
                height={68}
                className="lc-core-logo"
              />
              <span>Alex AI</span>
            </div>
          </div>
          <p className="lc-orbit-note">Plan. Learn. Quiz. Repeat.</p>
        </div>

        <div className="lc-chat">
          <div>
            <div className="lc-eyebrow">Live chat demo</div>
            <h3 className="lc-title">Ask Alex about your studies</h3>
            <p className="lc-sub">
              Try asking what to study today, explain a hard topic, or make a
              quick quiz.
            </p>
          </div>

          <div className="lc-panel">
            <div className="lc-messages">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`lc-bubble lc-bubble--${m.role === "user" ? "user" : "assistant"}`}
                >
                  {m.text}
                </div>
              ))}
            </div>

            <div className="lc-composer">
              <input
                className="lc-input"
                type="text"
                maxLength={120}
                placeholder={
                  locked ? "Open Alex AI to continue" : "Ask Alex what to study today..."
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") send();
                }}
                disabled={locked}
              />
              <button
                className="lc-send"
                type="button"
                onClick={send}
                disabled={locked || !input.trim()}
              >
                Send
              </button>
            </div>

            <div className="lc-meta">
              <span>Instant preview responses from the Alex AI website assistant</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
