-- =============================================================
-- MindGuard — Database Initialization Script
-- =============================================================
-- This script runs once when the PostgreSQL container is first
-- created. SQLAlchemy handles table creation via create_all or
-- Alembic migrations. This file sets up database-level config.
-- =============================================================

-- Ensure UTF-8 encoding
SET client_encoding = 'UTF8';

-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_stat_statements for query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Database-level settings for performance
ALTER DATABASE mental_fatigue_db SET timezone TO 'UTC';
ALTER DATABASE mental_fatigue_db SET log_min_duration_statement TO 1000;

-- Grant schema privileges
GRANT ALL PRIVILEGES ON DATABASE mental_fatigue_db TO mf_user;
