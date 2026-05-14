export const dynamic = "force-dynamic";

import { NextRequest, NextResponse } from "next/server";
import { AUTH_TOKEN_LOCAL_STORAGE_KEY, getSessionUserId } from "@/lib/auth";
import { sql } from "@/lib/db";

// Map Next.js onboarding degree codes to the canonical Reflex degree
// names in REGION_DEGREE_OPTIONS (uni_app.py). Mismatched names cause
// Reflex to treat the user as un-onboarded.
const DEGREE_CODE_TO_REFLEX_NAME: Record<string, string> = {
  // Sri Lanka
  se: "Software Engineering",
  elcs: "Electronics and Computer Science (BECS)",
  ps: "Physical Science",
  bs: "Biological Science",
  // UK / US — Next.js uses generic "cs" / "se" with country context
  "cs-uk": "Computer Science (UK)",
  "se-uk": "Software Engineering (UK)",
  "cs-us": "Computer Science (US)",
  "se-us": "Software Engineering (US)",
  // India
  "btech-cs": "B.Tech Computer Science",
  "btech-it": "B.Tech Information Technology",
};

const ONBOARDING_FINAL_STEP = 6;

function resolveDegreeName(country: string, degree: string): string {
  const direct = DEGREE_CODE_TO_REFLEX_NAME[degree];
  if (direct) return direct;
  // UK/US share the generic "cs" / "se" codes — disambiguate by country.
  const compound = `${degree}-${country}`;
  return DEGREE_CODE_TO_REFLEX_NAME[compound] ?? "Custom";
}

function semesterToYear(semester: string): string {
  const match = semester.match(/(\d+)/);
  if (!match) return "Year 1";
  const n = parseInt(match[1], 10);
  if (n <= 2) return "Year 1";
  if (n <= 4) return "Year 2";
  if (n <= 6) return "Year 3";
  return "Year 4";
}

export async function POST(req: NextRequest) {
  try {
    const sessionId = req.cookies.get(AUTH_TOKEN_LOCAL_STORAGE_KEY)?.value;
    if (!sessionId) {
      return NextResponse.json(
        { error: "Not authenticated." },
        { status: 401 }
      );
    }

    const userId = await getSessionUserId(sessionId);
    if (!userId) {
      return NextResponse.json(
        { error: "Session expired." },
        { status: 401 }
      );
    }

    const body = await req.json().catch(() => null);
    const country = String(body?.country ?? "").trim().toLowerCase();
    const degree = String(body?.degree ?? "").trim();
    const pathway = body?.pathway ? String(body.pathway).trim() : "";
    const semester = String(body?.semester ?? "").trim();

    if (!country || !degree || !semester) {
      return NextResponse.json(
        { error: "country, degree, and semester are required." },
        { status: 400 }
      );
    }

    const reflexDegree = resolveDegreeName(country, degree);
    const year = semesterToYear(semester);

    await sql`
      INSERT INTO usermemory
        (user_id, step, name, degree, pathway, is_started,
         selected_year, selected_semester, summary, other_degree_text)
      VALUES
        (${userId}, ${ONBOARDING_FINAL_STEP}, '', ${reflexDegree}, ${pathway}, true,
         ${year}, ${semester}, '', '')
      ON CONFLICT (user_id) DO UPDATE SET
        step = EXCLUDED.step,
        degree = EXCLUDED.degree,
        pathway = EXCLUDED.pathway,
        is_started = EXCLUDED.is_started,
        selected_year = EXCLUDED.selected_year,
        selected_semester = EXCLUDED.selected_semester,
        updated_at = NOW()
    `;

    await sql`
      UPDATE userprofile
      SET is_onboarded = true
      WHERE user_id = ${userId}
    `;

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("[onboarding/complete] error:", err);
    return NextResponse.json(
      { error: "Something went wrong saving onboarding." },
      { status: 500 }
    );
  }
}
