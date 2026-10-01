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


function miniAppUrl(env) {
  return String(env.MINI_APP_URL || "https://qw0w.github.io/koleya-telegram/").trim();
}

async function telegramApi(env, method, payload) {
  if (!env.BOT_TOKEN) throw new Error("missing_bot_token");
  const r = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  const data = await r.json().catch(() => null);
  if (!r.ok || !data || !data.ok) {
    throw new Error((data && data.description) || `telegram_${method}_failed`);
  }
  return data.result;
}

async function webhookSecret(env) {
  if (!env.BOT_TOKEN) throw new Error("missing_bot_token");
  const bytes = await crypto.subtle.digest(
    "SHA-256",
    enc.encode("koleya-webhook:" + env.BOT_TOKEN),
  );
  return hex(new Uint8Array(bytes));
}

function welcomeCopy(user) {
  const lang = String(user?.language_code || "").toLowerCase();
  if (lang.startsWith("ru")) {
    return {
      title: "🌙 <b>КОЛЕЯ</b>",
      body:
        "Ночная дорога зовёт. Прокладывай путь, сражайся с нечистью, возвращай эхо в лагерь и попробуй пройти дальше остальных.\n\n" +
        "🎮 <b>Играй прямо в Telegram</b> — ничего скачивать не нужно.",
      play: "🎮 Играть",
      help:
        "Иди всё дальше по дороге, выбирай карточки пути и вовремя возвращайся в лагерь. Чем дальше зайдёшь — тем выше риск и награда.\n\n" +
        "После запуска игры всё управление находится внутри Mini App.",
    };
  }
  return {
    title: "🌙 <b>KOLEYA</b>",
    body:
      "The night road is calling. Build your path, face dark creatures, bring Echo back to camp and see how far you can go.\n\n" +
      "🎮 <b>Play directly in Telegram</b> — no download required.",
    play: "🎮 Play",
    help:
      "Travel deeper along the road, choose path cards and return to camp before it is too late. The farther you go, the greater the risk and reward.\n\n" +
      "All controls are inside the Mini App.",
  };
}

function playKeyboard(env, text) {
  return {
    inline_keyboard: [[
      {
        text,
        web_app: { url: miniAppUrl(env) },
      },
    ]],
  };
}

async function sendWelcome(env, chatId, user) {
  const c = welcomeCopy(user);
  const text = c.title + "\n\n" + c.body;
  const photo = String(env.WELCOME_IMAGE_URL || "").trim();

  if (photo) {
    try {
      await telegramApi(env, "sendPhoto", {
        chat_id: chatId,
        photo,
        caption: text,
        parse_mode: "HTML",
        reply_markup: playKeyboard(env, c.play),
      });
      return;
    } catch {
      // Fall back to a normal message if the image URL is temporarily unavailable.
    }
  }

  await telegramApi(env, "sendMessage", {
    chat_id: chatId,
    text,
    parse_mode: "HTML",
    disable_web_page_preview: true,
    reply_markup: playKeyboard(env, c.play),
  });
}

async function sendHelp(env, chatId, user) {
  const c = welcomeCopy(user);
  await telegramApi(env, "sendMessage", {
    chat_id: chatId,
    text: c.help,
    reply_markup: playKeyboard(env, c.play),
  });
}

async function handleTelegramWebhook(request, env) {
  const expected = await webhookSecret(env);
  const received = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
  if (!timingSafeHexEqual(expected, received)) {
    return json({ ok: false, error: "bad_webhook_secret" }, 403);
  }

  const update = await request.json().catch(() => null);
  const message = update?.message;
  if (!message || message.chat?.type !== "private") {
    return json({ ok: true });
  }

  const text = String(message.text || "").trim();
  const command = text.split(/\s+/)[0].split("@")[0].toLowerCase();

  if (command === "/start" || command === "/play") {
    await sendWelcome(env, message.chat.id, message.from);
  } else if (command === "/help") {
    await sendHelp(env, message.chat.id, message.from);
  }

  return json({ ok: true });
}

async function configureTelegramBot(origin, env) {
  if (!env.BOT_TOKEN) throw new Error("missing_bot_token");
  const secret = await webhookSecret(env);
  const appUrl = miniAppUrl(env);

  const webhook = await telegramApi(env, "setWebhook", {
    url: origin + "/telegram/webhook",
    secret_token: secret,
    allowed_updates: ["message"],
    drop_pending_updates: false,
  });

  const menu = await telegramApi(env, "setChatMenuButton", {
    menu_button: {
      type: "web_app",
      text: "🎮 Играть",
      web_app: { url: appUrl },
    },
  });

  const commands = await telegramApi(env, "setMyCommands", {
    commands: [
      { command: "play", description: "Открыть игру" },
      { command: "help", description: "Как играть" },
    ],
  });

  return { webhook, menu, commands, miniAppUrl: appUrl };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "POST" && url.pathname === "/telegram/webhook") {
      try {
        return await handleTelegramWebhook(request, env);
      } catch (error) {
        return json({ ok: false, error: String(error?.message || "telegram_webhook_failed") }, 500);
      }
    }

    if (request.method === "GET" && url.pathname === "/telegram/setup") {
      try {
        const result = await configureTelegramBot(url.origin, env);
        return json({ ok: true, ...result });
      } catch (error) {
        return json({ ok: false, error: String(error?.message || "telegram_setup_failed") }, 500);
      }
    }

    const cors = corsInfo(request, env);
    if (request.method === "OPTIONS") {
      return new Response(null, { status: cors.ok ? 204 : 403, headers: cors.headers });
    }
    if (!cors.ok) return json({ ok: false, error: "origin_not_allowed" }, 403, cors.headers);

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
