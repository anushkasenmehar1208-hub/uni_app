import bcrypt from "bcryptjs";
import { createHash, randomBytes } from "crypto";
import { sql } from "./db";

const SESSION_EXPIRATION_DAYS = 7;
const GUEST_USER_ID_BASE = 1_500_000_000;
const GUEST_USER_ID_SPAN = 450_000_000;

export const AUTH_TOKEN_LOCAL_STORAGE_KEY = "_auth_token";
export const GUEST_TOKEN_LOCAL_STORAGE_KEY = "alex_guest_token";

export interface LocalUser {
  id: number;
  username: string;
  password_hash: Buffer;
  enabled: boolean;
}

export async function findUserByUsername(
  username: string
): Promise<LocalUser | null> {
  const rows = await sql<LocalUser[]>`
    SELECT id, username, password_hash, enabled
    FROM localuser
    WHERE LOWER(username) = LOWER(${username})
    LIMIT 1
  `;
  return rows[0] ?? null;
}

export async function verifyPassword(
  user: LocalUser,
  candidate: string
): Promise<boolean> {
  // password_hash from Postgres bytea is returned as a Buffer of UTF-8
  // bytes containing the bcrypt hash string (e.g. "$2b$12$...").
  const hashString = user.password_hash.toString("utf-8");
  return bcrypt.compare(candidate, hashString);
}

export async function hashPassword(password: string): Promise<Buffer> {
  const hash = await bcrypt.hash(password, 12);
  return Buffer.from(hash, "utf-8");
}

export async function createUser(
  username: string,
  password: string
): Promise<LocalUser> {
  const password_hash = await hashPassword(password);
  const rows = await sql<LocalUser[]>`
    INSERT INTO localuser (username, password_hash, enabled)
    VALUES (${username}, ${password_hash}, true)
    RETURNING id, username, password_hash, enabled
  `;
  return rows[0];
}

export async function storeUserProfileEmail(
  userId: number,
  email: string
): Promise<void> {
  const normalized = email.trim().toLowerCase();
  if (!normalized) return;
  await sql`
    INSERT INTO userprofile (user_id, email, is_onboarded, unique_id, is_pro, is_premium_1, is_premium_2, plan_tier, model_usage_json, daily_message_count)
    VALUES (${userId}, ${normalized}, false, '', false, false, false, 'free', '{}', 0)
    ON CONFLICT (user_id) DO UPDATE SET email = EXCLUDED.email
  `;
}

export async function createSession(userId: number): Promise<string> {
  // Generate a URL-safe token matching the format Reflex uses.
  const sessionId = randomBytes(32).toString("base64url");
  const expiration = new Date(
    Date.now() + SESSION_EXPIRATION_DAYS * 24 * 60 * 60 * 1000
  );
  await sql`
    INSERT INTO localauthsession (user_id, session_id, expiration)
    VALUES (${userId}, ${sessionId}, ${expiration})
  `;
  return sessionId;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await sql`DELETE FROM localauthsession WHERE session_id = ${sessionId}`;
}

export async function getSessionUserId(
  sessionId: string
): Promise<number | null> {
  const rows = await sql<{ user_id: number }[]>`
    SELECT user_id
    FROM localauthsession
    WHERE session_id = ${sessionId}
      AND expiration > NOW()
    LIMIT 1
  `;
  return rows[0]?.user_id ?? null;
}

function guestUidFromToken(guestToken: string): number | null {
  const raw = guestToken.trim();
  let cleaned = raw;
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (typeof parsed === "string") cleaned = parsed.trim();
  } catch {}
  if (!cleaned) return null;

  const digest = createHash("sha256")
    .update(`alex-guest:${cleaned}`, "utf8")
    .digest("hex");
  const offset = Number.parseInt(digest.slice(0, 12), 16) % GUEST_USER_ID_SPAN;
  return GUEST_USER_ID_BASE + offset;
}

export async function migrateGuestMemoryToUser(
  guestToken: string | null | undefined,
  userId: number
): Promise<void> {
  const guestUid = guestUidFromToken(String(guestToken ?? ""));
  if (!guestUid || guestUid === userId) return;

  await sql.begin(async (tx) => {
    const guestRows = await tx<
      {
        step: number;
        name: string;
        degree: string;
        pathway: string;
        active_subject: string;
        is_started: boolean;
        selected_year: string;
        selected_semester: string;
        summary: string;
        other_degree_text: string;
      }[]
    >`
      SELECT step, name, degree, pathway, active_subject, is_started,
             selected_year, selected_semester, summary, other_degree_text
      FROM usermemory
      WHERE user_id = ${guestUid}
      LIMIT 1
    `;
    const guestMemory = guestRows[0];
    if (!guestMemory) return;

    const realRows = await tx<{ user_id: number; is_started: boolean }[]>`
      SELECT user_id, is_started
      FROM usermemory
      WHERE user_id = ${userId}
      LIMIT 1
    `;
    const realMemory = realRows[0];

    if (!realMemory) {
      await tx`
        UPDATE usermemory
        SET user_id = ${userId}
        WHERE user_id = ${guestUid}
      `;
    } else {
      if (guestMemory.is_started || !realMemory.is_started) {
        await tx`
          UPDATE usermemory
          SET step = ${guestMemory.step},
              name = ${guestMemory.name},
              degree = ${guestMemory.degree},
              pathway = ${guestMemory.pathway},
              active_subject = ${guestMemory.active_subject},
              is_started = ${guestMemory.is_started},
              selected_year = ${guestMemory.selected_year},
              selected_semester = ${guestMemory.selected_semester},
              other_degree_text = ${guestMemory.other_degree_text},
              updated_at = NOW()
          WHERE user_id = ${userId}
        `;
      }

      if (guestMemory.summary.trim()) {
        await tx`
          UPDATE usermemory
          SET summary = ${guestMemory.summary},
              updated_at = NOW()
          WHERE user_id = ${userId}
        `;
      }

      await tx`DELETE FROM usermemory WHERE user_id = ${guestUid}`;
    }

    if (guestMemory.is_started) {
      await tx`
        UPDATE userprofile
        SET is_onboarded = true
        WHERE user_id = ${userId}
      `;
    }
  });
}
