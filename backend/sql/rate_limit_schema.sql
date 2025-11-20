-- Rate limiting table and functions
-- Run this migration to set up rate limiting for expensive API endpoints

-- Create rate_limits table
CREATE TABLE IF NOT EXISTS rate_limits (
    id BIGSERIAL PRIMARY KEY,
    client_ip TEXT NOT NULL,
    endpoint_group TEXT NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 0,
    window_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_request_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(client_ip, endpoint_group)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_rate_limits_client_endpoint
    ON rate_limits(client_ip, endpoint_group);

-- Index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_rate_limits_window_start
    ON rate_limits(window_start);

-- Function to check and increment rate limit
-- Returns: {allowed: boolean, current_count: integer, reset_at: timestamptz}
CREATE OR REPLACE FUNCTION check_and_increment_rate_limit(
    p_client_ip TEXT,
    p_endpoint_group TEXT,
    p_daily_limit INTEGER
)
RETURNS JSON AS $$
DECLARE
    v_record RECORD;
    v_current_count INTEGER;
    v_window_start TIMESTAMPTZ;
    v_reset_at TIMESTAMPTZ;
    v_allowed BOOLEAN;
BEGIN
    -- Calculate the start of the current UTC day
    v_window_start := DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC';
    v_reset_at := v_window_start + INTERVAL '1 day';

    -- Try to get existing record for this IP and endpoint group
    SELECT * INTO v_record
    FROM rate_limits
    WHERE client_ip = p_client_ip
      AND endpoint_group = p_endpoint_group
    FOR UPDATE;  -- Lock the row to prevent race conditions

    IF FOUND THEN
        -- Check if we're still in the same window (same UTC day)
        IF v_record.window_start >= v_window_start THEN
            -- Same window - check if under limit
            v_current_count := v_record.request_count;

            IF v_current_count < p_daily_limit THEN
                -- Under limit - increment and allow
                UPDATE rate_limits
                SET request_count = request_count + 1,
                    last_request_at = NOW()
                WHERE client_ip = p_client_ip
                  AND endpoint_group = p_endpoint_group;

                v_allowed := TRUE;
                v_current_count := v_current_count + 1;
            ELSE
                -- Over limit - deny
                v_allowed := FALSE;
            END IF;
        ELSE
            -- New window - reset counter
            UPDATE rate_limits
            SET request_count = 1,
                window_start = v_window_start,
                last_request_at = NOW()
            WHERE client_ip = p_client_ip
              AND endpoint_group = p_endpoint_group;

            v_allowed := TRUE;
            v_current_count := 1;
        END IF;
    ELSE
        -- No existing record - create new one
        INSERT INTO rate_limits (client_ip, endpoint_group, request_count, window_start, last_request_at)
        VALUES (p_client_ip, p_endpoint_group, 1, v_window_start, NOW());

        v_allowed := TRUE;
        v_current_count := 1;
    END IF;

    -- Return result as JSON
    RETURN json_build_object(
        'allowed', v_allowed,
        'current_count', v_current_count,
        'reset_at', v_reset_at
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get rate limit status without incrementing
CREATE OR REPLACE FUNCTION get_rate_limit_status(
    p_client_ip TEXT,
    p_endpoint_group TEXT
)
RETURNS JSON AS $$
DECLARE
    v_record RECORD;
    v_window_start TIMESTAMPTZ;
    v_reset_at TIMESTAMPTZ;
    v_current_count INTEGER;
BEGIN
    -- Calculate the start of the current UTC day
    v_window_start := DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC';
    v_reset_at := v_window_start + INTERVAL '1 day';

    -- Get existing record
    SELECT * INTO v_record
    FROM rate_limits
    WHERE client_ip = p_client_ip
      AND endpoint_group = p_endpoint_group;

    IF FOUND AND v_record.window_start >= v_window_start THEN
        -- Record exists and is current
        v_current_count := v_record.request_count;
    ELSE
        -- No record or expired
        v_current_count := 0;
    END IF;

    RETURN json_build_object(
        'current_count', v_current_count,
        'reset_at', v_reset_at
    );
END;
$$ LANGUAGE plpgsql;

-- Cleanup function to remove old rate limit records (optional, for maintenance)
-- Call this periodically to prevent table bloat
CREATE OR REPLACE FUNCTION cleanup_old_rate_limits()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Delete records older than 7 days
    DELETE FROM rate_limits
    WHERE window_start < NOW() - INTERVAL '7 days';

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- If you're using service role, these may not be necessary
-- GRANT SELECT, INSERT, UPDATE ON rate_limits TO authenticated;
-- GRANT EXECUTE ON FUNCTION check_and_increment_rate_limit TO authenticated;
-- GRANT EXECUTE ON FUNCTION get_rate_limit_status TO authenticated;
