import { sql } from "./db";

export interface OnboardingMemory {
  step: number;
  degree: string;
  pathway: string;
  is_started: boolean;
  selected_year: string;
  selected_semester: string;
}

export interface OnboardingProfile {
  is_onboarded: boolean;
}

function extractNumber(value: string): string | null {
  return value.match(/\d+/)?.[0] ?? null;
}

export function onboardingRedirectForMemory(
  memory: OnboardingMemory | null
): string | null {
  if (!memory?.is_started) return null;

  const degree = memory.degree.trim();
  if (degree === "Custom" || degree === "Others") {
    return "/free";
  }

  const year = extractNumber(memory.selected_year);
  const semester = extractNumber(memory.selected_semester);
  if (year && semester) {
    return `/s/y${year}s${semester}`;
  }

  return null;
}

export async function getOnboardingState(userId: number): Promise<{
  memory: OnboardingMemory | null;
  profile: OnboardingProfile | null;
  redirectTo: string | null;
}> {
  const memoryRows = await sql<OnboardingMemory[]>`
    SELECT step, degree, pathway, is_started, selected_year, selected_semester
    FROM usermemory
    WHERE user_id = ${userId}
    LIMIT 1
  `;

  const profileRows = await sql<OnboardingProfile[]>`
    SELECT is_onboarded FROM userprofile WHERE user_id = ${userId} LIMIT 1
  `;

  const memory = memoryRows[0] ?? null;
  const profile = profileRows[0] ?? null;

  return {
    memory,
    profile,
    redirectTo: onboardingRedirectForMemory(memory),
  };
}
