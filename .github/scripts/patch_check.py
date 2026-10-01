from pathlib import Path
import re
import sys

root = Path(".")
required = [
    Path("index.html"),
    Path("telegram-config.js"),
    Path(".nojekyll"),
    Path("VERSION"),
    Path("CHANGELOG.md"),
]

errors = []
for p in required:
    if not p.exists():
        errors.append(f"missing required file: {p}")

if not Path("fonts").is_dir():
    errors.append("missing fonts/ directory")

version = Path("VERSION").read_text(encoding="utf-8").strip() if Path("VERSION").exists() else ""
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    errors.append(f"VERSION must be semantic version X.Y.Z, got: {version!r}")

index = Path("index.html").read_text(encoding="utf-8") if Path("index.html").exists() else ""
cfg = Path("telegram-config.js").read_text(encoding="utf-8") if Path("telegram-config.js").exists() else ""

checks = [
    ("Telegram Web App SDK is missing", "telegram.org/js/telegram-web-app.js" in index),
    ("AdsGram SDK is missing", "sad.adsgram.ai/js/sad.min.js" in index),
    ("telegram-config.js is not loaded", "telegram-config.js" in index),
    ("active Yandex SDK initialization found", "YaGames.init(" not in index),
    ("Yandex /sdk.js include found", 'src="/sdk.js"' not in index and "src='/sdk.js'" not in index),
    ("production dev ad bypass is enabled", "devRewardWithoutAd: false" in cfg),
]
for msg, ok in checks:
    if not ok:
        errors.append(msg)

# Prevent accidental Telegram bot token commits in production text files.
token_re = re.compile(r"\b\d{7,12}:[A-Za-z0-9_-]{20,}\b")
for p in [Path("index.html"), Path("telegram-config.js"), Path("README_TELEGRAM.md"), Path("PATCHING.md")]:
    if p.exists() and token_re.search(p.read_text(encoding="utf-8", errors="ignore")):
        errors.append(f"possible Telegram bot token found in {p}")

if Path("index.html").exists() and Path("index.html").stat().st_size > 5_000_000:
    errors.append("index.html unexpectedly exceeds 5 MB")

if errors:
    print("PATCH CHECK FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print(f"PATCH CHECK OK — v{version}")
