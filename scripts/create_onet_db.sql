-- ONET Database Schema
-- SQLite Database Creation Script
-- For Skill Recommendation System
-- Based on ONET 30.1 Text Database Structure
-- Occupation x Task (IM scale) and Occupation x Technology Skills (derived weight)

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better performance
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- 1. ONET Occupation
CREATE TABLE IF NOT EXISTS onet_occupation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_onet_occupation_code ON onet_occupation(code);
CREATE INDEX IF NOT EXISTS idx_onet_occupation_title ON onet_occupation(title);

-- 2. ONET Task (from Task Statements)
CREATE TABLE IF NOT EXISTS onet_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id VARCHAR(20) NOT NULL UNIQUE,
    task_text TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_onet_task_task_id ON onet_task(task_id);

-- 3. ONET Occupation-Task Relation (Task Ratings, IM scale for importance)
CREATE TABLE IF NOT EXISTS onet_occupation_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occupation_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    scale_id VARCHAR(10) NOT NULL DEFAULT 'IM',
    data_value DECIMAL(5,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (occupation_id) REFERENCES onet_occupation(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES onet_task(id) ON DELETE CASCADE,
    UNIQUE(occupation_id, task_id, scale_id)
);

CREATE INDEX IF NOT EXISTS idx_onet_occupation_task_occupation ON onet_occupation_task(occupation_id);
CREATE INDEX IF NOT EXISTS idx_onet_occupation_task_task ON onet_occupation_task(task_id);
CREATE INDEX IF NOT EXISTS idx_onet_occupation_task_scale ON onet_occupation_task(scale_id);

-- 4. ONET Technology Skill (from Technology Skills.txt, Example = software/tool name)
CREATE TABLE IF NOT EXISTS onet_technology_skill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    example VARCHAR(500) NOT NULL UNIQUE,
    commodity_code VARCHAR(20),
    commodity_title VARCHAR(500),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_onet_technology_skill_example ON onet_technology_skill(example);

-- 5. ONET Occupation-Technology Skill Relation (weight derived from Hot Technology / In Demand)
CREATE TABLE IF NOT EXISTS onet_occupation_technology_skill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occupation_id INTEGER NOT NULL,
    technology_skill_id INTEGER NOT NULL,
    weight DECIMAL(3,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (occupation_id) REFERENCES onet_occupation(id) ON DELETE CASCADE,
    FOREIGN KEY (technology_skill_id) REFERENCES onet_technology_skill(id) ON DELETE CASCADE,
    UNIQUE(occupation_id, technology_skill_id)
);

CREATE INDEX IF NOT EXISTS idx_onet_occupation_tech_skill_occupation ON onet_occupation_technology_skill(occupation_id);
CREATE INDEX IF NOT EXISTS idx_onet_occupation_tech_skill_skill ON onet_occupation_technology_skill(technology_skill_id);

-- ============================================================================
-- TRIGGERS for updated_at
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS update_onet_occupation_timestamp 
AFTER UPDATE ON onet_occupation
BEGIN
    UPDATE onet_occupation SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_onet_task_timestamp 
AFTER UPDATE ON onet_task
BEGIN
    UPDATE onet_task SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_onet_occupation_task_timestamp 
AFTER UPDATE ON onet_occupation_task
BEGIN
    UPDATE onet_occupation_task SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_onet_technology_skill_timestamp 
AFTER UPDATE ON onet_technology_skill
BEGIN
    UPDATE onet_technology_skill SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_onet_occupation_technology_skill_timestamp 
AFTER UPDATE ON onet_occupation_technology_skill
BEGIN
    UPDATE onet_occupation_technology_skill SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
