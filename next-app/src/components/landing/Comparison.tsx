type CellTone = "yes" | "no" | "neutral" | "strong";

interface Row {
  label: string;
  alex: { text: string; tone: CellTone };
  chatgpt: { text: string; tone: CellTone };
  claude: { text: string; tone: CellTone };
  highlight?: boolean;
}

const ROWS: Row[] = [
  {
    label: "Knows your university syllabus",
    alex: { text: "Yes", tone: "yes" },
    chatgpt: { text: "No", tone: "no" },
    claude: { text: "No", tone: "no" },
    highlight: true,
  },
  {
    label: "Day-by-day semester planner",
    alex: { text: "Built in", tone: "yes" },
    chatgpt: { text: "Manual", tone: "neutral" },
    claude: { text: "Manual", tone: "neutral" },
  },
  {
    label: "Voice mentor (talk like a tutor)",
    alex: { text: "45 min/day", tone: "yes" },
    chatgpt: { text: "Limited", tone: "neutral" },
    claude: { text: "No", tone: "no" },
    highlight: true,
  },
  {
    label: "YouTube lectures + auto quizzes",
    alex: { text: "Yes", tone: "yes" },
    chatgpt: { text: "No", tone: "no" },
    claude: { text: "No", tone: "no" },
  },
  {
    label: "Notes & task tracker",
    alex: { text: "Yes", tone: "yes" },
    chatgpt: { text: "No", tone: "no" },
    claude: { text: "No", tone: "no" },
  },
  {
    label: "Study diagrams on demand",
    alex: { text: "Yes", tone: "yes" },
    chatgpt: { text: "Limited", tone: "neutral" },
    claude: { text: "Limited", tone: "neutral" },
  },
  {
    label: "Auto-routes between 5 AI models",
    alex: { text: "Yes", tone: "yes" },
    chatgpt: { text: "1 model", tone: "neutral" },
    claude: { text: "1 model", tone: "neutral" },
  },
  {
    label: "Monthly price",
    alex: { text: "$3", tone: "strong" },
    chatgpt: { text: "$20", tone: "neutral" },
    claude: { text: "$20", tone: "neutral" },
    highlight: true,
  },
];

const TONE_COLOR: Record<CellTone, { color: string; weight: number }> = {
  yes: { color: "rgba(134,239,172,0.95)", weight: 750 },
  no: { color: "rgba(248,113,113,0.78)", weight: 650 },
  neutral: { color: "rgba(255,255,255,0.78)", weight: 550 },
  strong: { color: "rgba(250,249,245,0.98)", weight: 780 },
};

export function Comparison() {
  return (
    <section
      id="landing-comparison-section"
      className="relative w-full flex justify-center"
      style={{ padding: "104px 16px 0", zIndex: 4 }}
    >
      <div
        className="w-full flex flex-col items-start gap-4"
        style={{ maxWidth: 1280 }}
      >
        <span className="landing-eyebrow">WHY STUDENTS SWITCH</span>
        <h2
          className="landing-heading"
          style={{ fontSize: "clamp(2.4rem, 2.9vw, 3.3rem)", textAlign: "left" }}
        >
          Alex vs ChatGPT vs Claude — for studying
        </h2>
        <p
          className="landing-sub"
          style={{ maxWidth: 720, textAlign: "left" }}
        >
          Generic chatbots don&apos;t know your syllabus. Alex does. At a
          fraction of the price.
        </p>

        <div
          className="w-full overflow-x-auto"
          style={{
            maxWidth: 1080,
            padding: 22,
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 28,
            background:
              "linear-gradient(180deg, rgba(255,255,255,0.045) 0%, rgba(255,255,255,0.018) 100%)",
            boxShadow: "0 28px 80px rgba(0,0,0,0.36)",
            marginTop: 16,
          }}
        >
          <div
            className="grid items-center"
            style={{
              gridTemplateColumns:
                "minmax(300px, 2fr) repeat(3, minmax(128px, 1fr))",
              gap: 16,
              minWidth: 760,
              paddingBottom: 16,
              borderBottom: "1px solid rgba(255,255,255,0.08)",
            }}
          >
            <div />
            <ColHeader name="Alex AI" price="Pro · $3/mo" green />
            <ColHeader name="ChatGPT" price="Plus · $20/mo" />
            <ColHeader name="Claude" price="Pro · $20/mo" />
          </div>

          {ROWS.map((row) => (
            <div
              key={row.label}
              className="grid items-center"
              style={{
                gridTemplateColumns:
                  "minmax(300px, 2fr) repeat(3, minmax(128px, 1fr))",
                gap: 16,
                minWidth: 760,
                padding: "14px 12px",
                marginTop: 10,
                borderRadius: 16,
                background: row.highlight
                  ? "linear-gradient(180deg, rgba(94,211,132,0.08) 0%, rgba(94,211,132,0.02) 100%)"
                  : "transparent",
                border: row.highlight
                  ? "1px solid rgba(94,211,132,0.18)"
                  : "1px solid transparent",
              }}
            >
              <span
                style={{
                  color: "rgba(255,255,255,0.84)",
                  fontWeight: 600,
                  fontSize: "0.96rem",
                }}
              >
                {row.label}
              </span>
              <Cell {...row.alex} />
              <Cell {...row.chatgpt} />
              <Cell {...row.claude} />
            </div>
          ))}
        </div>

        <p
          style={{
            color: "rgba(255,255,255,0.36)",
            fontSize: "0.74rem",
            lineHeight: 1.5,
            maxWidth: 640,
            marginTop: 12,
          }}
        >
          Prices for ChatGPT Plus and Claude Pro per their public pricing pages
          (May 2026). Comparison reflects core consumer plans.
        </p>
      </div>
    </section>
  );
}

function ColHeader({
  name,
  price,
  green,
}: {
  name: string;
  price: string;
  green?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span
        style={{
          color: green ? "rgba(134,239,172,0.95)" : "rgba(255,255,255,0.9)",
          fontWeight: 700,
          fontSize: "0.98rem",
        }}
      >
        {name}
      </span>
      <span
        style={{
          color: "rgba(255,255,255,0.5)",
          fontSize: "0.82rem",
        }}
      >
        {price}
      </span>
    </div>
  );
}

function Cell({ text, tone }: { text: string; tone: CellTone }) {
  const t = TONE_COLOR[tone];
  return (
    <span
      style={{
        color: t.color,
        fontWeight: t.weight,
        fontSize: "0.95rem",
      }}
    >
      {text}
    </span>
  );
}
