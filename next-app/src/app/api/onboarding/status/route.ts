export const dynamic = "force-dynamic";

import { NextRequest, NextResponse } from "next/server";
import { AUTH_TOKEN_LOCAL_STORAGE_KEY, getSessionUserId } from "@/lib/auth";
import { getOnboardingState } from "@/lib/onboarding";

// Debug endpoint: returns the current user's UserProfile/UserMemory
// state so we can verify whether onboarding writes are landing.
function readToken(req: NextRequest): string | null {
  const fromCookie = req.cookies.get(AUTH_TOKEN_LOCAL_STORAGE_KEY)?.value;
  if (fromCookie) return fromCookie;
  const auth = req.headers.get("authorization") ?? "";
  const match = auth.match(/^Bearer\s+(.+)$/i);
  return match ? match[1].trim() : null;
}

export async function GET(req: NextRequest) {
  const sessionId = readToken(req);
  if (!sessionId) {
    return NextResponse.json(
      { error: "no token in cookie or header" },
      { status: 401 }
    );
  }
  const userId = await getSessionUserId(sessionId);
  if (!userId) {
    return NextResponse.json({ error: "session expired" }, { status: 401 });
  }

  const onboarding = await getOnboardingState(userId);

  return NextResponse.json({
    user_id: userId,
    memory: onboarding.memory,
    profile: onboarding.profile,
    redirectTo: onboarding.redirectTo,
  });
}
