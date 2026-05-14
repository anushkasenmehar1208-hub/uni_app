const FAQS = [
  {
    q: "Is this just ChatGPT in a wrapper?",
    a: "No. Alex routes between 5 different AI models depending on the question, and pairs that with curriculum-aware planning, voice mentoring, notes, and quizzes. ChatGPT is one general model with no idea what semester you're in. Alex builds a real day-by-day study plan around your actual courses.",
  },
  {
    q: "Will my professor know I used AI?",
    a: "Alex is built for learning, not cheating. The default mode teaches you the topic step-by-step and quizzes you — it doesn't write your assignment for you. If you ask Alex to explain a concept and then write your own answer, you've used it the same way you'd use a tutor. We don't recommend submitting raw AI output as your work, and most universities have clear policies on what's allowed.",
  },
  {
    q: "What if my exact course or university isn't listed?",
    a: "Pick the 'Custom' degree option during signup and Alex lets you define your own subjects. Built-in curricula currently cover Sri Lanka, UK, US, and India — but Alex teaches any subject you give it.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Yes. One click in your account, no email required, no questions asked. You also get a 7-day money-back guarantee on Pro — if you don't find it useful in the first week, email us for a full refund.",
  },
  {
    q: "How is the price so low compared to ChatGPT Plus?",
    a: "Three reasons. First, Alex is built specifically for studying — we route to cheaper models for routine questions and only use expensive ones when reasoning is genuinely needed. Second, we're an independent team, not a venture-funded company. Third, students should be able to afford this — that's the whole point.",
  },
  {
    q: "Do I need a credit card to start?",
    a: "No. The first 3 days are fully free, no card required. After that, the free plan gives you 10 messages a day forever. You only enter payment details if you decide to upgrade to Pro.",
  },
  {
    q: "What happens to my chats and data?",
    a: "Your chats are private to your account. We don't sell student data and we don't train AI models on your conversations. Full details are in our Privacy Policy.",
  },
  {
    q: "Can I share an account with my classmate?",
    a: "Each account is meant for one student because Alex builds a personalised study plan around your specific degree, week, and progress. Sharing breaks the planner. If you want to study together, both of you should sign up.",
  },
];

export function FAQ() {
  return (
    <section
      id="landing-faq-section"
      className="relative w-full"
      style={{ padding: "120px 16px 0", zIndex: 4 }}
    >
      <style>{`
        #landing-faq-section details[open] .alex-faq-icon { transform: rotate(45deg); }
        #landing-faq-section .alex-faq-icon {
          transition: transform 0.18s ease;
          display: inline-block;
        }
        #landing-faq-section summary::-webkit-details-marker { display: none; }
        #landing-faq-section summary { list-style: none; cursor: pointer; }
      `}</style>

      <div
        className="mx-auto flex flex-col items-start gap-3 mb-10"
        style={{ maxWidth: 780 }}
      >
        <span className="landing-eyebrow">FAQ</span>
        <h2
          className="landing-heading"
          style={{ fontSize: "clamp(2.4rem, 2.9vw, 3.3rem)", textAlign: "left" }}
        >
          Honest answers to what students actually ask
        </h2>
      </div>

      <div className="mx-auto flex flex-col gap-2.5" style={{ maxWidth: 780 }}>
        {FAQS.map((item, i) => (
          <details
            key={i}
            style={{
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 16,
              background:
                "linear-gradient(180deg, rgba(255,255,255,0.045) 0%, rgba(255,255,255,0.02) 100%)",
            }}
          >
            <summary
              className="flex items-center justify-between gap-4"
              style={{
                padding: "20px 22px",
                color: "rgba(255,255,255,0.94)",
                fontSize: "1.05rem",
                fontWeight: 650,
                letterSpacing: "-0.02em",
              }}
            >
              <span>{item.q}</span>
              <span
                className="alex-faq-icon"
                style={{
                  color: "rgba(255,255,255,0.62)",
                  fontSize: "1.4rem",
                  lineHeight: 1,
                }}
              >
                +
              </span>
            </summary>
            <div
              style={{
                padding: "0 22px 22px 22px",
                color: "rgba(255,255,255,0.66)",
                fontSize: "0.98rem",
                lineHeight: 1.7,
              }}
            >
              {item.a}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
