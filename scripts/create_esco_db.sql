-- ESCO Database Schema
-- SQLite Database Creation Script
-- For Skill Recommendation System
-- Based on ESCO CSV structure

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better performance
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- 1. ESCO Occupation
CREATE TABLE IF NOT EXISTS esco_occupation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uri VARCHAR(500) NOT NULL,
    language VARCHAR(10) NOT NULL,
    code VARCHAR(50),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    isco_group VARCHAR(50),
    alt_labels TEXT,
    hidden_labels TEXT,
    modified_date DATETIME,
    regulated_profession_note TEXT,
    scope_note TEXT,
    definition TEXT,
    in_scheme VARCHAR(500),
    nace_code VARCHAR(50),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(uri, language)
);

CREATE INDEX IF NOT EXISTS idx_esco_occupation_uri ON esco_occupation(uri);
CREATE INDEX IF NOT EXISTS idx_esco_occupation_language ON esco_occupation(language);
CREATE INDEX IF NOT EXISTS idx_esco_occupation_code ON esco_occupation(code);

-- 2. ESCO Skill
CREATE TABLE IF NOT EXISTS esco_skill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uri VARCHAR(500) NOT NULL,
    language VARCHAR(10) NOT NULL,
    code VARCHAR(50),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    definition TEXT,
    skill_type VARCHAR(50),
    reuse_level VARCHAR(50),
    alt_labels TEXT,
    hidden_labels TEXT,
    scope_note TEXT,
    status VARCHAR(50),
    modified_date DATETIME,
    in_scheme VARCHAR(500),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(uri, language)
);

CREATE INDEX IF NOT EXISTS idx_esco_skill_uri ON esco_skill(uri);
CREATE INDEX IF NOT EXISTS idx_esco_skill_language ON esco_skill(language);
CREATE INDEX IF NOT EXISTS idx_esco_skill_skill_type ON esco_skill(skill_type);

-- 3. ESCO Occupation-Skill Relation
CREATE TABLE IF NOT EXISTS esco_occupation_skill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occupation_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    is_essential BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (occupation_id) REFERENCES esco_occupation(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES esco_skill(id) ON DELETE CASCADE,
    UNIQUE(occupation_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_esco_occupation_skill_occupation ON esco_occupation_skill(occupation_id);
CREATE INDEX IF NOT EXISTS idx_esco_occupation_skill_skill ON esco_occupation_skill(skill_id);

-- ============================================================================
-- TRIGGERS for updated_at
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS update_esco_occupation_timestamp 
AFTER UPDATE ON esco_occupation
BEGIN
    UPDATE esco_occupation SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_esco_skill_timestamp 
AFTER UPDATE ON esco_skill
BEGIN
    UPDATE esco_skill SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_esco_occupation_skill_timestamp 
AFTER UPDATE ON esco_occupation_skill
BEGIN
    UPDATE esco_occupation_skill SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
