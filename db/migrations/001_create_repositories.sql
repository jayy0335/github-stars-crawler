CREATE TABLE IF NOT EXISTS repositories (
    repo_id TEXT PRIMARY KEY,
    name_with_owner TEXT NOT NULL,
    repo_name TEXT,
    owner_login TEXT,
    url TEXT,
    stars INT NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT now(),
    last_seen TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_repositories_stars ON repositories(stars);
