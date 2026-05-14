import Link from "next/link";

export function Footer() {
  return (
    <footer className="relative border-t border-white/[0.06] mt-20">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-white to-white/70 flex items-center justify-center">
              <span className="text-black font-bold text-sm">A</span>
            </div>
            <span className="text-white font-semibold text-[15px]">Alex AI</span>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-[0.92rem] text-white/52">
            <Link
              href="/refund"
              className="hover:text-white/80 transition-colors"
            >
              Refund & Cancellation
            </Link>
            <Link
              href="/privacy"
              className="hover:text-white/80 transition-colors"
            >
              Privacy Policy
            </Link>
            <Link
              href="/terms"
              className="hover:text-white/80 transition-colors"
            >
              Terms
            </Link>
            <Link
              href="/support"
              className="hover:text-white/80 transition-colors"
            >
              Support
            </Link>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-white/[0.04] text-center text-white/40 text-[0.85rem]">
          © {new Date().getFullYear()} Alex AI. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
