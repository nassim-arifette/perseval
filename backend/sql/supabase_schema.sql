-- Supabase schema for Perseval cache tables
-- Run this SQL in your Supabase SQL editor to create the required tables

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

-- Create index for faster lookups
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

-- Create index for faster lookups
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

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_product_name ON product_cache(name);
CREATE INDEX IF NOT EXISTS idx_product_updated ON product_cache(updated_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE influencer_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_cache ENABLE ROW LEVEL SECURITY;

-- Create policies for service role (backend API)
-- These policies allow the service role to do anything
CREATE POLICY "Service role can do anything on influencer_cache"
    ON influencer_cache
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role can do anything on company_cache"
    ON company_cache
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role can do anything on product_cache"
    ON product_cache
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Optional: Create policies for authenticated users (if you want to allow direct access)
-- Uncomment these if you want authenticated users to read the cache
-- CREATE POLICY "Authenticated users can read influencer_cache"
--     ON influencer_cache
--     FOR SELECT
--     TO authenticated
--     USING (true);

-- CREATE POLICY "Authenticated users can read company_cache"
--     ON company_cache
--     FOR SELECT
--     TO authenticated
--     USING (true);

-- CREATE POLICY "Authenticated users can read product_cache"
--     ON product_cache
--     FOR SELECT
--     TO authenticated
--     USING (true);

-- Marketplace influencers table (curated list for public display)
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
    overall_trust_score DECIMAL(3, 2) NOT NULL,  -- 0.00 to 1.00
    trust_label TEXT NOT NULL,  -- 'high', 'medium', 'low'

    -- Component scores
    message_history_score DECIMAL(3, 2),
    followers_score DECIMAL(3, 2),
    web_reputation_score DECIMAL(3, 2),
    disclosure_score DECIMAL(3, 2),

    -- Additional metadata
    analysis_summary TEXT,
    issues JSONB,  -- Array of issues/red flags
    last_analyzed_at TIMESTAMPTZ NOT NULL,

    -- Marketplace metadata
    added_to_marketplace_at TIMESTAMPTZ DEFAULT NOW(),
    is_featured BOOLEAN DEFAULT false,
    admin_notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(handle, platform)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_marketplace_handle ON marketplace_influencers(handle, platform);
CREATE INDEX IF NOT EXISTS idx_marketplace_trust_score ON marketplace_influencers(overall_trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_marketplace_followers ON marketplace_influencers(followers_count DESC);
CREATE INDEX IF NOT EXISTS idx_marketplace_trust_label ON marketplace_influencers(trust_label);
CREATE INDEX IF NOT EXISTS idx_marketplace_last_analyzed ON marketplace_influencers(last_analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_marketplace_featured ON marketplace_influencers(is_featured DESC);

-- Enable Row Level Security
ALTER TABLE marketplace_influencers ENABLE ROW LEVEL SECURITY;

-- Service role can do anything
CREATE POLICY "Service role can do anything on marketplace_influencers"
    ON marketplace_influencers
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Public read access (anyone can view marketplace)
CREATE POLICY "Public can read marketplace_influencers"
    ON marketplace_influencers
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- User feedback table (for post-analysis feedback and newsletter signups)
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Analysis context
    analysis_type TEXT NOT NULL,  -- 'full', 'influencer', 'company', 'product', 'text'
    analyzed_entity TEXT,  -- Handle/name of what was analyzed (optional)

    -- Feedback data (simplified to 3 emoji ratings)
    experience_rating TEXT NOT NULL CHECK (experience_rating IN ('good', 'medium', 'bad')),  -- 'good', 'medium', or 'bad'
    review_text TEXT,  -- User review (max 1000 chars)

    -- Email for newsletter (optional)
    email TEXT,  -- Validated email format
    email_consented BOOLEAN DEFAULT false,  -- Explicit consent for email communication

    -- Security and rate limiting (hashed for privacy)
    ip_hash TEXT,  -- SHA-256 hash of IP address
    session_hash TEXT,  -- Hash of session/fingerprint for deduplication

    -- Metadata
    user_agent TEXT,  -- For analytics (truncated)
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT review_text_length CHECK (char_length(review_text) <= 1000),
    CONSTRAINT email_format CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Create indexes for queries and rate limiting
CREATE INDEX IF NOT EXISTS idx_feedback_created ON user_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON user_feedback(analysis_type);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON user_feedback(experience_rating);
CREATE INDEX IF NOT EXISTS idx_feedback_email ON user_feedback(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_feedback_ip_hash ON user_feedback(ip_hash, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_session_hash ON user_feedback(session_hash, created_at DESC);

-- Enable Row Level Security
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;

-- Service role can do anything
CREATE POLICY "Service role can do anything on user_feedback"
    ON user_feedback
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Anon users can only insert their own feedback (not read others)
CREATE POLICY "Anon can insert feedback"
    ON user_feedback
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Function to check rate limiting (max 5 submissions per IP hash per hour)
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
