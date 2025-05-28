"""
Setup script for the Enhanced Maze Game
Run this to check dependencies and set up the environment
"""

import sys
import os
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_and_install_packages():
    """Check and install required packages"""
    required_packages = [
        "pygame",
        "supabase",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ All packages installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please install manually:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    
    return True

def create_env_file():
    """Create .env file template if it doesn't exist"""
    env_file = ".env"
    
    if os.path.exists(env_file):
        print("✅ .env file already exists")
        return True
    
    env_template = """# Supabase Configuration
# Get these values from your Supabase project dashboard
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Optional: Set to False to disable database features
ENABLE_DATABASE=True

# Game Settings (optional)
DEBUG_MODE=False
"""
    
    try:
        with open(env_file, "w") as f:
            f.write(env_template)
        print("✅ Created .env template file")
        print("📝 Please edit .env with your Supabase credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_game_files():
    """Check if required game files exist"""
    required_files = [
        "game_map.py",
        "supabase_handler.py",
        "Raycasting_test.py"
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} found")
        else:
            missing_files.append(file)
            print(f"❌ {file} missing")
    
    if missing_files:
        print(f"\n❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    return True

def test_database_connection():
    """Test if database connection works"""
    try:
        from supabase_handler import GameSupabaseHandler
        
        # Try to create handler (this will test env vars)
        handler = GameSupabaseHandler()
        print("✅ Database handler created successfully")
        
        # Test basic connection
        result = handler.supabase.table('user_profiles').select('id').limit(1).execute()
        print("✅ Database connection test passed")
        return True
        
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("💡 The game will still work in offline mode")
        return False

def run_setup():
    """Run the complete setup process"""
    print("🎮 Enhanced Maze Game Setup")
    print("=" * 40)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    print()
    
    # Check and install packages
    if not check_and_install_packages():
        success = False
    
    print()
    
    # Create .env file
    if not create_env_file():
        success = False
    
    print()
    
    # Check game files
    if not check_game_files():
        success = False
    
    print()
    
    # Test database (optional)
    print("🔗 Testing database connection...")
    db_works = test_database_connection()
    
    print()
    print("=" * 40)
    
    if success:
        print("✅ Setup completed successfully!")
        print()
        print("🚀 To start the game, run:")
        print("   python Raycasting_test.py")
        print()
        
        if not db_works:
            print("💡 Database features are disabled. To enable:")
            print("   1. Create a Supabase project at https://supabase.com")
            print("   2. Run the SQL schema in your Supabase SQL editor")
            print("   3. Update your .env file with the correct credentials")
        else:
            print("🎉 All features are ready to use!")
        
        print()
        print("📖 Controls:")
        print("   WASD/Arrow Keys - Move")
        print("   Q/E - Strafe")
        print("   M - Toggle minimap")
        print("   R - Generate new maze")
        print("   ESC - Menu")
        
    else:
        print("❌ Setup failed. Please fix the issues above and try again.")
    
    return success

if __name__ == "__main__":
    run_setup()
