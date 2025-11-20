-- Reset Supabase Schema - Clean Slate
-- WARNING: This will DELETE ALL DATA in these tables!
-- Run this in Supabase SQL Editor to start fresh

-- Drop existing tables (CASCADE removes dependencies)
DROP TABLE IF EXISTS rate_limits CASCADE;
DROP TABLE IF EXISTS user_feedback CASCADE;
DROP TABLE IF EXISTS marketplace_influencers CASCADE;
DROP TABLE IF EXISTS product_cache CASCADE;
DROP TABLE IF EXISTS company_cache CASCADE;
DROP TABLE IF EXISTS influencer_cache CASCADE;

-- Drop existing functions
DROP FUNCTION IF EXISTS check_and_increment_rate_limit(TEXT, TEXT, INTEGER);
DROP FUNCTION IF EXISTS check_feedback_rate_limit(TEXT, TEXT);

-- Drop existing views
DROP VIEW IF EXISTS newsletter_subscribers;

-- Now run the full schema creation

-- ============================================================================
-- CACHE TABLES
-- ============================================================================

-- Influencer cache table
CREATE TABLE IF NOT EXISTS influencer_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    handle TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'instagram',
    analysis_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(handle, platform)
);

CREATE INDEX IF NOT EXISTS idx_influencer_handle ON influencer_cache(handle, platform);
CREATE INDEX IF NOT EXISTS idx_influencer_updated ON influencer_cache(updated_at DESC);

-- Company cache table
CREATE TABLE IF NOT EXISTS company_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    analysis_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_name ON company_cache(name);
CREATE INDEX IF NOT EXISTS idx_company_updated ON company_cache(updated_at DESC);

-- Product cache table
CREATE TABLE IF NOT EXISTS product_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    analysis_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_product_name ON product_cache(name);
CREATE INDEX IF NOT EXISTS idx_product_updated ON product_cache(updated_at DESC);

-- ============================================================================
-- MARKETPLACE TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS marketplace_influencers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    handle TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'instagram',

    -- Profile data
    display_name TEXT,
    bio TEXT,
    profile_url TEXT,
    followers_count INTEGER,
    following_count INTEGER,
    posts_count INTEGER,
    is_verified BOOLEAN DEFAULT false,

    -- Trust scores
    overall_trust_score DECIMAL(3, 2) NOT NULL,
    trust_label TEXT NOT NULL,

    -- Component scores
    message_history_score DECIMAL(3, 2),
    followers_score DECIMAL(3, 2),
    web_reputation_score DECIMAL(3, 2),
    disclosure_score DECIMAL(3, 2),

    -- Additional metadata
    analysis_summary TEXT,
    issues JSONB,
    last_analyzed_at TIMESTAMPTZ NOT NULL,

    -- Marketplace metadata
    added_to_marketplace_at TIMESTAMPTZ DEFAULT NOW(),
    is_featured BOOLEAN DEFAULT false,
    admin_notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(handle, platform)
);

CREATE INDEX IF NOT EXISTS idx_marketplace_handle ON marketplace_influencers(handle, platform);
CREATE INDEX IF NOT EXISTS idx_marketplace_trust_score ON marketplace_influencers(overall_trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_marketplace_followers ON marketplace_influencers(followers_count DESC);
CREATE INDEX IF NOT EXISTS idx_marketplace_trust_label ON marketplace_influencers(trust_label);
CREATE INDEX IF NOT EXISTS idx_marketplace_last_analyzed ON marketplace_influencers(last_analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_marketplace_featured ON marketplace_influencers(is_featured DESC);

-- ============================================================================
-- USER FEEDBACK TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Analysis context
    analysis_type TEXT NOT NULL,
    analyzed_entity TEXT,

    -- Feedback data
    experience_rating TEXT NOT NULL CHECK (experience_rating IN ('good', 'medium', 'bad')),
    review_text TEXT,

    -- Email for newsletter (optional)
    email TEXT,
    email_consented BOOLEAN DEFAULT false,

    -- Security and rate limiting
    ip_hash TEXT,
    session_hash TEXT,

    -- Metadata
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT review_text_length CHECK (char_length(review_text) <= 1000),
    CONSTRAINT email_format CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX IF NOT EXISTS idx_feedback_created ON user_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON user_feedback(analysis_type);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON user_feedback(experience_rating);
CREATE INDEX IF NOT EXISTS idx_feedback_email ON user_feedback(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_feedback_ip_hash ON user_feedback(ip_hash, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_session_hash ON user_feedback(session_hash, created_at DESC);

-- ============================================================================
-- RATE LIMITING TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    identifier TEXT NOT NULL,
    endpoint_group TEXT NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMPTZ DEFAULT NOW(),
    last_request_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(identifier, endpoint_group)
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier ON rate_limits(identifier, endpoint_group);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE influencer_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketplace_influencers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES
-- ============================================================================

-- Service role can do anything on all tables
CREATE POLICY "Service role can do anything on influencer_cache"
    ON influencer_cache FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "Service role can do anything on company_cache"
    ON company_cache FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "Service role can do anything on product_cache"
    ON product_cache FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "Service role can do anything on marketplace_influencers"
    ON marketplace_influencers FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "Service role can do anything on user_feedback"
    ON user_feedback FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "Service role can do anything on rate_limits"
    ON rate_limits FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- Public read access for marketplace
CREATE POLICY "Public can read marketplace_influencers"
    ON marketplace_influencers FOR SELECT TO anon, authenticated
    USING (true);

-- Anon users can insert feedback
CREATE POLICY "Anon can insert feedback"
    ON user_feedback FOR INSERT TO anon
    WITH CHECK (true);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Rate limiting function for analysis endpoints
CREATE OR REPLACE FUNCTION check_and_increment_rate_limit(
    p_identifier TEXT,
    p_endpoint_group TEXT,
    p_limit INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    v_count INTEGER;
    v_window_start TIMESTAMPTZ;
BEGIN
    -- Lock the row for this identifier and endpoint
    SELECT request_count, window_start INTO v_count, v_window_start
    FROM rate_limits
    WHERE identifier = p_identifier AND endpoint_group = p_endpoint_group
    FOR UPDATE;

    -- If no record exists or window expired, create/reset
    IF NOT FOUND OR (NOW() - v_window_start) > INTERVAL '1 day' THEN
        INSERT INTO rate_limits (identifier, endpoint_group, request_count, window_start, last_request_at)
        VALUES (p_identifier, p_endpoint_group, 1, NOW(), NOW())
        ON CONFLICT (identifier, endpoint_group)
        DO UPDATE SET
            request_count = 1,
            window_start = NOW(),
            last_request_at = NOW();
        RETURN true;
    END IF;

    -- Check if limit exceeded
    IF v_count >= p_limit THEN
        RETURN false;
    END IF;

    -- Increment counter
    UPDATE rate_limits
    SET request_count = request_count + 1,
        last_request_at = NOW()
    WHERE identifier = p_identifier AND endpoint_group = p_endpoint_group;

    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Feedback rate limiting function
CREATE OR REPLACE FUNCTION check_feedback_rate_limit(p_ip_hash TEXT, p_session_hash TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    ip_count INTEGER;
    session_count INTEGER;
BEGIN
    -- Check IP-based rate limit (max 5 per hour)
    SELECT COUNT(*) INTO ip_count
    FROM user_feedback
    WHERE ip_hash = p_ip_hash
    AND created_at > NOW() - INTERVAL '1 hour';

    -- Check session-based rate limit (max 3 per hour)
    SELECT COUNT(*) INTO session_count
    FROM user_feedback
    WHERE session_hash = p_session_hash
    AND created_at > NOW() - INTERVAL '1 hour';

    RETURN (ip_count < 5 AND session_count < 3);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Newsletter subscribers view (for admin use only)
CREATE OR REPLACE VIEW newsletter_subscribers AS
SELECT
    email,
    MIN(created_at) as subscribed_at,
    COUNT(*) as feedback_count,
    AVG(CASE
        WHEN experience_rating = 'good' THEN 1.0
        WHEN experience_rating = 'medium' THEN 0.5
        ELSE 0.0
    END) as satisfaction_rate
FROM user_feedback
WHERE email IS NOT NULL
AND email_consented = true
GROUP BY email
ORDER BY subscribed_at DESC;
