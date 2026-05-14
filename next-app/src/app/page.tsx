import { BackgroundLayers } from "@/components/landing/BackgroundLayers";
import { Nav } from "@/components/landing/Nav";
import { Hero } from "@/components/landing/Hero";
import { DemoWidget } from "@/components/landing/DemoWidget";
import { Story } from "@/components/landing/Story";
import { Voice } from "@/components/landing/Voice";
import { Features } from "@/components/landing/Features";
import { Founder } from "@/components/landing/Founder";
import { Comparison } from "@/components/landing/Comparison";
import { Pricing } from "@/components/landing/Pricing";
import { FAQ } from "@/components/landing/FAQ";
import { Footer } from "@/components/landing/Footer";

export default function HomePage() {
  return (
    <main
      className="relative min-h-screen"
      style={{ background: "#000000", overflowX: "hidden" }}
    >
      <BackgroundLayers />
      <div className="relative" style={{ zIndex: 4 }}>
        <Nav />
        <Hero />
        <DemoWidget />
        <Story />
        <Voice />
        <Features />
        <Founder />
        <Comparison />
        <Pricing />
        <FAQ />
        <Footer />
      </div>
    </main>
  );
}
