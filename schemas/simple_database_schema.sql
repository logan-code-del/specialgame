-- Simple Maze Game Database Schema
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
    created_at TIMESTAMPTZ DEFAULT NOW()
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
    completed BOOLEAN DEFAULT FALSE
);

-- ==================== PLAYER PROGRESS TABLE ====================
CREATE TABLE IF NOT EXISTS player_progress (
    id BIGSERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    game_session_id BIGINT REFERENCES game_sessions(id) ON DELETE SET NULL,
    score INTEGER NOT NULL DEFAULT 0,
    maze_size TEXT,
    completion_time REAL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
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
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== MAZE RATINGS TABLE ====================
CREATE TABLE IF NOT EXISTS maze_ratings (
    id BIGSERIAL PRIMARY KEY,
    maze_id BIGINT REFERENCES mazes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(maze_id, user_id)
);

-- ==================== FRIENDSHIPS TABLE ====================
CREATE TABLE IF NOT EXISTS friendships (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    friend_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, friend_id)
);

-- ==================== USER ACHIEVEMENTS TABLE ====================
CREATE TABLE IF NOT EXISTS user_achievements (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    achievement_id TEXT NOT NULL,
    achievement_name TEXT NOT NULL,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- ==================== GAME BACKUPS TABLE ====================
CREATE TABLE IF NOT EXISTS game_backups (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    maze_data JSONB NOT NULL,
    player_x REAL NOT NULL,
    player_y REAL NOT NULL,
    player_angle REAL NOT NULL,
    current_score INTEGER DEFAULT 0,
    saved_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== ISSUE REPORTS TABLE ====================
CREATE TABLE IF NOT EXISTS issue_reports (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    username TEXT,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    reported_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== ENABLE ROW LEVEL SECURITY ====================
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE mazes ENABLE ROW LEVEL SECURITY;
ALTER TABLE maze_ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE friendships ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_backups ENABLE ROW LEVEL SECURITY;
ALTER TABLE issue_reports ENABLE ROW LEVEL SECURITY;

-- ==================== BASIC POLICIES ====================

-- Allow anyone to read leaderboards
CREATE POLICY "Anyone can view progress" ON player_progress FOR SELECT USING (true);
CREATE POLICY "Anyone can insert progress" ON player_progress FOR INSERT WITH CHECK (true);

-- Allow anyone to view public mazes
CREATE POLICY "Anyone can view public mazes" ON mazes FOR SELECT USING (is_public = true);

-- Users can manage their own data
CREATE POLICY "Users can manage own profile" ON user_profiles FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own sessions" ON game_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own mazes" ON mazes FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own ratings" ON maze_ratings FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own friendships" ON friendships FOR ALL USING (auth.uid() = user_id OR auth.uid() = friend_id);
CREATE POLICY "Users can manage own achievements" ON user_achievements FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own backups" ON game_backups FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own reports" ON issue_reports FOR ALL USING (auth.uid() = user_id);

-- ==================== AUTO-CREATE USER PROFILE ====================
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

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==================== GRANT PERMISSIONS ====================
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
