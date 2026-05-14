import Link from "next/link";

interface Plan {
  badge?: string;
  title: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  guarantee?: string;
  ctaLabel: string;
  ctaHref: string;
  accent: "default" | "pro";
}

const FREE: Plan = {
  title: "Free",
  price: "USD 0",
  period: "starter",
  description:
    "Start with Alex AI, build your study workspace, and test the academic mentor before upgrading.",
  features: [
    "3-day trial for new users",
    "10 free messages/day after trial",
    "Auto model routing",
    "Basic workspace access",
  ],
  ctaLabel: "Start Free",
  ctaHref: "/register",
  accent: "default",
};

const PRO: Plan = {
  badge: "Best for daily studying",
  title: "Pro",
  price: "USD 3",
  period: "/ month",
  description:
    "The full everyday student workspace for guided study, planner tools, and voice-supported learning.",
  features: [
    "Unlimited daily messages",
    "Full semester planner access",
    "Auto model routing for every chat",
    "45 min/day voice mentor limit",
    "Notes, tasks, YouTube learning with quizzes, and more",
  ],
  guarantee: "7-day money-back guarantee",
  ctaLabel: "Upgrade to Pro",
  ctaHref: "/pricing",
  accent: "pro",
};

export function Pricing() {
  return (
    <section
      id="landing-pricing-section"
      className="relative w-full"
      style={{ padding: "104px 16px 0", zIndex: 4 }}
    >
      <div
        className="mx-auto flex flex-col items-center text-center gap-4 mb-12"
        style={{ maxWidth: 1280 }}
      >
        <span
          style={{
            color: "rgba(255,255,255,0.44)",
            fontSize: "0.78rem",
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          PRICING
        </span>
        <h2
          className="landing-heading"
          style={{ fontSize: "clamp(2.55rem, 3vw, 3.5rem)" }}
        >
          Start free. Upgrade when Alex becomes your daily study tool.
        </h2>
        <p
          className="landing-sub"
          style={{ maxWidth: 700, lineHeight: 1.75 }}
        >
          Built for university students who want a smarter way to plan and
          study.
        </p>
      </div>

      <div
        className="mx-auto flex flex-wrap justify-center gap-5"
        style={{ maxWidth: 1080 }}
      >
        <PricingCard plan={FREE} />
        <PricingCard plan={PRO} />
      </div>
    </section>
  );
}

function PricingCard({ plan }: { plan: Plan }) {
  const isPro = plan.accent === "pro";
  return (
    <article
      className="relative flex flex-col w-full sm:w-[calc(50%-10px)]"
      style={{
        minHeight: 500,
        padding: 24,
        border: `1px solid ${isPro ? "rgba(94,211,132,0.36)" : "rgba(255,255,255,0.08)"}`,
        borderRadius: 24,
        background: isPro
          ? "radial-gradient(circle at 50% 0%, rgba(74,222,128,0.10) 0%, transparent 60%), linear-gradient(180deg, rgba(255,255,255,0.065) 0%, rgba(255,255,255,0.025) 100%)"
          : "radial-gradient(circle at 50% 0%, rgba(255,255,255,0.04) 0%, transparent 60%), linear-gradient(180deg, rgba(255,255,255,0.065) 0%, rgba(255,255,255,0.025) 100%)",
        boxShadow: "0 24px 70px rgba(0,0,0,0.36)",
      }}
    >
      {plan.badge && (
        <div
          className="absolute"
          style={{
            top: -12,
            left: "50%",
            transform: "translateX(-50%)",
            padding: "6px 14px",
            borderRadius: 999,
            background: "linear-gradient(180deg, #bbf7d0 0%, #86efac 100%)",
            color: "rgba(10,14,11,0.9)",
            fontSize: "0.74rem",
            fontWeight: 800,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            whiteSpace: "nowrap",
          }}
        >
          {plan.badge}
        </div>
      )}

      <div className="flex flex-col gap-2 mt-2">
        <h3
          style={{
            color: "rgba(255,255,255,0.95)",
            fontSize: "1.5rem",
            fontWeight: 700,
            margin: 0,
          }}
        >
          {plan.title}
        </h3>
        <div className="flex items-baseline gap-1.5">
          <span
            style={{
              color: "rgba(255,255,255,0.98)",
              fontSize: "2.4rem",
              fontWeight: 700,
              lineHeight: 1,
            }}
          >
            {plan.price}
          </span>
          <span
            style={{
              color: "rgba(255,255,255,0.5)",
              fontSize: "0.96rem",
              fontWeight: 500,
            }}
          >
            {plan.period}
          </span>
        </div>
        <p
          style={{
            color: "rgba(255,255,255,0.56)",
            fontSize: "0.95rem",
            lineHeight: 1.65,
            margin: "8px 0 0",
          }}
        >
          {plan.description}
        </p>
      </div>

      <ul className="flex flex-col gap-2.5 mt-6 mb-6 flex-1">
        {plan.features.map((feature) => (
          <li
            key={feature}
            className="flex items-start gap-2.5"
            style={{
              color: "rgba(255,255,255,0.86)",
              fontSize: "0.95rem",
              lineHeight: 1.55,
            }}
          >
            <span
              aria-hidden
              style={{
                color: "rgba(231,182,157,0.8)",
                fontWeight: 700,
                lineHeight: 1.55,
              }}
            >
              •
            </span>
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      {plan.guarantee && (
        <div
          className="flex items-center gap-2"
          style={{
            color: "rgba(255,255,255,0.82)",
            fontSize: "0.9rem",
            fontWeight: 600,
            marginBottom: 14,
          }}
        >
          <span style={{ color: "rgba(134,239,172,0.92)" }}>✓</span>
          {plan.guarantee}
        </div>
      )}

      <Link
        href={plan.ctaHref}
        className="w-full text-center"
        style={{
          padding: "14px 22px",
          borderRadius: 999,
          background: isPro
            ? "linear-gradient(180deg, #f7f4ed 0%, #ebe4d7 100%)"
            : "rgba(255,255,255,0.045)",
          color: isPro ? "#1c1915" : "rgba(255,255,255,0.88)",
          fontWeight: isPro ? 750 : 650,
          fontSize: "0.96rem",
          textDecoration: "none",
          boxShadow: isPro
            ? "0 18px 46px rgba(0,0,0,0.44), 0 1px 0 rgba(255,255,255,0.45) inset"
            : "0 10px 30px rgba(0,0,0,0.25)",
          border: isPro
            ? "1px solid rgba(255,255,255,0.16)"
            : "1px solid rgba(255,255,255,0.08)",
        }}
      >
        {plan.ctaLabel}
      </Link>

      {isPro && (
        <p
          className="text-center mt-3"
          style={{
            color: "rgba(255,255,255,0.54)",
            fontSize: "0.84rem",
            fontWeight: 650,
            margin: "12px 0 0",
          }}
        >
          Cancel anytime
        </p>
      )}
    </article>
  );
}
