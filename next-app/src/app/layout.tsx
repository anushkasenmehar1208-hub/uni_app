import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  display: "swap",
});

const websiteJsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "Alex Studies",
  alternateName: "Alex AI",
  url: "https://alexstudies.com/",
};

export const metadata: Metadata = {
  title: {
    default: "Alex Studies",
    template: "%s | Alex Studies",
  },
  description:
    "Alex Studies helps students plan their semester, organize study tasks, learn with AI guidance, and stay on track day by day.",
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    title: "Alex Studies",
    description:
      "Student-focused AI study planning, tutoring, notes, and tasks in one workspace.",
    siteName: "Alex Studies",
    url: "https://alexstudies.com/",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${jakarta.variable} antialiased`}
      style={{ colorScheme: "dark" }}
    >
      <body className="bg-[#0a0a0c] text-white">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(websiteJsonLd).replace(/</g, "\\u003c"),
          }}
        />
        {children}
      </body>
    </html>
  );
}
