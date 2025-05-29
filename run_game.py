#!/usr/bin/env python3
"""
Maze Game Launcher
This script starts the menu application
"""

import subprocess
import sys
import os

def main():
    """Launch the maze game menu"""
    try:
        # Check if required files exist
        required_files = [
            'menu_app.py',
            'maze_game.py',
            'supabase_handler.py',
            'game_map.py',
            '.env',
            'maze_generator.py',
            'chat_interface.py'  # Added chat_interface.py to required files
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            return 1
        
        print("🎮 Starting Maze Game...")
        
        # Launch the menu application
        subprocess.run([sys.executable, 'menu_app.py'], check=True)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Game interrupted by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Menu application failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())