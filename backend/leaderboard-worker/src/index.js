const enc = new TextEncoder();
let schemaPromise = null;

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...extra,
    },
  });
}

function corsInfo(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = String(env.ALLOWED_ORIGIN || "https://qw0w.github.io")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
  const ok = !origin || allowed.includes(origin);
  const allowOrigin = origin && ok ? origin : allowed[0] || "*";
  return {
    ok,
    headers: {
      "access-control-allow-origin": allowOrigin,
      "access-control-allow-methods": "POST,GET,OPTIONS",
      "access-control-allow-headers": "content-type",
      "access-control-max-age": "86400",
      vary: "Origin",
    },
  };
}

async function hmac(keyBytes, data) {
  const key = await crypto.subtle.importKey(
    "raw",
    keyBytes,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return new Uint8Array(await crypto.subtle.sign("HMAC", key, enc.encode(data)));
}

function hex(bytes) {
  return [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function timingSafeHexEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function validateInitData(raw, botToken, maxAgeSeconds) {
  if (!raw || typeof raw !== "string") throw new Error("missing_init_data");
  if (!botToken) throw new Error("server_not_configured");

  const params = new URLSearchParams(raw);
  const receivedHash = params.get("hash");
  if (!receivedHash) throw new Error("missing_hash");

  const pairs = [];
  for (const [key, value] of params.entries()) {
    if (key === "hash") continue;
    pairs.push(`${key}=${value}`);
  }
  pairs.sort();
  const dataCheckString = pairs.join("\n");

  const secretKey = await hmac(enc.encode("WebAppData"), botToken);
  const calculatedHash = hex(await hmac(secretKey, dataCheckString));
  if (!timingSafeHexEqual(calculatedHash, receivedHash.toLowerCase())) {
    throw new Error("bad_signature");
  }

  const authDate = Number(params.get("auth_date") || 0);
  const now = Math.floor(Date.now() / 1000);
  const maxAge = Math.max(300, Number(maxAgeSeconds || 86400));
  if (!Number.isFinite(authDate) || authDate <= 0) throw new Error("bad_auth_date");
  if (authDate > now + 300 || now - authDate > maxAge) throw new Error("expired_init_data");

  let user;
  try {
    user = JSON.parse(params.get("user") || "null");
  } catch {
    throw new Error("bad_user");
  }
  if (!user || !Number.isSafeInteger(Number(user.id)) || Number(user.id) <= 0) {
    throw new Error("missing_user");
  }
  return user;
}

async function ensureSchema(env) {
  if (!env.DB) throw new Error("missing_d1_binding");
  if (!schemaPromise) {
    schemaPromise = env.DB.batch([
      env.DB.prepare(`
        CREATE TABLE IF NOT EXISTS leaderboard_players (
          telegram_id TEXT PRIMARY KEY,
          username TEXT,
          display_name TEXT NOT NULL,
          best_score INTEGER NOT NULL DEFAULT 0,
          score_updated_at INTEGER NOT NULL,
          seen_at INTEGER NOT NULL
        )
      `),
      env.DB.prepare(`
        CREATE INDEX IF NOT EXISTS idx_leaderboard_score
        ON leaderboard_players(best_score DESC, score_updated_at ASC)
      `),
    ]).catch((error) => {
      schemaPromise = null;
      throw error;
    });
  }
  return schemaPromise;
}

function identityFromUser(user) {
  const id = String(user.id);
  const username = typeof user.username === "string" ? user.username.slice(0, 64) : null;
  const first = typeof user.first_name === "string" ? user.first_name.trim() : "";
  const last = typeof user.last_name === "string" ? user.last_name.trim() : "";
  const full = [first, last].filter(Boolean).join(" ").slice(0, 80);
  const displayName = full || (username ? `@${username}` : `Player ${id.slice(-6)}`);
  return { id, username, displayName };
}

function cleanScore(value) {
  const n = Number(value);
  if (!Number.isInteger(n) || n < 0 || n > 100000) throw new Error("bad_score");
  return n;
}

async function upsertPlayer(env, user, score) {
  const p = identityFromUser(user);
  const now = Math.floor(Date.now() / 1000);
  await env.DB.prepare(`
    INSERT INTO leaderboard_players
      (telegram_id, username, display_name, best_score, score_updated_at, seen_at)
    VALUES (?1, ?2, ?3, ?4, ?5, ?5)
    ON CONFLICT(telegram_id) DO UPDATE SET
      username = excluded.username,
      display_name = excluded.display_name,
      best_score = CASE
        WHEN excluded.best_score > leaderboard_players.best_score
          THEN excluded.best_score
        ELSE leaderboard_players.best_score
      END,
      score_updated_at = CASE
        WHEN excluded.best_score > leaderboard_players.best_score
          THEN excluded.score_updated_at
        ELSE leaderboard_players.score_updated_at
      END,
      seen_at = excluded.seen_at
  `).bind(p.id, p.username, p.displayName, score, now).run();
  return p;
}

async function leaderboard(env, telegramId) {
  const top = await env.DB.prepare(`
    WITH ranked AS (
      SELECT
        telegram_id,
        username,
        display_name,
        best_score,
        score_updated_at,
        RANK() OVER (ORDER BY best_score DESC) AS rank
      FROM leaderboard_players
      WHERE best_score > 0
    )
    SELECT telegram_id, username, display_name, best_score, score_updated_at, rank
    FROM ranked
    ORDER BY best_score DESC, score_updated_at ASC, telegram_id ASC
    LIMIT 10
  `).all();

  const me = await env.DB.prepare(`
    WITH ranked AS (
      SELECT
        telegram_id,
        username,
        display_name,
        best_score,
        score_updated_at,
        RANK() OVER (ORDER BY best_score DESC) AS rank
      FROM leaderboard_players
      WHERE best_score > 0
    )
    SELECT telegram_id, username, display_name, best_score, score_updated_at, rank
    FROM ranked
    WHERE telegram_id = ?1
    LIMIT 1
  `).bind(telegramId).first();

  const count = await env.DB.prepare(
    "SELECT COUNT(*) AS total FROM leaderboard_players WHERE best_score > 0"
  ).first();

  const entries = (top.results || []).map((row) => ({
    rank: Number(row.rank),
    name: row.display_name || (row.username ? `@${row.username}` : "—"),
    score: Number(row.best_score) || 0,
    me: String(row.telegram_id) === telegramId,
  }));

  if (me && !entries.some((row) => row.me)) {
    entries.push({
      rank: Number(me.rank),
      name: me.display_name || (me.username ? `@${me.username}` : "—"),
      score: Number(me.best_score) || 0,
      me: true,
      separated: true,
    });
  }

  return {
    ok: true,
    entries,
    userRank: me ? Number(me.rank) : null,
    userScore: me ? Number(me.best_score) || 0 : 0,
    total: Number(count?.total) || 0,
  };
}

async function readBody(request) {
  const type = request.headers.get("content-type") || "";
  if (!type.toLowerCase().includes("application/json")) throw new Error("json_required");
  return request.json();
}

export default {
  async fetch(request, env) {
    const cors = corsInfo(request, env);
    if (request.method === "OPTIONS") {
      return new Response(null, { status: cors.ok ? 204 : 403, headers: cors.headers });
    }
    if (!cors.ok) return json({ ok: false, error: "origin_not_allowed" }, 403, cors.headers);

    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") {
      return json({ ok: true, service: "koleya-leaderboard", version: 1 }, 200, cors.headers);
    }
    if (request.method !== "POST") {
      return json({ ok: false, error: "not_found" }, 404, cors.headers);
    }
    if (url.pathname !== "/v1/score" && url.pathname !== "/v1/leaderboard") {
      return json({ ok: false, error: "not_found" }, 404, cors.headers);
    }

    try {
      const body = await readBody(request);
      const user = await validateInitData(
        body.initData,
        env.BOT_TOKEN,
        env.INIT_DATA_MAX_AGE || "86400",
      );
      await ensureSchema(env);

      const requestedScore = cleanScore(body.score ?? 0);
      const player = await upsertPlayer(env, user, requestedScore);

      if (url.pathname === "/v1/score") {
        const row = await env.DB.prepare(
          "SELECT best_score FROM leaderboard_players WHERE telegram_id = ?1"
        ).bind(player.id).first();
        return json({ ok: true, best: Number(row?.best_score) || 0 }, 200, cors.headers);
      }

      return json(await leaderboard(env, player.id), 200, cors.headers);
    } catch (error) {
      const code = String(error?.message || "request_failed");
      const authErrors = new Set([
        "missing_init_data",
        "missing_hash",
        "bad_signature",
        "bad_auth_date",
        "expired_init_data",
        "bad_user",
        "missing_user",
      ]);
      const status = authErrors.has(code)
        ? 401
        : code === "bad_score" || code === "json_required"
          ? 400
          : 500;
      return json({ ok: false, error: code }, status, cors.headers);
    }
  },
};
