"use client";

import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import AboutUs from "@/components/AboutUs";
import HowItWorks from "@/components/HowItWorks";
import FAQ from "@/components/FAQ";
import Footer from "@/components/Footer";
import Reveal from "@/components/ui/Reveal";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)] text-[var(--foreground)]">
      <Navbar />

        <main className="flex-1 space-y-4">
          <Reveal><Hero /></Reveal>
          <Reveal delay={80}><AboutUs /></Reveal>
          <Reveal delay={140}><HowItWorks /></Reveal>
          <Reveal delay={200}><FAQ /></Reveal>
        </main>

      <Footer />
    </div>
  );
}
