import Image from "next/image";

const CHIPS = [
  "Live voice teaching",
  "Ask follow-up questions",
  "Diagrams for hard topics",
  "Notes + tasks saved automatically",
];

export function Voice() {
  return (
    <section
      className="relative w-full"
      style={{ padding: "96px 16px 0", zIndex: 4 }}
    >
      <div
        className="mx-auto flex flex-col md:flex-row gap-10 items-center w-full"
        style={{ maxWidth: 1280 }}
      >
        <div
          className="hidden md:block flex-shrink-0 relative"
          style={{
            width: 380,
            height: 400,
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 22,
            overflow: "hidden",
            background: "rgba(255,255,255,0.02)",
          }}
        >
          <Image
            src="/landing-voice-demo.png"
            alt="Alex AI voice mentor"
            fill
            sizes="380px"
            style={{
              objectFit: "cover",
              filter:
                "brightness(1.18) contrast(1.06) saturate(1.04) drop-shadow(0 32px 80px rgba(0,0,0,0.45))",
              borderRadius: 20,
            }}
          />
        </div>

        <div className="flex-1 flex flex-col gap-5">
          <h2
            style={{
              color: "rgba(255,255,255,0.95)",
              fontSize: "clamp(1.8rem, 2.4vw, 2.6rem)",
              fontWeight: 600,
              lineHeight: 1.08,
              margin: 0,
            }}
            className="max-md:!text-[clamp(1.9rem,5vw,2.8rem)]"
          >
            Talk to Alex like a private tutor
          </h2>
          <p
            style={{
              color: "rgba(255,255,255,0.56)",
              fontSize: "0.95rem",
              lineHeight: 1.8,
              margin: 0,
            }}
          >
            Speak or type while Alex explains topics, creates diagrams, saves
            notes, and keeps your tasks in one study space.
          </p>
          <div className="flex flex-wrap gap-2.5">
            {CHIPS.map((chip) => (
              <span key={chip} className="proof-chip">
                {chip}
              </span>
            ))}
          </div>
        </div>

        <div
          className="flex-shrink-0 hidden md:flex flex-col items-center justify-center gap-3 relative"
          style={{
            width: "100%",
            maxWidth: 320,
            height: 420,
            padding: "18px 18px 16px",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 30,
            background:
              "radial-gradient(circle at 50% 8%, rgba(255,255,255,0.11) 0%, rgba(255,255,255,0.035) 42%, rgba(255,255,255,0.015) 100%)",
            boxShadow:
              "0 30px 86px rgba(0,0,0,0.34), 0 0 70px rgba(255,255,255,0.035) inset",
          }}
        >
          <div
            className="relative w-full flex items-center justify-center"
            style={{
              height: 338,
              maxWidth: 280,
              overflow: "hidden",
              borderRadius: 28,
            }}
          >
            <div
              className="absolute"
              style={{
                top: "50%",
                left: "50%",
                width: 84,
                height: 84,
                transform: "translate(-50%, -50%)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "50%",
              }}
            />
            <div
              className="absolute"
              style={{
                top: "50%",
                left: "50%",
                width: 52,
                height: 52,
                transform: "translate(-50%, -50%)",
                borderRadius: "50%",
                background:
                  "radial-gradient(circle, rgba(255,255,255,.26) 0%, rgba(255,255,255,.03) 100%)",
                boxShadow: "0 0 26px rgba(255,255,255,.04)",
              }}
            />
          </div>
          <p
            style={{
              color: "rgba(255,255,255,0.64)",
              fontSize: "0.88rem",
              fontWeight: 700,
              margin: 0,
            }}
          >
            Your live AI study mentor
          </p>
        </div>
      </div>
    </section>
  );
}
