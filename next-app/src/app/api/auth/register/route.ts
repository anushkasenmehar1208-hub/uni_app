import { NextRequest, NextResponse } from "next/server";
import {
  AUTH_TOKEN_LOCAL_STORAGE_KEY,
  createSession,
  createUser,
  findUserByUsername,
  storeUserProfileEmail,
} from "@/lib/auth";

const USERNAME_REGEX = /^[a-zA-Z0-9_.-]{3,32}$/;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => null);
    const username = String(body?.username ?? "").trim();
    const email = String(body?.email ?? "").trim();
    const password = String(body?.password ?? "");

    if (!username || !email || !password) {
      return NextResponse.json(
        { error: "All fields are required." },
        { status: 400 }
      );
    }

    if (!USERNAME_REGEX.test(username)) {
      return NextResponse.json(
        {
          error:
            "Username must be 3-32 characters and only contain letters, numbers, dots, dashes, or underscores.",
        },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: "Password must be at least 8 characters." },
        { status: 400 }
      );
    }

    const existing = await findUserByUsername(username);
    if (existing) {
      return NextResponse.json(
        { error: "That username is already taken." },
        { status: 409 }
      );
    }

    const user = await createUser(username, password);
    await storeUserProfileEmail(user.id, email);
    const sessionId = await createSession(user.id);

    const res = NextResponse.json({
      ok: true,
      token: sessionId,
      tokenKey: AUTH_TOKEN_LOCAL_STORAGE_KEY,
    });

    res.cookies.set(AUTH_TOKEN_LOCAL_STORAGE_KEY, sessionId, {
      httpOnly: false,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 7 * 24 * 60 * 60,
      path: "/",
    });

    return res;
  } catch (err) {
    console.error("[register] error:", err);
    return NextResponse.json(
      { error: "Something went wrong. Try again." },
      { status: 500 }
    );
  }
}
