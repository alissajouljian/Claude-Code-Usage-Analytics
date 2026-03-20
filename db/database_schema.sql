-- Schema for Claude Code Usage Analytics Platform

CREATE TABLE IF NOT EXISTS employees (
    email TEXT PRIMARY KEY,
    full_name TEXT,
    practice TEXT,
    level TEXT,
    location TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    timestamp DATETIME,
    event_body TEXT,
    event_name TEXT,
    session_id TEXT,
    user_id TEXT,
    email TEXT,
    model TEXT,
    cost_usd REAL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cache_read_tokens INTEGER,
    cache_creation_tokens INTEGER,
    duration_ms INTEGER,
    tool_name TEXT,
    decision TEXT,
    success BOOLEAN,
    prompt_length INTEGER,
    error_message TEXT,
    status_code TEXT,
    FOREIGN KEY (email) REFERENCES employees(email)
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_email ON events(email);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_name);
