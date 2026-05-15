import postgres from "postgres";

declare global {
  // eslint-disable-next-line no-var
  var __sqlClient: ReturnType<typeof postgres> | undefined;
}

function getClient(): ReturnType<typeof postgres> {
  if (globalThis.__sqlClient) return globalThis.__sqlClient;
  const DATABASE_URL = process.env.DATABASE_URL;
  if (!DATABASE_URL) {
    throw new Error(
      "DATABASE_URL env var is required. Get the Neon Postgres connection string from Railway -> next-app service -> Variables."
    );
  }
  const client = postgres(DATABASE_URL, {
    max: 5,
    idle_timeout: 30,
    connect_timeout: 10,
    ssl: "require",
  });
  globalThis.__sqlClient = client;
  return client;
}

const fnTarget = (() => {}) as unknown as ReturnType<typeof postgres>;

export const sql = new Proxy(fnTarget, {
  apply(_target, _thisArg, args: unknown[]) {
    const client = getClient() as unknown as (...a: unknown[]) => unknown;
    return client(...args);
  },
  get(_target, prop) {
    const client = getClient() as unknown as Record<string | symbol, unknown>;
    const value = client[prop];
    return typeof value === "function" ? (value as Function).bind(client) : value;
  },
}) as ReturnType<typeof postgres>;
