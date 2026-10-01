# Changelog

## 1.1.0 — pending

Telegram global leaderboard.

- Replaces the old Yandex-only records screen with a shared Telegram leaderboard.
- Adds a Cloudflare Worker + D1 backend.
- Validates Telegram WebApp initData on the server before trusting user identity.
- Migrates an existing local best score when the player opens the records screen.
- Submits new personal records automatically after a run.
- Shows the global top 10 and the current player's rank.
- Keeps the production v1.0.0 build untouched until the backend is deployed and tested.

## 1.0.0 — 2026-10-01

Stable Telegram baseline.

- Telegram Mini App launch is working.
- GitHub Pages production hosting is working.
- AdsGram rewarded block is configured with BlockID 51166.
- Rewarded rewards are granted only after a successful ad completion.
- Browser/Web Audio fixes for combat sounds are included.
- The safe first-pass renderer optimization is included.
- The later aggressive ambient/lighting optimization was rolled back.
- This release is the rollback baseline for future patches.
