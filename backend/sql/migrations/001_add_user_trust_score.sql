-- Migration 001: add community voting support to marketplace_influencers
-- Safe to run multiple times – uses IF NOT EXISTS guards everywhere.

ALTER TABLE IF EXISTS marketplace_influencers
ADD COLUMN IF NOT EXISTS user_trust_score DECIMAL(3, 2) DEFAULT 0.50,
ADD COLUMN IF NOT EXISTS total_votes INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_marketplace_user_trust_score
    ON marketplace_influencers(user_trust_score DESC);

-- Refresh the influencer vote stats view so the new columns are reflected everywhere.
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
