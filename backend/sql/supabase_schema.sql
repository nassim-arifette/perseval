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
DROP POLICY IF EXISTS "Service role can do anything on influencer_cache" ON influencer_cache;
CREATE POLICY "Service role can do anything on influencer_cache"
    ON influencer_cache
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can do anything on company_cache" ON company_cache;
CREATE POLICY "Service role can do anything on company_cache"
    ON company_cache
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can do anything on product_cache" ON product_cache;
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
DROP POLICY IF EXISTS "Service role can do anything on marketplace_influencers" ON marketplace_influencers;
CREATE POLICY "Service role can do anything on marketplace_influencers"
    ON marketplace_influencers
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Public read access (anyone can view marketplace)
DROP POLICY IF EXISTS "Public can read marketplace_influencers" ON marketplace_influencers;
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
DROP POLICY IF EXISTS "Service role can do anything on user_feedback" ON user_feedback;
CREATE POLICY "Service role can do anything on user_feedback"
    ON user_feedback
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Anon users can only insert their own feedback (not read others)
DROP POLICY IF EXISTS "Anon can insert feedback" ON user_feedback;
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

-- User influencer submissions table (for crowdsourced marketplace additions)
CREATE TABLE IF NOT EXISTS influencer_submissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Submission data
    handle TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'instagram',
    reason TEXT,  -- Why user thinks this influencer should be added (optional, max 500 chars)

    -- Submitter tracking (anonymized for privacy)
    submitter_ip_hash TEXT NOT NULL,  -- SHA-256 hash of IP for rate limiting
    submitter_session_hash TEXT,  -- Optional session fingerprint

    -- Submission status workflow
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'analyzing', 'approved', 'rejected')),

    -- Automated analysis results (from Perplexity + Mistral)
    analysis_data JSONB,  -- Full analysis results stored as JSON
    trust_score DECIMAL(3, 2),  -- Automated trust score (0.00-1.00)
    analysis_completed_at TIMESTAMPTZ,
    analysis_error TEXT,  -- Error message if analysis failed

    -- Admin review
    reviewed_by TEXT,  -- Admin username/identifier
    reviewed_at TIMESTAMPTZ,
    admin_notes TEXT,  -- Admin's decision notes
    rejection_reason TEXT,  -- Specific reason if rejected

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT reason_length CHECK (char_length(reason) <= 500)
);

-- Create indexes for queries and admin workflow
CREATE INDEX IF NOT EXISTS idx_submissions_status ON influencer_submissions(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_handle ON influencer_submissions(handle, platform);
CREATE INDEX IF NOT EXISTS idx_submissions_submitter ON influencer_submissions(submitter_ip_hash, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_created ON influencer_submissions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_reviewed ON influencer_submissions(reviewed_at DESC) WHERE reviewed_at IS NOT NULL;

-- Enable Row Level Security
ALTER TABLE influencer_submissions ENABLE ROW LEVEL SECURITY;

-- Service role can do anything (for backend API)
DROP POLICY IF EXISTS "Service role can do anything on influencer_submissions" ON influencer_submissions;
CREATE POLICY "Service role can do anything on influencer_submissions"
    ON influencer_submissions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Anon users can insert submissions (rate limited by function)
DROP POLICY IF EXISTS "Anon can insert submissions" ON influencer_submissions;
CREATE POLICY "Anon can insert submissions"
    ON influencer_submissions
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Function to check submission rate limit (max 3 submissions per IP per day)
CREATE OR REPLACE FUNCTION check_submission_rate_limit(p_ip_hash TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    submission_count INTEGER;
BEGIN
    -- Check IP-based rate limit (max 3 submissions per 24 hours)
    SELECT COUNT(*) INTO submission_count
    FROM influencer_submissions
    WHERE submitter_ip_hash = p_ip_hash
    AND created_at > NOW() - INTERVAL '24 hours';

    RETURN (submission_count < 3);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to prevent duplicate submissions (same handle/platform within 7 days)
CREATE OR REPLACE FUNCTION check_duplicate_submission(p_handle TEXT, p_platform TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    existing_count INTEGER;
BEGIN
    -- Check for existing pending/approved submissions
    SELECT COUNT(*) INTO existing_count
    FROM influencer_submissions
    WHERE LOWER(handle) = LOWER(p_handle)
    AND platform = p_platform
    AND status IN ('pending', 'analyzing', 'approved')
    AND created_at > NOW() - INTERVAL '7 days';

    RETURN (existing_count = 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_submission_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_influencer_submissions_timestamp ON influencer_submissions;
CREATE TRIGGER update_influencer_submissions_timestamp
    BEFORE UPDATE ON influencer_submissions
    FOR EACH ROW
    EXECUTE FUNCTION update_submission_timestamp();

-- View for admin dashboard (pending submissions needing review)
CREATE OR REPLACE VIEW pending_submissions AS
SELECT
    id,
    handle,
    platform,
    reason,
    status,
    trust_score,
    analysis_completed_at,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as hours_waiting
FROM influencer_submissions
WHERE status IN ('pending', 'analyzing')
ORDER BY created_at ASC;

-- User votes table (crowdsourcing trust scores)
CREATE TABLE IF NOT EXISTS influencer_votes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Vote target
    influencer_handle TEXT NOT NULL,
    influencer_platform TEXT NOT NULL DEFAULT 'instagram',

    -- Vote data
    vote_type TEXT NOT NULL CHECK (vote_type IN ('trust', 'distrust')),  -- trust = thumbs up, distrust = thumbs down
    vote_weight DECIMAL(3, 2) DEFAULT 1.00 CHECK (vote_weight >= 0 AND vote_weight <= 1.00),  -- Weight for weighted voting (future use)

    -- Voter tracking (anonymized for privacy)
    voter_ip_hash TEXT NOT NULL,  -- SHA-256 hash of IP address
    voter_session_hash TEXT,  -- Optional session fingerprint

    -- Optional feedback
    comment TEXT,  -- Optional comment explaining the vote (max 500 chars)

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT comment_length CHECK (char_length(comment) <= 500),
    -- One vote per IP per influencer (can update vote, not create duplicate)
    UNIQUE(influencer_handle, influencer_platform, voter_ip_hash)
);

-- Create indexes for vote queries and aggregations
CREATE INDEX IF NOT EXISTS idx_votes_influencer ON influencer_votes(influencer_handle, influencer_platform);
CREATE INDEX IF NOT EXISTS idx_votes_type ON influencer_votes(vote_type);
CREATE INDEX IF NOT EXISTS idx_votes_created ON influencer_votes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_votes_voter ON influencer_votes(voter_ip_hash);

-- Enable Row Level Security
ALTER TABLE influencer_votes ENABLE ROW LEVEL SECURITY;

-- Service role can do anything (for backend API)
DROP POLICY IF EXISTS "Service role can do anything on influencer_votes" ON influencer_votes;
CREATE POLICY "Service role can do anything on influencer_votes"
    ON influencer_votes
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Anon users can insert and update their own votes
DROP POLICY IF EXISTS "Anon can insert votes" ON influencer_votes;
CREATE POLICY "Anon can insert votes"
    ON influencer_votes
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Function to check vote rate limit (max 20 votes per IP per hour to prevent spam)
CREATE OR REPLACE FUNCTION check_vote_rate_limit(p_ip_hash TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    vote_count INTEGER;
BEGIN
    -- Check IP-based rate limit (max 20 votes per hour)
    SELECT COUNT(*) INTO vote_count
    FROM influencer_votes
    WHERE voter_ip_hash = p_ip_hash
    AND created_at > NOW() - INTERVAL '1 hour';

    RETURN (vote_count < 20);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to calculate user trust score for an influencer
CREATE OR REPLACE FUNCTION calculate_user_trust_score(p_handle TEXT, p_platform TEXT)
RETURNS DECIMAL(3, 2) AS $$
DECLARE
    trust_votes INTEGER;
    distrust_votes INTEGER;
    total_votes INTEGER;
    trust_score DECIMAL(3, 2);
BEGIN
    -- Count trust votes
    SELECT COUNT(*) INTO trust_votes
    FROM influencer_votes
    WHERE LOWER(influencer_handle) = LOWER(p_handle)
    AND influencer_platform = p_platform
    AND vote_type = 'trust';

    -- Count distrust votes
    SELECT COUNT(*) INTO distrust_votes
    FROM influencer_votes
    WHERE LOWER(influencer_handle) = LOWER(p_handle)
    AND influencer_platform = p_platform
    AND vote_type = 'distrust';

    total_votes := trust_votes + distrust_votes;

    -- If no votes, return 0.50 (neutral)
    IF total_votes = 0 THEN
        RETURN 0.50;
    END IF;

    -- Calculate score: trust_votes / total_votes
    -- Add smoothing: (trust_votes + 2) / (total_votes + 4) to prevent extreme scores with few votes
    trust_score := (trust_votes::DECIMAL + 2) / (total_votes::DECIMAL + 4);

    -- Ensure score is between 0.00 and 1.00
    trust_score := GREATEST(0.00, LEAST(1.00, trust_score));

    RETURN trust_score;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's vote for an influencer
CREATE OR REPLACE FUNCTION get_user_vote(p_handle TEXT, p_platform TEXT, p_ip_hash TEXT)
RETURNS TEXT AS $$
DECLARE
    vote_type TEXT;
BEGIN
    SELECT influencer_votes.vote_type INTO vote_type
    FROM influencer_votes
    WHERE LOWER(influencer_handle) = LOWER(p_handle)
    AND influencer_platform = p_platform
    AND voter_ip_hash = p_ip_hash;

    RETURN vote_type;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update updated_at timestamp on votes
CREATE OR REPLACE FUNCTION update_vote_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_influencer_votes_timestamp ON influencer_votes;
CREATE TRIGGER update_influencer_votes_timestamp
    BEFORE UPDATE ON influencer_votes
    FOR EACH ROW
    EXECUTE FUNCTION update_vote_timestamp();

-- Add user_trust_score to marketplace_influencers table
ALTER TABLE marketplace_influencers
ADD COLUMN IF NOT EXISTS user_trust_score DECIMAL(3, 2) DEFAULT 0.50,
ADD COLUMN IF NOT EXISTS total_votes INTEGER DEFAULT 0;

-- Create index for user trust score
CREATE INDEX IF NOT EXISTS idx_marketplace_user_trust_score ON marketplace_influencers(user_trust_score DESC);

-- View for vote statistics by influencer
CREATE OR REPLACE VIEW influencer_vote_stats AS
SELECT
    influencer_handle,
    influencer_platform,
    COUNT(*) as total_votes,
    SUM(CASE WHEN vote_type = 'trust' THEN 1 ELSE 0 END) as trust_votes,
    SUM(CASE WHEN vote_type = 'distrust' THEN 1 ELSE 0 END) as distrust_votes,
    calculate_user_trust_score(influencer_handle, influencer_platform) as user_trust_score,
    MAX(created_at) as last_vote_at
FROM influencer_votes
GROUP BY influencer_handle, influencer_platform
ORDER BY total_votes DESC;
