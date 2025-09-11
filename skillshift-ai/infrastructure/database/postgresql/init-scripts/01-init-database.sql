-- MLBB Coach AI Database Initialization Script
-- Creates optimized schema with proper indexing for high performance

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password_2025';

-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ign VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}',
    statistics JSONB DEFAULT '{}'
);

-- Create indexes for users table
CREATE INDEX idx_users_ign ON users USING btree (ign);
CREATE INDEX idx_users_email ON users USING btree (email);
CREATE INDEX idx_users_created_at ON users USING btree (created_at);
CREATE INDEX idx_users_last_login ON users USING btree (last_login);
CREATE INDEX idx_users_preferences ON users USING gin (preferences);

-- Heroes and Game Data
CREATE TABLE heroes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL,
    difficulty INTEGER CHECK (difficulty >= 1 AND difficulty <= 10),
    release_date DATE,
    is_active BOOLEAN DEFAULT true,
    base_stats JSONB NOT NULL DEFAULT '{}',
    skills JSONB NOT NULL DEFAULT '{}',
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for heroes table
CREATE INDEX idx_heroes_name ON heroes USING btree (name);
CREATE INDEX idx_heroes_role ON heroes USING btree (role);
CREATE INDEX idx_heroes_difficulty ON heroes USING btree (difficulty);
CREATE INDEX idx_heroes_is_active ON heroes USING btree (is_active);
CREATE INDEX idx_heroes_base_stats ON heroes USING gin (base_stats);
CREATE INDEX idx_heroes_meta_data ON heroes USING gin (meta_data);

-- Matches and Game Sessions
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_type VARCHAR(50) NOT NULL,
    duration_seconds INTEGER,
    result VARCHAR(20) CHECK (result IN ('win', 'loss', 'draw')),
    raw_data JSONB NOT NULL DEFAULT '{}',
    processed_data JSONB DEFAULT '{}',
    screenshot_paths TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    is_processed BOOLEAN DEFAULT false
);

-- Create indexes for matches table
CREATE INDEX idx_matches_user_id ON matches USING btree (user_id);
CREATE INDEX idx_matches_match_type ON matches USING btree (match_type);
CREATE INDEX idx_matches_result ON matches USING btree (result);
CREATE INDEX idx_matches_created_at ON matches USING btree (created_at);
CREATE INDEX idx_matches_is_processed ON matches USING btree (is_processed);
CREATE INDEX idx_matches_raw_data ON matches USING gin (raw_data);
CREATE INDEX idx_matches_processed_data ON matches USING gin (processed_data);

-- Player Performance in Matches
CREATE TABLE player_performances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hero_id UUID REFERENCES heroes(id),
    hero_name VARCHAR(100) NOT NULL,
    position INTEGER CHECK (position >= 1 AND position <= 10),
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    damage_dealt BIGINT DEFAULT 0,
    damage_taken BIGINT DEFAULT 0,
    gold_earned INTEGER DEFAULT 0,
    items JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    mvp_score DECIMAL(5,2),
    is_mvp BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for player_performances table
CREATE INDEX idx_player_performances_match_id ON player_performances USING btree (match_id);
CREATE INDEX idx_player_performances_user_id ON player_performances USING btree (user_id);
CREATE INDEX idx_player_performances_hero_id ON player_performances USING btree (hero_id);
CREATE INDEX idx_player_performances_hero_name ON player_performances USING btree (hero_name);
CREATE INDEX idx_player_performances_is_mvp ON player_performances USING btree (is_mvp);
CREATE INDEX idx_player_performances_mvp_score ON player_performances USING btree (mvp_score DESC);
CREATE INDEX idx_player_performances_kda ON player_performances USING btree (kills, deaths, assists);
CREATE INDEX idx_player_performances_metrics ON player_performances USING gin (performance_metrics);

-- Analysis Results and Coaching Data
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    analysis_type VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    results JSONB NOT NULL DEFAULT '{}',
    coaching_insights JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '[]',
    processing_time_ms INTEGER,
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days')
);

-- Create indexes for analysis_results table
CREATE INDEX idx_analysis_results_match_id ON analysis_results USING btree (match_id);
CREATE INDEX idx_analysis_results_user_id ON analysis_results USING btree (user_id);
CREATE INDEX idx_analysis_results_type ON analysis_results USING btree (analysis_type);
CREATE INDEX idx_analysis_results_confidence ON analysis_results USING btree (confidence_score DESC);
CREATE INDEX idx_analysis_results_created_at ON analysis_results USING btree (created_at);
CREATE INDEX idx_analysis_results_expires_at ON analysis_results USING btree (expires_at);
CREATE INDEX idx_analysis_results_results ON analysis_results USING gin (results);

-- User Sessions and Activity Tracking
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for user_sessions table
CREATE INDEX idx_user_sessions_user_id ON user_sessions USING btree (user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions USING btree (session_token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions USING btree (expires_at);
CREATE INDEX idx_user_sessions_is_active ON user_sessions USING btree (is_active);

-- Cache Management Table
CREATE TABLE cache_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(500) NOT NULL UNIQUE,
    partition VARCHAR(100) NOT NULL,
    value_data JSONB,
    value_text TEXT,
    ttl_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for cache_entries table
CREATE INDEX idx_cache_entries_key ON cache_entries USING btree (cache_key);
CREATE INDEX idx_cache_entries_partition ON cache_entries USING btree (partition);
CREATE INDEX idx_cache_entries_expires_at ON cache_entries USING btree (expires_at);
CREATE INDEX idx_cache_entries_access_count ON cache_entries USING btree (access_count DESC);

-- Performance Metrics and System Health
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(200) NOT NULL,
    metric_value DECIMAL(15,6),
    metric_unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for system_metrics table
CREATE INDEX idx_system_metrics_name ON system_metrics USING btree (metric_name);
CREATE INDEX idx_system_metrics_recorded_at ON system_metrics USING btree (recorded_at);
CREATE INDEX idx_system_metrics_name_time ON system_metrics USING btree (metric_name, recorded_at);
CREATE INDEX idx_system_metrics_tags ON system_metrics USING gin (tags);

-- Create partitioned table for high-volume metrics (by month)
CREATE TABLE system_metrics_partitioned (
    id UUID DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(200) NOT NULL,
    metric_value DECIMAL(15,6),
    metric_unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (recorded_at);

-- Create monthly partitions for current and next 12 months
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..12 LOOP
        start_date := DATE_TRUNC('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'system_metrics_' || TO_CHAR(start_date, 'YYYY_MM');
        
        EXECUTE FORMAT('CREATE TABLE %I PARTITION OF system_metrics_partitioned 
                       FOR VALUES FROM (%L) TO (%L)', 
                       partition_name, start_date, end_date);
        
        EXECUTE FORMAT('CREATE INDEX idx_%I_name_time ON %I (metric_name, recorded_at)',
                       partition_name, partition_name);
    END LOOP;
END $$;

-- Functions for common operations
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_heroes_updated_at BEFORE UPDATE ON heroes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM cache_entries WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get user performance statistics
CREATE OR REPLACE FUNCTION get_user_performance_stats(user_uuid UUID, days_back INTEGER DEFAULT 30)
RETURNS TABLE (
    total_matches BIGINT,
    wins BIGINT,
    losses BIGINT,
    win_rate DECIMAL(5,2),
    avg_kills DECIMAL(5,2),
    avg_deaths DECIMAL(5,2),
    avg_assists DECIMAL(5,2),
    avg_kda DECIMAL(5,2),
    mvp_count BIGINT,
    mvp_rate DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_matches,
        COUNT(*) FILTER (WHERE m.result = 'win') as wins,
        COUNT(*) FILTER (WHERE m.result = 'loss') as losses,
        ROUND(
            (COUNT(*) FILTER (WHERE m.result = 'win')::DECIMAL / NULLIF(COUNT(*), 0)) * 100, 
            2
        ) as win_rate,
        ROUND(AVG(pp.kills), 2) as avg_kills,
        ROUND(AVG(pp.deaths), 2) as avg_deaths,
        ROUND(AVG(pp.assists), 2) as avg_assists,
        ROUND(AVG(
            CASE 
                WHEN pp.deaths = 0 THEN pp.kills + pp.assists 
                ELSE (pp.kills + pp.assists)::DECIMAL / pp.deaths 
            END
        ), 2) as avg_kda,
        COUNT(*) FILTER (WHERE pp.is_mvp = true) as mvp_count,
        ROUND(
            (COUNT(*) FILTER (WHERE pp.is_mvp = true)::DECIMAL / NULLIF(COUNT(*), 0)) * 100, 
            2
        ) as mvp_rate
    FROM matches m
    JOIN player_performances pp ON m.id = pp.match_id
    WHERE pp.user_id = user_uuid
    AND m.created_at >= NOW() - (days_back || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- Create materialized view for hero win rates
CREATE MATERIALIZED VIEW hero_win_rates AS
SELECT 
    h.id as hero_id,
    h.name as hero_name,
    h.role,
    COUNT(*) as total_matches,
    COUNT(*) FILTER (WHERE m.result = 'win') as wins,
    ROUND(
        (COUNT(*) FILTER (WHERE m.result = 'win')::DECIMAL / NULLIF(COUNT(*), 0)) * 100, 
        2
    ) as win_rate,
    ROUND(AVG(pp.kills), 2) as avg_kills,
    ROUND(AVG(pp.deaths), 2) as avg_deaths,
    ROUND(AVG(pp.assists), 2) as avg_assists,
    COUNT(*) FILTER (WHERE pp.is_mvp = true) as mvp_count,
    NOW() as last_updated
FROM heroes h
JOIN player_performances pp ON h.id = pp.hero_id
JOIN matches m ON pp.match_id = m.id
WHERE m.created_at >= NOW() - INTERVAL '30 days'
GROUP BY h.id, h.name, h.role
HAVING COUNT(*) >= 10;  -- Only heroes with at least 10 matches

CREATE UNIQUE INDEX idx_hero_win_rates_hero_id ON hero_win_rates (hero_id);

-- Schedule automatic refresh of materialized view
CREATE OR REPLACE FUNCTION refresh_hero_win_rates()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY hero_win_rates;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT CONNECT ON DATABASE mlbb_coach_ai TO mlbb_user;
GRANT USAGE ON SCHEMA public TO mlbb_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mlbb_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mlbb_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mlbb_user;

-- Insert sample heroes data
INSERT INTO heroes (name, role, difficulty, base_stats, skills) VALUES
('Layla', 'Marksman', 2, '{"hp": 2500, "mana": 430, "attack": 120}', '{"passive": "Malefic Bomb", "skill1": "Malefic Bomb", "skill2": "Void Projectile", "ultimate": "Destruction Rush"}'),
('Miya', 'Marksman', 3, '{"hp": 2600, "mana": 450, "attack": 125}', '{"passive": "Moon Blessing", "skill1": "Fission Shot", "skill2": "Arrow of Eclipse", "ultimate": "Hidden Moonlight"}'),
('Tigreal', 'Tank', 2, '{"hp": 3200, "mana": 400, "attack": 100}', '{"passive": "Fearless", "skill1": "Attack Wave", "skill2": "Sacred Hammer", "ultimate": "Implosion"}'),
('Franco', 'Tank', 3, '{"hp": 3100, "mana": 420, "attack": 95}', '{"passive": "Wasteland Force", "skill1": "Iron Hook", "skill2": "Revenge", "ultimate": "Bloody Hunt"}'),
('Chou', 'Fighter', 4, '{"hp": 2800, "mana": 400, "attack": 130}', '{"passive": "Only Fast", "skill1": "Jeet Kune Do", "skill2": "Shunpo", "ultimate": "The Way of Dragon"}');

-- Create database maintenance job
CREATE OR REPLACE FUNCTION maintenance_job()
RETURNS VOID AS $$
BEGIN
    -- Clean expired cache entries
    PERFORM clean_expired_cache();
    
    -- Clean old analysis results
    DELETE FROM analysis_results WHERE expires_at < NOW();
    
    -- Clean expired user sessions
    DELETE FROM user_sessions WHERE expires_at < NOW();
    
    -- Update statistics
    ANALYZE;
    
    -- Refresh materialized views
    PERFORM refresh_hero_win_rates();
    
    RAISE NOTICE 'Database maintenance completed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
INSERT INTO system_metrics (metric_name, metric_value, metric_unit, tags) 
VALUES ('database_initialization', 1, 'boolean', '{"status": "completed", "timestamp": "' || NOW() || '"}');

COMMENT ON DATABASE mlbb_coach_ai IS 'MLBB Coach AI - High Performance Database with Optimized Indexing and Replication';

-- Final message
DO $$
BEGIN
    RAISE NOTICE 'MLBB Coach AI database initialized successfully with optimized schema and indexing';
END $$;
