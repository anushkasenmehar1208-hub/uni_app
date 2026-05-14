import Link from "next/link";

const STUDY_PLAN_LINKS: { label: string; href: string }[] = [
  { label: "AI Study Planner", href: "/ai-study-planner-for-university-students" },
  { label: "UK Computer Science", href: "/uk-computer-science-study-plan" },
  { label: "UK Software Engineering", href: "/uk-software-engineering-study-plan" },
  { label: "US Computer Science", href: "/us-computer-science-study-plan" },
  { label: "US Software Engineering", href: "/us-software-engineering-study-plan" },
  { label: "Sri Lanka Software Engineering", href: "/sri-lanka-software-engineering-study-plan" },
  { label: "Sri Lanka BECS", href: "/sri-lanka-becs-study-plan" },
  { label: "Sri Lanka Physical Science", href: "/sri-lanka-physical-science-study-plan" },
  { label: "Sri Lanka Biological Science", href: "/sri-lanka-biological-science-study-plan" },
  { label: "India B.Tech Computer Science", href: "/india-btech-computer-science-study-plan" },
  { label: "India B.Tech Information Technology", href: "/india-btech-information-technology-study-plan" },
];

const RESOURCE_LINKS: { label: string; href: string }[] = [
  { label: "Support", href: "/support" },
  { label: "Contact", href: "/support" },
  { label: "Privacy", href: "/privacy-policy" },
  { label: "Terms", href: "/terms" },
  { label: "Refund Policy", href: "/return-policy" },
  { label: "See Alex", href: "/register" },
];

export function Footer() {
  return (
    <footer
      className="relative w-full mt-24"
      style={{ zIndex: 4 }}
    >
      <div
        className="mx-auto flex flex-wrap gap-10"
        style={{
          maxWidth: 1120,
          padding: "56px 28px 48px",
        }}
      >
        <div
          className="flex flex-col gap-3"
          style={{ width: 260, flexShrink: 0 }}
        >
          <span
            style={{
              color: "rgba(255,255,255,0.88)",
              fontSize: "1.08rem",
              fontWeight: 800,
              fontFamily: "'Plus Jakarta Sans', 'Space Grotesk', sans-serif",
            }}
          >
            Alex AI
          </span>
          <span
            style={{
              color: "rgba(255,255,255,0.48)",
              fontSize: "0.9rem",
              lineHeight: 1.6,
            }}
          >
            AI-powered study platform
          </span>
          <a
            href="mailto:support.alexstudies@gmail.com"
            style={{
              color: "rgba(255,255,255,0.46)",
              fontSize: "0.9rem",
              textDecoration: "none",
            }}
            className="hover:!text-white/85 transition-colors"
          >
            support.alexstudies@gmail.com
          </a>
        </div>

        <div className="flex-1 min-w-[240px]">
          <h4
            style={{
              color: "rgba(255,255,255,0.82)",
              fontSize: "0.92rem",
              fontWeight: 700,
              marginBottom: 14,
            }}
          >
            Study Plans
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-y-2 gap-x-6">
            {STUDY_PLAN_LINKS.map((l) => (
              <FootLink key={l.href} {...l} />
            ))}
          </div>
        </div>

        <div style={{ width: 180, flexShrink: 0 }}>
          <h4
            style={{
              color: "rgba(255,255,255,0.82)",
              fontSize: "0.92rem",
              fontWeight: 700,
              marginBottom: 14,
            }}
          >
            Resources
          </h4>
          <div className="flex flex-col gap-2">
            {RESOURCE_LINKS.map((l) => (
              <FootLink key={l.label} {...l} />
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}

function FootLink({ label, href }: { label: string; href: string }) {
  return (
    <Link
      href={href}
      style={{
        color: "rgba(255,255,255,0.52)",
        fontSize: "0.95rem",
        fontWeight: 500,
        textDecoration: "none",
      }}
      className="hover:!text-white/90 transition-colors"
    >
      {label}
    </Link>
  );
}
