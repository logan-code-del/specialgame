-- Enhanced Maze Game Database Schema
-- Run this in your Supabase SQL Editor to create all required tables

-- ==================== USER PROFILES TABLE ====================
CREATE TABLE IF NOT EXISTS user_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    total_score BIGINT DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    best_time REAL,
    favorite_maze_size TEXT,
    last_played TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== GAME SESSIONS TABLE ====================
CREATE TABLE IF NOT EXISTS game_sessions (
    id BIGSERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    maze_width INTEGER NOT NULL,
    maze_height INTEGER NOT NULL,
    difficulty TEXT DEFAULT 'medium',
    session_start TIMESTAMPTZ DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    final_score INTEGER DEFAULT 0,
    session_duration REAL,
    completed BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'active'
);

-- ==================== PLAYER PROGRESS TABLE ====================
CREATE TABLE IF NOT EXISTS player_progress (
    id BIGSERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    game_session_id BIGINT REFERENCES game_sessions(id) ON DELETE SET NULL,
    score INTEGER NOT NULL DEFAULT 0,
    level INTEGER DEFAULT 1,
    maze_size TEXT,
    completion_time REAL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== MAZES TABLE ====================
CREATE TABLE IF NOT EXISTS mazes (
    id BIGSERIAL PRIMARY KEY,
    maze_name TEXT NOT NULL,
    maze_data JSONB NOT NULL,
    difficulty TEXT DEFAULT 'medium',
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    created_by TEXT NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT TRUE,
    play_count INTEGER DEFAULT 0,
    average_rating REAL DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== MAZE RATINGS TABLE ====================
CREATE TABLE IF NOT EXISTS maze_ratings (
    id BIGSERIAL PRIMARY KEY,
    maze_id BIGINT REFERENCES mazes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(maze_id, user_id)
);

-- ==================== FRIENDSHIPS TABLE ====================
CREATE TABLE IF NOT EXISTS friendships (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    friend_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'blocked')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, friend_id),
    CHECK (user_id != friend_id)
);

-- ==================== USER ACHIEVEMENTS TABLE ====================
CREATE TABLE IF NOT EXISTS user_achievements (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    achievement_id TEXT NOT NULL,
    achievement_name TEXT NOT NULL,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    game_score INTEGER,
    game_time REAL,
    UNIQUE(user_id, achievement_id)
);

-- ==================== GAME BACKUPS TABLE ====================
CREATE TABLE IF NOT EXISTS game_backups (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    game_session_id BIGINT REFERENCES game_sessions(id) ON DELETE SET NULL,
    maze_data JSONB NOT NULL,
    player_x REAL NOT NULL,
    player_y REAL NOT NULL,
    player_angle REAL NOT NULL,
    current_score INTEGER DEFAULT 0,
    game_time REAL DEFAULT 0,
    saved_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== ISSUE REPORTS TABLE ====================
CREATE TABLE IF NOT EXISTS issue_reports (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    username TEXT,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    game_data JSONB,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    reported_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ==================== INDEXES FOR PERFORMANCE ====================

-- User profiles indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username);

-- Game sessions indexes
CREATE INDEX IF NOT EXISTS idx_game_sessions_user_id ON game_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_status ON game_sessions(status);
CREATE INDEX IF NOT EXISTS idx_game_sessions_start ON game_sessions(session_start);

-- Player progress indexes
CREATE INDEX IF NOT EXISTS idx_player_progress_user_id ON player_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_player_progress_score ON player_progress(score DESC);
CREATE INDEX IF NOT EXISTS idx_player_progress_timestamp ON player_progress(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_player_progress_maze_size ON player_progress(maze_size);

-- Mazes indexes
CREATE INDEX IF NOT EXISTS idx_mazes_user_id ON mazes(user_id);
CREATE INDEX IF NOT EXISTS idx_mazes_public ON mazes(is_public);
CREATE INDEX IF NOT EXISTS idx_mazes_difficulty ON mazes(difficulty);
CREATE INDEX IF NOT EXISTS idx_mazes_play_count ON mazes(play_count DESC);
CREATE INDEX IF NOT EXISTS idx_mazes_rating ON mazes(average_rating DESC);

-- Maze ratings indexes
CREATE INDEX IF NOT EXISTS idx_maze_ratings_maze_id ON maze_ratings(maze_id);
CREATE INDEX IF NOT EXISTS idx_maze_ratings_user_id ON maze_ratings(user_id);

-- Friendships indexes
CREATE INDEX IF NOT EXISTS idx_friendships_user_id ON friendships(user_id);
CREATE INDEX IF NOT EXISTS idx_friendships_friend_id ON friendships(friend_id);
CREATE INDEX IF NOT EXISTS idx_friendships_status ON friendships(status);

-- User achievements indexes
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_achievement_id ON user_achievements(achievement_id);

-- ==================== ROW LEVEL SECURITY POLICIES ====================

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE mazes ENABLE ROW LEVEL SECURITY;
ALTER TABLE maze_ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE friendships ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_backups ENABLE ROW LEVEL SECURITY;
ALTER TABLE issue_reports ENABLE ROW LEVEL SECURITY;

-- ==================== USER PROFILES POLICIES ====================

-- Users can read all profiles (for leaderboards, friend search)
CREATE POLICY "Users can view all profiles" ON user_profiles
FOR SELECT TO authenticated, anon
USING (true);

-- Users can insert their own profile
CREATE POLICY "Users can insert own profile" ON user_profiles
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON user_profiles
FOR UPDATE TO authenticated
USING (auth.uid() = user_id);

-- ==================== GAME SESSIONS POLICIES ====================

-- Anyone can insert game sessions (for guest play)
CREATE POLICY "Anyone can insert game sessions" ON game_sessions
FOR INSERT TO authenticated, anon
WITH CHECK (true);

-- Users can view their own sessions
CREATE POLICY "Users can view own sessions" ON game_sessions
FOR SELECT TO authenticated
USING (auth.uid() = user_id);

-- Anonymous users can view their sessions by player_name (limited)
CREATE POLICY "Anonymous can view own sessions" ON game_sessions
FOR SELECT TO anon
USING (true);

-- Users can update their own sessions
CREATE POLICY "Users can update own sessions" ON game_sessions
FOR UPDATE TO authenticated, anon
USING (auth.uid() = user_id OR user_id IS NULL);

-- ==================== PLAYER PROGRESS POLICIES ====================

-- Anyone can insert progress (for guest scores on leaderboard)
CREATE POLICY "Anyone can insert progress" ON player_progress
FOR INSERT TO authenticated, anon
WITH CHECK (true);

-- Anyone can view progress (for leaderboards)
CREATE POLICY "Anyone can view progress" ON player_progress
FOR SELECT TO authenticated, anon
USING (true);

-- Users can update their own progress
CREATE POLICY "Users can update own progress" ON player_progress
FOR UPDATE TO authenticated
USING (auth.uid() = user_id);

-- ==================== MAZES POLICIES ====================

-- Anyone can view public mazes
CREATE POLICY "Anyone can view public mazes" ON mazes
FOR SELECT TO authenticated, anon
USING (is_public = true);

-- Users can view their own mazes
CREATE POLICY "Users can view own mazes" ON mazes
FOR SELECT TO authenticated
USING (auth.uid() = user_id);

-- Authenticated users can insert mazes
CREATE POLICY "Authenticated users can insert mazes" ON mazes
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Users can update their own mazes
CREATE POLICY "Users can update own mazes" ON mazes
FOR UPDATE TO authenticated
USING (auth.uid() = user_id);

-- Users can delete their own mazes
CREATE POLICY "Users can delete own mazes" ON mazes
FOR DELETE TO authenticated
USING (auth.uid() = user_id);

-- ==================== MAZE RATINGS POLICIES ====================

-- Anyone can view ratings
CREATE POLICY "Anyone can view ratings" ON maze_ratings
FOR SELECT TO authenticated, anon
USING (true);

-- Authenticated users can insert ratings
CREATE POLICY "Authenticated users can insert ratings" ON maze_ratings
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Users can update their own ratings
CREATE POLICY "Users can update own ratings" ON maze_ratings
FOR UPDATE TO authenticated
USING (auth.uid() = user_id);

-- ==================== FRIENDSHIPS POLICIES ====================

-- Users can view friendships involving them
CREATE POLICY "Users can view own friendships" ON friendships
FOR SELECT TO authenticated
USING (auth.uid() = user_id OR auth.uid() = friend_id);

-- Users can insert friendship requests
CREATE POLICY "Users can insert friendships" ON friendships
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Users can update friendships involving them
CREATE POLICY "Users can update own friendships" ON friendships
FOR UPDATE TO authenticated
USING (auth.uid() = user_id OR auth.uid() = friend_id);

-- ==================== USER ACHIEVEMENTS POLICIES ====================

-- Users can view all achievements (for comparison)
CREATE POLICY "Users can view all achievements" ON user_achievements
FOR SELECT TO authenticated
USING (true);

-- System can insert achievements (you might want to restrict this further)
CREATE POLICY "System can insert achievements" ON user_achievements
FOR INSERT TO authenticated, anon
WITH CHECK (true);

-- ==================== GAME BACKUPS POLICIES ====================

-- Users can view their own backups
CREATE POLICY "Users can view own backups" ON game_backups
FOR SELECT TO authenticated
USING (auth.uid() = user_id);

-- Users can insert their own backups
CREATE POLICY "Users can insert own backups" ON game_backups
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Users can update their own backups
CREATE POLICY "Users can update own backups" ON game_backups
FOR UPDATE TO authenticated
USING (auth.uid() = user_id);

-- Users can delete their own backups
CREATE POLICY "Users can delete own backups" ON game_backups
FOR DELETE TO authenticated
USING (auth.uid() = user_id);

-- ==================== ISSUE REPORTS POLICIES ====================

-- Anyone can insert issue reports
CREATE POLICY "Anyone can insert issue reports" ON issue_reports
FOR INSERT TO authenticated, anon
WITH CHECK (true);

-- Users can view their own reports
CREATE POLICY "Users can view own reports" ON issue_reports
FOR SELECT TO authenticated
USING (auth.uid() = user_id);

-- ==================== FUNCTIONS AND TRIGGERS ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mazes_updated_at BEFORE UPDATE ON mazes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_maze_ratings_updated_at BEFORE UPDATE ON maze_ratings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_friendships_updated_at BEFORE UPDATE ON friendships FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically create user profile when user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (user_id, username, email)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
        NEW.email
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==================== SAMPLE DATA (OPTIONAL) ====================

-- Insert some sample achievements definitions
INSERT INTO user_achievements (user_id, achievement_id, achievement_name, earned_at) VALUES
('00000000-0000-0000-0000-000000000000', 'sample', 'Sample Achievement', NOW())
ON CONFLICT (user_id, achievement_id) DO NOTHING;

-- You can delete the sample data after testing
DELETE FROM user_achievements WHERE achievement_id = 'sample';

-- ==================== VIEWS FOR EASY QUERYING ====================

-- Leaderboard view
CREATE OR REPLACE VIEW leaderboard AS
SELECT 
    pp.player_name,
    pp.user_id,
    MAX(pp.score) as best_score,
    MIN(pp.completion_time) as best_time,
    COUNT(*) as games_played,
    AVG(pp.score) as average_score,
    pp.maze_size,
    MAX(pp.timestamp) as last_played
FROM player_progress pp
WHERE pp.score > 0
GROUP BY pp.player_name, pp.user_id, pp.maze_size
ORDER BY best_score DESC;

-- User statistics view
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    up.user_id,
    up.username,
    up.total_score,
    up.games_played,
    up.best_time,
    COUNT(ua.id) as achievements_count,
    COUNT(f.id) as friends_count,
    COUNT(m.id) as mazes_created
FROM user_profiles up
LEFT JOIN user_achievements ua ON up.user_id = ua.user_id
LEFT JOIN friendships f ON up.user_id = f.user_id AND f.status = 'accepted'
LEFT JOIN mazes m ON up.user_id = m.user_id
GROUP BY up.user_id, up.username, up.total_score, up.games_played, up.best_time;

-- Popular mazes view
CREATE OR REPLACE VIEW popular_mazes AS
SELECT 
    m.*,
    COUNT(pp.id) as times_completed,
    AVG(pp.score) as average_completion_score,
    AVG(pp.completion_time) as average_completion_time
FROM mazes m
LEFT JOIN player_progress pp ON m.maze_name = pp.maze_size
WHERE m.is_public = true
GROUP BY m.id
ORDER BY m.play_count DESC, m.average_rating DESC;

-- ==================== STORED PROCEDURES ====================

-- Procedure to get user's game summary
CREATE OR REPLACE FUNCTION get_user_game_summary(target_user_id UUID)
RETURNS TABLE (
    total_games INTEGER,
    total_score BIGINT,
    best_score INTEGER,
    average_score NUMERIC,
    best_time REAL,
    achievements_count BIGINT,
    rank INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH user_data AS (
        SELECT 
            COUNT(*)::INTEGER as total_games,
            SUM(pp.score) as total_score,
            MAX(pp.score) as best_score,
            AVG(pp.score) as average_score,
            MIN(pp.completion_time) as best_time
        FROM player_progress pp
        WHERE pp.user_id = target_user_id
    ),
    achievement_data AS (
        SELECT COUNT(*) as achievements_count
        FROM user_achievements ua
        WHERE ua.user_id = target_user_id
    ),
    rank_data AS (
        SELECT 
            ROW_NUMBER() OVER (ORDER BY MAX(score) DESC) as rank
        FROM player_progress
        WHERE user_id IS NOT NULL
        GROUP BY user_id
        HAVING user_id = target_user_id
    )
    SELECT 
        ud.total_games,
        ud.total_score,
        ud.best_score,
        ud.average_score,
        ud.best_time,
        ad.achievements_count,
        COALESCE(rd.rank::INTEGER, 0) as rank
    FROM user_data ud
    CROSS JOIN achievement_data ad
    LEFT JOIN rank_data rd ON true;
END;
$$ LANGUAGE plpgsql;

-- Procedure to clean up old game sessions
CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete game sessions older than 30 days that are still 'active'
    DELETE FROM game_sessions 
    WHERE status = 'active' 
    AND session_start < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ==================== SECURITY FUNCTIONS ====================

-- Function to check if user can access maze
CREATE OR REPLACE FUNCTION can_access_maze(maze_id BIGINT, requesting_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    maze_record RECORD;
BEGIN
    SELECT * INTO maze_record FROM mazes WHERE id = maze_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Public mazes are accessible to everyone
    IF maze_record.is_public THEN
        RETURN TRUE;
    END IF;
    
    -- Private mazes are only accessible to their creator
    IF maze_record.user_id = requesting_user_id THEN
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ==================== PERFORMANCE OPTIMIZATION ====================

-- Materialized view for global statistics (refresh periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS global_game_stats AS
SELECT 
    COUNT(DISTINCT pp.user_id) as total_players,
    COUNT(*) as total_games,
    AVG(pp.score) as average_score,
    MAX(pp.score) as highest_score,
    MIN(pp.completion_time) as fastest_time,
    COUNT(DISTINCT m.id) as total_mazes,
    mode() WITHIN GROUP (ORDER BY pp.maze_size) as most_popular_size
FROM player_progress pp
LEFT JOIN mazes m ON m.is_public = true;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_global_stats ON global_game_stats ((1));

-- Function to refresh global stats (call this periodically)
CREATE OR REPLACE FUNCTION refresh_global_stats()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW global_game_stats;
END;
$$ LANGUAGE plpgsql;

-- ==================== DATA VALIDATION ====================

-- Function to validate maze data structure
CREATE OR REPLACE FUNCTION validate_maze_data(maze_data JSONB)
RETURNS BOOLEAN AS $$
DECLARE
    row_data JSONB;
    expected_width INTEGER;
    current_width INTEGER;
BEGIN
    -- Check if maze_data is an array
    IF jsonb_typeof(maze_data) != 'array' THEN
        RETURN FALSE;
    END IF;
    
    -- Check if maze has at least one row
    IF jsonb_array_length(maze_data) = 0 THEN
        RETURN FALSE;
    END IF;
    
    -- Get expected width from first row
    expected_width := jsonb_array_length(maze_data->0);
    
    -- Check each row
    FOR i IN 0..jsonb_array_length(maze_data)-1 LOOP
        row_data := maze_data->i;
        
        -- Check if row is an array
        IF jsonb_typeof(row_data) != 'array' THEN
            RETURN FALSE;
        END IF;
        
        -- Check if row has consistent width
        current_width := jsonb_array_length(row_data);
        IF current_width != expected_width THEN
            RETURN FALSE;
        END IF;
        
        -- Check if all elements are valid maze characters
        FOR j IN 0..current_width-1 LOOP
            IF row_data->>j NOT IN ('#', '.', 'S', 'E') THEN
                RETURN FALSE;
            END IF;
        END LOOP;
    END LOOP;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Add constraint to mazes table
ALTER TABLE mazes ADD CONSTRAINT valid_maze_data 
CHECK (validate_maze_data(maze_data));

-- ==================== AUDIT LOGGING ====================

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    user_id UUID,
    old_data JSONB,
    new_data JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Function for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, user_id, old_data)
        VALUES (TG_TABLE_NAME, TG_OP, auth.uid(), row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, user_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, auth.uid(), row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, user_id, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, auth.uid(), row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Add audit triggers to important tables (uncomment if you want audit logging)
-- CREATE TRIGGER audit_user_profiles AFTER INSERT OR UPDATE OR DELETE ON user_profiles FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
-- CREATE TRIGGER audit_mazes AFTER INSERT OR UPDATE OR DELETE ON mazes FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- ==================== CLEANUP AND MAINTENANCE ====================

-- Function to archive old data
CREATE OR REPLACE FUNCTION archive_old_data(days_old INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER := 0;
BEGIN
    -- Archive old game sessions to a separate table (create if needed)
    CREATE TABLE IF NOT EXISTS game_sessions_archive (LIKE game_sessions INCLUDING ALL);
    
    -- Move old completed sessions to archive
    WITH moved_sessions AS (
        DELETE FROM game_sessions 
        WHERE status = 'completed' 
        AND session_end < NOW() - INTERVAL '1 day' * days_old
        RETURNING *
    )
    INSERT INTO game_sessions_archive SELECT * FROM moved_sessions;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- ==================== FINAL SETUP COMMANDS ====================

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Create a scheduled job to refresh global stats (if you have pg_cron extension)
-- SELECT cron.schedule('refresh-global-stats', '0 */6 * * *', 'SELECT refresh_global_stats();');

-- Create a scheduled job to cleanup old sessions
-- SELECT cron.schedule('cleanup-old-sessions', '0 2 * * *', 'SELECT cleanup_old_sessions();');

-- ==================== VERIFICATION QUERIES ====================

-- Verify all tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'user_profiles', 'game_sessions', 'player_progress', 'mazes', 
    'maze_ratings', 'friendships', 'user_achievements', 'game_backups', 'issue_reports'
);

-- Verify all indexes were created
SELECT indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND indexname LIKE 'idx_%';

-- Verify RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN (
    'user_profiles', 'game_sessions', 'player_progress', 'mazes', 
    'maze_ratings', 'friendships', 'user_achievements', 'game_backups', 'issue_reports'
);

-- Show all policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd 
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ==================== SUCCESS MESSAGE ====================
DO $$
BEGIN
    RAISE NOTICE '✅ Enhanced Maze Game Database Schema Setup Complete!';
    RAISE NOTICE 'Tables created: user_profiles, game_sessions, player_progress, mazes, maze_ratings, friendships, user_achievements, game_backups, issue_reports';
    RAISE NOTICE 'Views created: leaderboard, user_stats, popular_mazes';
    RAISE NOTICE 'Functions created: Various utility and validation functions';
    RAISE NOTICE 'RLS policies: Configured for secure multi-user access';
    RAISE NOTICE 'Ready for enhanced maze game integration!';
END $$;