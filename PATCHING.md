# Koleya patch workflow

Production URL: https://qw0w.github.io/koleya-telegram/

## Branches

- `main` — production. GitHub Pages publishes this branch.
- `stable` — last confirmed-good production snapshot.
- `patch/vX.Y.Z` — temporary branch for each new patch.

## Release process

1. Start a new patch branch from current `main`, for example `patch/v1.0.1`.
2. Make only the intended changes on the patch branch.
3. Increment `VERSION` using semantic versioning:
   - PATCH: bug fix / balance / small content update — 1.0.0 → 1.0.1
   - MINOR: meaningful new feature/content — 1.0.0 → 1.1.0
   - MAJOR: incompatible save/game architecture change — 1.x → 2.0.0
4. Add a short entry to `CHANGELOG.md`.
5. Wait for the **Patch Safety Check** GitHub Action to pass.
6. Move the tested patch to `main`. GitHub Pages then publishes it automatically.
7. Test the live Mini App inside Telegram.
8. Only after the live build is confirmed good, advance `stable` to the same commit.

## Rollback rule

If production breaks, restore the game files from `stable` to `main` immediately, publish, and investigate on a new patch branch.

The `stable` branch must never be advanced until the live Telegram build has been checked.

## Save compatibility

Existing local saves must remain readable across patch/minor updates. If the save schema changes:
- keep defaults for missing fields;
- migrate old values forward;
- do not rename/delete save keys without a migration;
- test with an existing save before release.

## Cache rule

After a release, fully close and reopen the Telegram Mini App when testing. For changes to external assets/config, bump the app version and use versioned asset URLs when needed so Telegram/WebView cannot hold a stale file.

## Ads rule

Never enable `devRewardWithoutAd` in production. Never commit Telegram bot tokens or other secrets.
