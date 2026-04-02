-- Migration: Add burst_events table and avatar queue support
-- Created: 2026-04-01

-- Table for logging burst events from audio detection
CREATE TABLE IF NOT EXISTS burst_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- 'achievement', 'death', 'killstreak', 'explosion'
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    timestamp INTEGER NOT NULL,  -- unix_ms from client
    game_context VARCHAR(255),   -- optional game/app context
    processed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_burst_events_user_id ON burst_events(user_id);
CREATE INDEX IF NOT EXISTS idx_burst_events_event_type ON burst_events(event_type);
CREATE INDEX IF NOT EXISTS idx_burst_events_timestamp ON burst_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_burst_events_processed ON burst_events(processed);

-- Table for avatar queue tracking (optional - if you want persistent queue)
CREATE TABLE IF NOT EXISTS avatar_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',  -- 'normal' or 'burst'
    payload TEXT,  -- JSON payload
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_avatar_queue_user_status ON avatar_queue(user_id, status);
CREATE INDEX IF NOT EXISTS idx_avatar_queue_priority ON avatar_queue(priority, created_at);

-- Migration log entry
INSERT INTO sqlite_master (type, name, tbl_name, rootpage, sql) 
SELECT 'migration', 'burst_events_2024_04_01', '', 0, 'Applied burst_events table migration'
WHERE NOT EXISTS (
    SELECT 1 FROM sqlite_master WHERE name = 'burst_events'
);
