import { LiveChatDemo } from "./LiveChatDemo";

const STEPS = [
  "Choose your degree",
  "Alex AI analyzes your semester",
  "Get your personalized study system",
];

export function Story() {
  return (
    <section
      id="landing-story-section"
      className="relative w-full"
      style={{ padding: "80px 16px 0", zIndex: 4 }}
    >
      <div
        className="mx-auto flex flex-col items-start"
        style={{
          maxWidth: "min(1280px, calc(100vw - 32px))",
        }}
      >
        <h2
          className="landing-heading"
          style={{
            fontSize: "clamp(2.7rem, 4.15vw, 4rem)",
            fontWeight: 500,
            margin: 0,
          }}
        >
          Choose your degree. Alex builds
          <br />
          your daily study path.
        </h2>

        <p
          style={{
            color: "rgba(255,255,255,0.52)",
            fontSize: "clamp(1.18rem, 1.65vw, 1.5rem)",
            fontWeight: 450,
            lineHeight: 1.5,
            maxWidth: "min(1120px, calc(100vw - 56px))",
            marginTop: 20,
          }}
        >
          From your semester subjects, Alex creates a clear daily path and helps
          you study without getting lost.
        </p>

        <div
          className="w-full self-center flex flex-col items-center gap-4"
          style={{
            maxWidth: 560,
            marginTop: 56,
            paddingTop: 48,
            borderTop: "1px solid rgba(255,255,255,0.09)",
          }}
        >
          {STEPS.map((step, i) => (
            <div key={step} className="flex flex-col items-center gap-3">
              <div
                style={{
                  color: "rgba(255,255,255,0.9)",
                  fontSize: "clamp(1.28rem, 1.9vw, 1.65rem)",
                  fontWeight: 500,
                  fontFamily: "'Plus Jakarta Sans', 'Space Grotesk', sans-serif",
                  textAlign: "center",
                }}
              >
                {step}
              </div>
              {i < STEPS.length - 1 && (
                <span
                  style={{
                    color: "rgba(255,255,255,0.38)",
                    fontSize: "1.35rem",
                  }}
                >
                  ↓
                </span>
              )}
            </div>
          ))}
        </div>

        <div className="w-full" style={{ paddingTop: 64 }}>
          <LiveChatDemo />
        </div>
      </div>
    </section>
  );
}
