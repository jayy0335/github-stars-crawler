DROP TABLE IF EXISTS repositories;

-- Create repositories table
CREATE TABLE IF NOT EXISTS repositories (
    repo_id TEXT PRIMARY KEY,
    name_with_owner TEXT NOT NULL,
    repo_name TEXT,
    owner_login TEXT,
    url TEXT,
    stars INT NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT now(),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Index to help lookup by name
CREATE INDEX IF NOT EXISTS idx_repositories_name_owner ON repositories (name_with_owner);
