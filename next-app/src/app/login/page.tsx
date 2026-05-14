"use client";

import Link from "next/link";
import { useState } from "react";
import { AuthCard } from "@/components/auth/AuthCard";
import { GoogleButton } from "@/components/auth/GoogleButton";
import { Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (res.ok) {
        window.location.href = "/app";
      } else {
        const data = await res.json().catch(() => ({}));
        setError(data.error || "Invalid username or password.");
      }
    } catch {
      setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard
      title="Welcome back"
      subtitle="Continue your study plan with Alex"
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="text-white hover:text-white/80 font-medium underline-offset-4 hover:underline"
          >
            Sign up
          </Link>
        </>
      }
    >
      <div className="space-y-5">
        <GoogleButton />

        <div className="flex items-center gap-3 text-white/40 text-[0.82rem]">
          <div className="h-px flex-1 bg-white/[0.06]" />
          <span>or</span>
          <div className="h-px flex-1 bg-white/[0.06]" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-white/64 text-[0.85rem] mb-1.5 font-medium">
              Username
            </label>
            <input
              type="text"
              required
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="alex.doe"
              className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-white/[0.2] rounded-xl px-4 py-3 text-white placeholder:text-white/30 text-[0.95rem] outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-white/64 text-[0.85rem] mb-1.5 font-medium">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-white/[0.2] rounded-xl px-4 py-3 pr-11 text-white placeholder:text-white/30 text-[0.95rem] outline-none transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white/80 transition-colors p-1"
              >
                {showPassword ? (
                  <EyeOff className="w-4.5 h-4.5" />
                ) : (
                  <Eye className="w-4.5 h-4.5" />
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="text-red-400 text-[0.88rem] bg-red-500/[0.08] border border-red-500/20 rounded-xl px-3.5 py-2.5">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white hover:bg-white/95 text-black font-semibold text-[14.5px] py-3 rounded-full transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>

          <div className="text-center">
            <Link
              href="/forgot-password"
              className="text-white/52 hover:text-white/80 text-[0.88rem] transition-colors"
            >
              Forgot password?
            </Link>
          </div>
        </form>
      </div>
    </AuthCard>
  );
}
