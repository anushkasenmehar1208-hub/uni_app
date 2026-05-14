export function Founder() {
  return (
    <section
      id="landing-founder-section"
      className="relative w-full"
      style={{ padding: "112px 16px 0", zIndex: 4 }}
    >
      <div
        className="mx-auto"
        style={{
          maxWidth: 900,
          padding: "40px 48px",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 28,
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)",
          boxShadow: "0 28px 80px rgba(0,0,0,0.36)",
        }}
      >
        <div className="flex flex-col md:flex-row gap-8 items-center md:items-start">
          <div
            className="flex-shrink-0 flex items-center justify-center"
            style={{
              width: 148,
              height: 148,
              borderRadius: "50%",
              border: "1px solid rgba(255,255,255,0.14)",
              background:
                "linear-gradient(135deg, rgba(231,182,157,0.32) 0%, rgba(94,211,132,0.18) 100%)",
              boxShadow: "0 24px 60px rgba(0,0,0,0.4)",
            }}
          >
            <span
              style={{
                fontFamily: "Georgia, 'Times New Roman', serif",
                fontSize: "3.6rem",
                fontWeight: 700,
                color: "rgba(255,255,255,0.95)",
              }}
            >
              A
            </span>
          </div>

          <div className="flex-1 flex flex-col gap-5">
            <span className="landing-eyebrow">BUILT BY STUDENTS</span>

            <p
              style={{
                color: "rgba(255,255,255,0.86)",
                fontSize: "1.18rem",
                lineHeight: 1.65,
                fontStyle: "italic",
                margin: 0,
              }}
              className="max-md:!text-[1.05rem]"
            >
              &ldquo;We built Alex because no AI tool actually understood what
              students were studying. ChatGPT could solve a problem, but it
              couldn&apos;t plan a semester, follow a syllabus, or teach day by
              day. So we built one that does — for every student trying to
              figure it out.&rdquo;
            </p>

            <div className="flex flex-col gap-1">
              <span
                style={{
                  color: "rgba(255,255,255,0.94)",
                  fontSize: "0.95rem",
                  fontWeight: 700,
                }}
              >
                The alexstudies team
              </span>
              <span
                style={{
                  color: "rgba(255,255,255,0.52)",
                  fontSize: "0.92rem",
                  fontWeight: 500,
                }}
              >
                Building for university students
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
