import Image from "next/image";

const CARDS = [
  {
    eyebrow: "Onboarding",
    title: "Built for your degree",
    description:
      "Pick your country, degree, and semester — Alex builds a personalized day-by-day study plan instantly.",
    image: "/landing-onboarding-demo.png",
  },
  {
    eyebrow: "Auto Quizzes",
    title: "Watch any YouTube lesson, get a quiz instantly",
    description:
      "Drop any YouTube link — Alex reads the transcript and builds a quiz so you actually remember what you watched. No more passive watching.",
    image: "/landing-quiz-demo.png",
  },
  {
    eyebrow: "Habit Tracker",
    title: "Builds your study habit",
    description:
      "100-day streak tracker keeps you accountable. See your progress across every subject at a glance.",
    image: "/landing-tracker-demo.png",
  },
  {
    eyebrow: "Notes",
    title: "Save and organize your notes",
    description:
      "Create rich study notes, attach media, and keep AI explanations saved in one library for every subject.",
    image: "/landing-notes-demo.png",
  },
];

export function Features() {
  return (
    <section
      id="landing-feature-showcase"
      className="relative w-full"
      style={{ padding: "112px 16px 0", zIndex: 4 }}
    >
      <div
        className="mx-auto flex flex-col items-center text-center gap-4 mb-12"
        style={{ maxWidth: 1280 }}
      >
        <span className="landing-eyebrow">EVERYTHING YOU NEED</span>
        <h2
          className="landing-heading"
          style={{ fontSize: "clamp(2.4rem, 2.9vw, 3.3rem)" }}
        >
          One app. Your entire semester.
        </h2>
        <p className="landing-sub" style={{ maxWidth: 640 }}>
          Degree plan, daily lessons, notes, habit tracker, voice tutor — built
          for how students actually study.
        </p>
      </div>

      <div
        className="mx-auto flex flex-wrap justify-center gap-5"
        style={{ maxWidth: 1520 }}
      >
        {CARDS.map((card) => (
          <article
            key={card.title}
            className="flex flex-col gap-4 w-full sm:w-[calc(50%-10px)] lg:w-[calc(25%-15px)]"
            style={{
              padding: 18,
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 24,
              background:
                "linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)",
              boxShadow: "0 24px 60px rgba(0,0,0,0.34)",
            }}
          >
            <div
              className="relative w-full"
              style={{
                height: 220,
                borderRadius: 18,
                overflow: "hidden",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              <Image
                src={card.image}
                alt={card.title}
                fill
                sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
                style={{
                  objectFit: "cover",
                  filter: "brightness(1.25) contrast(1.06) saturate(1.04)",
                }}
              />
            </div>
            <div className="flex flex-col gap-2">
              <span
                style={{
                  color: "rgba(255,255,255,0.44)",
                  fontSize: "0.74rem",
                  fontWeight: 700,
                  letterSpacing: "0.18em",
                  textTransform: "uppercase",
                }}
              >
                {card.eyebrow}
              </span>
              <h3
                style={{
                  color: "rgba(255,255,255,0.94)",
                  fontSize: "1.15rem",
                  fontWeight: 650,
                  margin: 0,
                }}
              >
                {card.title}
              </h3>
              <p
                style={{
                  color: "rgba(255,255,255,0.56)",
                  fontSize: "0.95rem",
                  lineHeight: 1.7,
                  margin: 0,
                }}
              >
                {card.description}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
