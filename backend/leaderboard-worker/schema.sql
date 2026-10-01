CREATE TABLE IF NOT EXISTS leaderboard_players (
  telegram_id TEXT PRIMARY KEY,
  username TEXT,
  display_name TEXT NOT NULL,
  best_score INTEGER NOT NULL DEFAULT 0,
  score_updated_at INTEGER NOT NULL,
  seen_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_score
ON leaderboard_players(best_score DESC, score_updated_at ASC);
