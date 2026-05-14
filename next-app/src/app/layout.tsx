import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Alex AI — Your Academic Mentor",
  description:
    "Choose your degree and let Alex AI organize your semester with planning, voice teaching, notes, tasks, and AI-powered study visuals.",
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    title: "Alex AI — Your Academic Mentor",
    description:
      "AI that teaches your full university semester day by day.",
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
      <body className="bg-[#0a0a0c] text-white">{children}</body>
    </html>
  );
}
