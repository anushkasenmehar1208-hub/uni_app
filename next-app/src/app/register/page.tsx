"use client";

import Link from "next/link";
import { useState } from "react";
import { AuthCard } from "@/components/auth/AuthCard";
import { GoogleButton } from "@/components/auth/GoogleButton";
import { Eye, EyeOff, Check } from "lucide-react";

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const passwordChecks = [
    { label: "At least 8 characters", valid: password.length >= 8 },
    { label: "Has a number", valid: /\d/.test(password) },
    { label: "Has a letter", valid: /[a-zA-Z]/.test(password) },
  ];
  const passwordValid = passwordChecks.every((c) => c.valid);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!passwordValid) {
      setError("Password doesn't meet the requirements.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.token) {
        try {
          localStorage.setItem(data.tokenKey, JSON.stringify(data.token));
        } catch {}
        window.location.href = "/onboarding";
      } else {
        setError(data.error || "Couldn't create your account. Try again.");
      }
    } catch {
      setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard
      title="Create your account"
      footer={
        <>
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-white hover:text-white/80 font-medium underline-offset-4 hover:underline"
          >
            Sign in
          </Link>
        </>
      }
    >
      <div className="space-y-5">
        <GoogleButton label="Continue with Google" />

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
              minLength={3}
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="alex.doe"
              className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-white/[0.2] rounded-xl px-4 py-3 text-white placeholder:text-white/30 text-[0.95rem] outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-white/64 text-[0.85rem] mb-1.5 font-medium">
              Email
            </label>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@university.edu"
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
                autoComplete="new-password"
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
            {password.length > 0 && (
              <div className="mt-2.5 space-y-1.5">
                {passwordChecks.map((c) => (
                  <div
                    key={c.label}
                    className={`flex items-center gap-2 text-[0.82rem] transition-colors ${
                      c.valid ? "text-emerald-400" : "text-white/40"
                    }`}
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{c.label}</span>
                  </div>
                ))}
              </div>
            )}
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
            {loading ? "Creating account..." : "Create account"}
          </button>

          <p className="text-center text-white/40 text-[0.78rem] leading-relaxed">
            By signing up you agree to our{" "}
            <Link href="/terms" className="text-white/60 hover:text-white/80 underline-offset-4 hover:underline">
              Terms
            </Link>{" "}
            &{" "}
            <Link href="/privacy" className="text-white/60 hover:text-white/80 underline-offset-4 hover:underline">
              Privacy Policy
            </Link>
          </p>
        </form>
      </div>
    </AuthCard>
  );
}
