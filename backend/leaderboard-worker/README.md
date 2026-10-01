# Koleya Telegram leaderboard backend

Cloudflare Worker + D1 backend for the global Telegram leaderboard.

Security:
- the browser sends Telegram.WebApp.initData;
- the Worker validates Telegram's HMAC-SHA-256 signature using BOT_TOKEN;
- BOT_TOKEN is a Cloudflare secret and is never committed;
- each Telegram user has one row and best_score can only move upward.

API:
- GET /health
- POST /v1/score with { initData, score }
- POST /v1/leaderboard with { initData, score }

Set the Cloudflare project root directory to:
backend/leaderboard-worker

The D1 binding is DB. Wrangler can auto-provision it on first deploy.
After deployment, set the BOT_TOKEN secret in Cloudflare and copy the Worker HTTPS URL into telegram-config.js as leaderboardApiUrl.
