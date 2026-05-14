"use client";

import Link from "next/link";

export function Nav() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-[#0a0a0c]/60 border-b border-white/[0.06]">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-white to-white/70 flex items-center justify-center">
            <span className="text-black font-bold text-sm">A</span>
          </div>
          <span className="text-white font-semibold text-[15px] tracking-tight">
            Alex AI
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <Link
            href="/login"
            className="text-white/70 hover:text-white text-[14px] font-medium px-4 py-2 transition-colors"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="bg-white text-black hover:bg-white/90 text-[14px] font-semibold px-5 py-2 rounded-full transition-all hover:scale-[1.02]"
          >
            Start free
          </Link>
        </div>
      </div>
    </nav>
  );
}
