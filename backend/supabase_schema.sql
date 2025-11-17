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
