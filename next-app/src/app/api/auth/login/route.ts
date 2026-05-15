export const dynamic = "force-dynamic";

import { NextRequest, NextResponse } from "next/server";
import {
  AUTH_TOKEN_LOCAL_STORAGE_KEY,
  createSession,
  findUserByUsername,
  verifyPassword,
} from "@/lib/auth";
import { getOnboardingState } from "@/lib/onboarding";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => null);
    const username = String(body?.username ?? "").trim();
    const password = String(body?.password ?? "");

    if (!username || !password) {
      return NextResponse.json(
        { error: "Username and password are required." },
        { status: 400 }
      );
    }

    const user = await findUserByUsername(username);
    if (!user || !user.enabled) {
      return NextResponse.json(
        { error: "Invalid username or password." },
        { status: 401 }
      );
    }

    const ok = await verifyPassword(user, password);
    if (!ok) {
      return NextResponse.json(
        { error: "Invalid username or password." },
        { status: 401 }
      );
    }

    const sessionId = await createSession(user.id);
    const onboarding = await getOnboardingState(user.id);

    const res = NextResponse.json({
      ok: true,
      token: sessionId,
      tokenKey: AUTH_TOKEN_LOCAL_STORAGE_KEY,
      redirectTo: onboarding.redirectTo ?? "/app",
    });

    // Also set as a cookie for any server-side Next.js auth checks.
    res.cookies.set(AUTH_TOKEN_LOCAL_STORAGE_KEY, sessionId, {
      httpOnly: false, // false so Reflex localStorage sync works
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 7 * 24 * 60 * 60,
      path: "/",
    });

    return res;
  } catch (err) {
    console.error("[login] error:", err);
    return NextResponse.json(
      { error: "Something went wrong. Try again." },
      { status: 500 }
    );
  }
}
