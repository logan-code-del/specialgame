"""
Configuration file for the Enhanced Maze Game
"""

# Game Settings
GAME_SETTINGS = {
    "screen_width": 960,  # SCREEN_HEIGHT * 2
    "screen_height": 480,
    "resizable": True,
    "vision_range": 6,  # How many tiles the player can see
    "movement_speed": 1.0,
    "auto_save_interval": 30,  # seconds
    "win_exploration_percentage": 0.8  # 80% exploration to win
}

# Scoring Settings
SCORING = {
    "exploration_points_per_tile": 10,
    "time_bonus_max": 1000,
    "speed_bonus_multiplier": 1.5
}

# Database Settings (these should be in your .env file)
DATABASE_CONFIG = {
    "auto_save": True,
    "guest_mode_enabled": True,
    "leaderboard_limit": 10,
    "max_backup_age_days": 7
}

# UI Colors (RGB tuples)
COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gray": (128, 128, 128),
    "blue": (0, 100, 200),
    "green": (0, 200, 0),
    "red": (200, 0, 0),
    "yellow": (255, 255, 0),
    "gold": (255, 215, 0),
    "sky": (0, 150, 200),
    "floor": (100, 100, 75)
}

# Key bindings
CONTROLS = {
    "move_forward": ["w", "up"],
    "move_backward": ["s", "down"],
    "turn_left": ["a", "left"],
    "turn_right": ["d", "right"],
    "strafe_left": ["q"],
    "strafe_right": ["e"],
    "toggle_minimap": ["m"],
    "regenerate_maze": ["r"],
    "complete_game": ["c"],
    "pause_menu": ["escape"]
}

# Achievement definitions
ACHIEVEMENTS = {
    "first_game": {
        "name": "First Steps",
        "description": "Complete your first maze",
        "condition": "games_completed >= 1"
    },
    "speed_runner": {
        "name": "Speed Runner",
        "description": "Complete a maze in under 60 seconds",
        "condition": "completion_time < 60"
    },
    "explorer": {
        "name": "Explorer",
        "description": "Explore 100% of a maze",
        "condition": "exploration_percentage >= 1.0"
    },
    "high_scorer": {
        "name": "High Scorer",
        "description": "Score over 1000 points in a single game",
        "condition": "score >= 1000"
    },
    "persistent": {
        "name": "Persistent",
        "description": "Play 10 games",
        "condition": "games_played >= 10"
    }
}