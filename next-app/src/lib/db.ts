import postgres from "postgres";

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  throw new Error(
    "DATABASE_URL env var is required. Get the Neon Postgres connection string from Railway -> next-app service -> Variables."
  );
}

declare global {
  // eslint-disable-next-line no-var
  var __sqlClient: ReturnType<typeof postgres> | undefined;
}

export const sql =
  globalThis.__sqlClient ??
  postgres(DATABASE_URL, {
    max: 5,
    idle_timeout: 30,
    connect_timeout: 10,
    ssl: "require",
  });

if (process.env.NODE_ENV !== "production") {
  globalThis.__sqlClient = sql;
}
