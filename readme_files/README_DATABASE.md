# Supabase Database Handler

This README explains how to set up and use the Supabase database handler for your raycasting maze game.

## Table of Contents
- [What is Supabase?](#what-is-supabase)
- [Setting Up Supabase](#setting-up-supabase)
- [Getting Your Supabase URL and Key](#getting-your-supabase-url-and-key)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [Usage Examples](#usage-examples)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

## What is Supabase?

Supabase is an open-source Firebase alternative that provides:
- PostgreSQL database
- Real-time subscriptions
- Authentication
- Auto-generated APIs
- Dashboard for managing data

It's perfect for storing game data like player scores, maze layouts, and progress tracking.

## Setting Up Supabase

### Step 1: Create a Supabase Account
1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign up with GitHub, Google, or email
4. Verify your email if required

### Step 2: Create a New Project
1. Click "New Project" on your dashboard
2. Choose your organization (or create one)
3. Fill in project details:
   - **Name**: `maze-game-db` (or any name you prefer)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to your location
4. Click "Create new project"
5. Wait 2-3 minutes for setup to complete

## Getting Your Supabase URL and Key

### Step 1: Find Your Project Settings
1. Go to your Supabase project dashboard
2. Click on the "Settings" icon (gear icon) in the left sidebar
3. Click on "API" in the settings menu

### Step 2: Copy Your Credentials
You'll see two important values:

**Project URL:**
```
https://your-project-id.supabase.co
```

**API Keys:**
- `anon` `public` - This is your public key (safe to use in client-side code)
- `service_role` `secret` - This is your secret key (keep this private!)

For this game, you'll use the **anon/public** key.

### Step 3: Copy the Values
```
URL: https://abcdefghijklmnop.supabase.co
Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS...
```

## Installation

### Step 1: Install Required Packages
```bash
pip install supabase python-dotenv
```

### Step 2: Download the Database Handler
Make sure you have the `supabase_handler.py` file in your project directory.

## Configuration

### Method 1: Using Environment Variables (Recommended)

Create a `.env` file in your project directory:

```bash:c:\Users\logan\OneDrive\Pictures\Documents\aaronsgame\.env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

**Important:** Add `.env` to your `.gitignore` file to keep your keys private!

```gitignore:c:\Users\logan\OneDrive\Pictures\Documents\aaronsgame\.gitignore
.env
__pycache__/
*.pyc
```

### Method 2: Using Direct Parameters

```python
from supabase_handler import SupabaseHandler

db = SupabaseHandler(
    url="https://your-project-id.supabase.co",
    key="your-anon-key-here"
)
```

### Method 3: Using System Environment Variables

**Windows:**
```cmd
set SUPABASE_URL=https://your-project-id.supabase.co
set SUPABASE_KEY=your-anon-key-here
```

**Mac/Linux:**
```bash
export SUPABASE_URL=https://your-project-id.supabase.co
export SUPABASE_KEY=your-anon-key-here
```

## Database Schema

### Recommended Tables for Your Maze Game

#### 1. Player Progress Table
```sql
CREATE TABLE player_progress (
    id BIGSERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    level INTEGER DEFAULT 1,
    score INTEGER DEFAULT 0,
    maze_size TEXT,
    completion_time REAL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 2. Mazes Table
```sql
CREATE TABLE mazes (
    id BIGSERIAL PRIMARY KEY,
    maze_name TEXT NOT NULL,
    maze_data JSONB NOT NULL,
    difficulty TEXT DEFAULT 'medium',
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3. Game Sessions Table
```sql
CREATE TABLE game_sessions (
    id BIGSERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    session_start TIMESTAMPTZ DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    total_score INTEGER DEFAULT 0,
    mazes_completed INTEGER DEFAULT 0
);
```

### Creating Tables in Supabase

1. Go to your Supabase project dashboard
2. Click "SQL Editor" in the left sidebar
3. Click "New Query"
4. Copy and paste the SQL above
5. Click "Run" to create the tables

## Usage Examples

### Basic Setup
```python
from supabase_handler import SupabaseHandler
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize database handler
db = SupabaseHandler()
```

### Saving Player Progress
```python
# Save a player's game completion
player_data = {
    "player_name": "Aaron",
    "level": 5,
    "score": 1250,
    "maze_size": "20x20",
    "completion_time": 45.7
}

result = db.add_record("player_progress", player_data)
print(f"Saved player progress: {result}")
```

### Getting High Scores
```python
# Get top 10 high scores
leaderboard = db.get_records_with_custom_query(
    "player_progress",
    select_columns="player_name, score, level, completion_time",
    order_by="score.desc",
    limit=10
)

print("=== LEADERBOARD ===")
for i, player in enumerate(leaderboard, 1):
    print(f"{i}. {player['player_name']}: {player['score']} points")
```

### Saving and Loading Mazes
```python
import json

# Save a maze
maze_layout = [
    ['#', '#', '#', '#'],
    ['#', '.', '.', '#'],
    ['#', '.', '.', '#'],
    ['#', '#', '#', '#']
]

maze_data = {
    "maze_name": "Test Maze",
    "maze_data": maze_layout,
    "difficulty": "easy",
    "width": 4,
    "height": 4
}

saved_maze = db.add_record("mazes", maze_data)

# Load a maze
loaded_maze = db.get_record_by_id("mazes", saved_maze['id'])
maze_layout = loaded_maze['maze_data']
```

### Integration with Your Game
```python
# In your Raycasting_test.py file, add this at the top:
from supabase_handler import SupabaseHandler
from dotenv import load_dotenv

load_dotenv()
db = SupabaseHandler()

# Save progress when player completes a maze
def save_game_progress(player_name, score, completion_time):
    progress_data = {
        "player_name": player_name,
        "score": score,
        "maze_size": f"{MAP_WIDTH}x{MAP_HEIGHT}",
        "completion_time": completion_time,
        "level": 1  # You can track levels
    }
    return db.add_record("player_progress", progress_data)

# Get player's best score
def get_player_best_score(player_name):
    scores = db.get_records_with_custom_query(
        "player_progress",
        filters={"player_name": player_name},
        order_by="score.desc",
        limit=1
    )
    return scores[0] if scores else None
```

## Environment Variables

### Using python-dotenv (Recommended)

Install python-dotenv:
```bash
pip install python-dotenv
```

Create `.env` file:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

Use in your code:
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

# Now you can use os.getenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
```

## Troubleshooting

### Common Issues

#### 1. "Supabase URL and KEY must be provided"
**Solution:** Make sure your environment variables are set correctly.

```python
# Debug your environment variables
import os
print("URL:", os.getenv('SUPABASE_URL'))
print("KEY:", os.getenv('SUPABASE_KEY'))
```

#### 2. "Connection failed" or "Invalid API key"
**Solutions:**
- Double-check your URL and key from Supabase dashboard
- Make sure you're using the `anon` key, not the `service_role` key
- Verify your project is active in Supabase

#### 3. "Table doesn't exist"
**Solution:** Create the tables using the SQL editor in Supabase dashboard.

#### 4. "Permission denied"
**Solution:** Check your Row Level Security (RLS) policies in Supabase.

For development, you can disable RLS:
1. Go to "Authentication" > "Policies" in Supabase
2. Find your table
3. Click "Disable RLS" (only for development!)

### Testing Your Connection

```python
# test_connection.py
from supabase_handler import SupabaseHandler
from dotenv import load_dotenv

load_dotenv()

try:
    db = SupabaseHandler()
    print("✅ Successfully connected to Supabase!")
    
    # Test with a simple query (this might fail if no tables exist yet)
    # tables = db.supabase.table('player_progress').select('*').limit(1).execute()
    # print("✅ Database query successful!")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Getting Help

1. **Supabase Documentation:** [https://supabase.com/docs](https://supabase.com/docs)
2. **Python Client Docs:** [https://supabase.com/docs/reference/python](https://supabase.com/docs/reference/python)
3. **Supabase Discord:** [https://discord.supabase.com](https://discord.supabase.com)

## Security Best Practices

1. **Never commit your `.env` file** - Add it to `.gitignore`
2. **Use the `anon` key** for client-side operations
3. **Set up Row Level Security (RLS)** for production
4. **Validate data** before sending to database
5. **Use environment variables** instead of hardcoding keys

## Next Steps

1. Set up your Supabase project
2. Create the recommended tables
3. Test the connection with the provided examples
4. Integrate database operations into your maze game
5. Add features like leaderboards, player profiles, and maze sharing

Happy coding! 🎮
