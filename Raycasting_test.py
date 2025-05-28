import pygame
import sys
import math
import time
from datetime import datetime
from supabase_handler import GameSupabaseHandler

pygame.init()

SCREEN_HEIGHT = 480
SCREEN_WIDTH = SCREEN_HEIGHT * 2
RESIZEABLE_BOOL = True

from game_map import MAP

# Calculate map size and tile size based on the generated maze
MAP_WIDTH = len(MAP[0])
MAP_HEIGHT = len(MAP)
TILE_SIZE = ((SCREEN_WIDTH / 2) / max(MAP_WIDTH, MAP_HEIGHT))  # Adjust for largest dimension
MAX_DEPTH = int(max(MAP_WIDTH, MAP_HEIGHT) * TILE_SIZE)

FOV = math.pi / 3
HALF_FOV = FOV / 2
CASTED_RAYS = 120
STEP_ANGLE = FOV / CASTED_RAYS
SCALE = (SCREEN_WIDTH / 2) / CASTED_RAYS

# Fog of war settings
VISION_RANGE = 6  # How many tiles the player can see around them
RAY_RANGE = VISION_RANGE * TILE_SIZE  # Maximum ray distance for fog effect

# Player starting position - find a good spawn point
def find_spawn_position():
    """Find a good spawn position in the maze"""
    for y in range(1, min(5, MAP_HEIGHT - 1)):
        for x in range(1, min(5, MAP_WIDTH - 1)):
            if MAP[y][x] == '.':
                return (x + 0.5) * TILE_SIZE, (y + 0.5) * TILE_SIZE
    return TILE_SIZE * 1.5, TILE_SIZE * 1.5  # Fallback

player_x, player_y = find_spawn_position()
player_angle = math.pi

# Game state
show_minimap = False
explored_tiles = set()
game_state = "menu"  # menu, login, game, leaderboard, stats
current_score = 0
game_start_time = None
player_name = ""
input_text = ""
input_mode = None  # None, "name", "email", "password", "username"
login_mode = "signin"  # signin, signup
friend_search_text = ""
friend_message = ""
show_friends_menu = False
error_message = ""
success_message = ""
menu_selection = 0
login_data = {"email": "", "password": "", "username": ""}

# Initialize database handler
try:
    db_handler = GameSupabaseHandler()
    print("✅ Database connected successfully!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    db_handler = None

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BLUE = (0, 100, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0)

if RESIZEABLE_BOOL:
    win = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.RESIZABLE)
else:
    win = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))

pygame.display.set_caption("Enhanced Maze Game")
clock = pygame.time.Clock()

def update_explored_tiles():
    """Update the set of explored tiles based on player's current position and vision range"""
    player_tile_x = int(player_x / TILE_SIZE)
    player_tile_y = int(player_y / TILE_SIZE)
    
    for dy in range(-VISION_RANGE, VISION_RANGE + 1):
        for dx in range(-VISION_RANGE, VISION_RANGE + 1):
            tile_x = player_tile_x + dx
            tile_y = player_tile_y + dy
            
            if 0 <= tile_y < MAP_HEIGHT and 0 <= tile_x < MAP_WIDTH:
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= VISION_RANGE:
                    explored_tiles.add((tile_x, tile_y))

def is_tile_visible(tile_x, tile_y):
    """Check if a tile should be visible based on player's current position and vision range"""
    player_tile_x = int(player_x / TILE_SIZE)
    player_tile_y = int(player_y / TILE_SIZE)
    
    dx = tile_x - player_tile_x
    dy = tile_y - player_tile_y
    distance = math.sqrt(dx*dx + dy*dy)
    
    return distance <= VISION_RANGE

def draw_map():
    """Draw the minimap with fog of war"""
    if not show_minimap:
        return
    
    # Calculate minimap size to fit screen
    minimap_size = min(SCREEN_HEIGHT, SCREEN_WIDTH // 2)
    minimap_tile_size = minimap_size / max(MAP_WIDTH, MAP_HEIGHT)
    
    # Draw background for the map area
    pygame.draw.rect(win, (50, 50, 50), (0, 0, minimap_size, minimap_size))
    
    # Draw the map with fog of war
    for row in range(MAP_HEIGHT):
        for col in range(MAP_WIDTH):
            tile_pos = (col, row)
            
            if tile_pos in explored_tiles:
                if is_tile_visible(col, row):
                    color = (200,200,200) if MAP[row][col] == '#' else (100,100,100)
                    alpha = 255
                else:
                    color = (100,100,100) if MAP[row][col] == '#' else (50,50,50)
                    alpha = 128
                
                tile_surface = pygame.Surface((minimap_tile_size - 1, minimap_tile_size - 1))
                tile_surface.fill(color)
                tile_surface.set_alpha(alpha)
                
                win.blit(tile_surface, (col * minimap_tile_size, row * minimap_tile_size))
            else:
                pygame.draw.rect(win, (20, 20, 20), 
                               (col * minimap_tile_size, row * minimap_tile_size, 
                                minimap_tile_size - 1, minimap_tile_size - 1))
    
    # Draw player on minimap
    minimap_player_x = (player_x / TILE_SIZE) * minimap_tile_size
    minimap_player_y = (player_y / TILE_SIZE) * minimap_tile_size
    pygame.draw.circle(win, (255, 0, 0), (int(minimap_player_x), int(minimap_player_y)), 4)
    
    # Draw direction line
    end_x = minimap_player_x - math.sin(player_angle) * 20
    end_y = minimap_player_y + math.cos(player_angle) * 20
    pygame.draw.line(win, (0,255,0), (minimap_player_x, minimap_player_y), (end_x, end_y), 2)

def cast_rays():
    """Cast rays with proper handling for fog of war"""
    start_angle = player_angle - HALF_FOV
    
    for ray in range(CASTED_RAYS):
        hit_wall = False
        wall_distance = 0
        
        for depth in range(MAX_DEPTH):
            target_x = player_x - math.sin(start_angle) * depth
            target_y = player_y + math.cos(start_angle) * depth
            
            col = int(target_x / TILE_SIZE)
            row = int(target_y / TILE_SIZE)
            
            if 0 <= row < MAP_HEIGHT and 0 <= col < MAP_WIDTH:
                if MAP[row][col] == '#':
                    hit_wall = True
                    wall_distance = depth
                    break
            else:
                hit_wall = True
                wall_distance = depth
                break
        
        if hit_wall:
            if wall_distance <= RAY_RANGE:
                color = 255 / (1 + wall_distance * wall_distance * 0.0001)
            else:
                color = max(0, 50 / (1 + wall_distance * wall_distance * 0.001))
            
            corrected_distance = wall_distance * math.cos(player_angle - start_angle)
            wall_height = 21000 / (corrected_distance + 0.0001)
            
            if wall_height > SCREEN_HEIGHT:
                wall_height = SCREEN_HEIGHT
            
            pygame.draw.rect(win, (color, color, color),
                           (SCREEN_HEIGHT + ray * SCALE,
                           (SCREEN_HEIGHT / 2) - wall_height / 2,
                           SCALE, wall_height))
        else:
            pygame.draw.rect(win, (0, 0, 0),
                           (SCREEN_HEIGHT + ray * SCALE,
                           0,
                           SCALE, SCREEN_HEIGHT))
        
        start_angle += STEP_ANGLE

def is_valid_position(x, y):
    """Check if a position is valid (not in a wall and within bounds)"""
    margin = 8
    
    positions_to_check = [
        (x, y),
        (x - margin, y),
        (x + margin, y),
        (x, y - margin),
        (x, y + margin),
    ]
    
    for check_x, check_y in positions_to_check:
        col = int(check_x / TILE_SIZE)
        row = int(check_y / TILE_SIZE)
        
        if not (0 <= row < MAP_HEIGHT and 0 <= col < MAP_WIDTH):
            return False
        
        if MAP[row][col] == '#':
            return False
    
    return True

def regenerate_maze():
    """Generate a new maze and reset player position"""
    global MAP, player_x, player_y, explored_tiles, MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, MAX_DEPTH, RAY_RANGE
    
    # Import fresh maze
    import importlib
    import game_map
    importlib.reload(game_map)
    MAP = game_map.MAP
    
    # Recalculate dimensions
    MAP_WIDTH = len(MAP[0])
    MAP_HEIGHT = len(MAP)
    TILE_SIZE = ((SCREEN_WIDTH / 2) / max(MAP_WIDTH, MAP_HEIGHT))
    MAX_DEPTH = int(max(MAP_WIDTH, MAP_HEIGHT) * TILE_SIZE)
    RAY_RANGE = VISION_RANGE * TILE_SIZE
    
    # Reset player position
    player_x, player_y = find_spawn_position()
    
    # Clear exploration
    explored_tiles.clear()
    
    print(f"New maze generated: {MAP_HEIGHT} x {MAP_WIDTH}")
    print(f"New starting position: ({player_x}, {player_y})")

def calculate_score():
    """Calculate current score based on exploration and time"""
    global current_score
    if game_start_time:
        time_bonus = max(0, 1000 - int(time.time() - game_start_time))
        exploration_bonus = len(explored_tiles) * 10
        current_score = time_bonus + exploration_bonus
    return current_score

def start_new_game():
    """Start a new game session"""
    global game_start_time, current_score, explored_tiles, player_x, player_y, game_state
    
    game_start_time = time.time()
    current_score = 0
    explored_tiles.clear()
    player_x, player_y = find_spawn_position()
    game_state = "game"
    
    # Start database session if connected (no parameters needed)
    if db_handler and db_handler.is_authenticated():
        db_handler.start_game_session()
    
    print("🎮 New game started!")

def complete_game():
    """Complete the current game and save progress"""
    global game_state, current_score
    
    if not game_start_time:
        return
    
    completion_time = time.time() - game_start_time
    final_score = calculate_score()
    
    # Save to database if available
    if db_handler:
        if db_handler.is_authenticated():
            # Save authenticated user progress (now works correctly)
            progress = db_handler.save_game_progress(
                score=final_score,
                completion_time=completion_time,
                maze_size=f"{MAP_WIDTH}x{MAP_HEIGHT}"
            )
            
            # End game session
            db_handler.end_game_session(final_score, completed=True)
            
            if progress:
                print(f"✅ Progress saved! Score: {final_score}")
            else:
                print("❌ Failed to save progress")
        else:
            # Save guest progress
            guest_name = player_name if player_name else "Guest"
            progress = db_handler.save_guest_progress(
                player_name=guest_name,
                score=final_score,
                completion_time=completion_time,
                maze_size=f"{MAP_WIDTH}x{MAP_HEIGHT}"
            )
            
            if progress:
                print(f"✅ Guest progress saved! Score: {final_score}")
    
    game_state = "game_complete"
    return final_score, completion_time


def draw_text(text, x, y, color=WHITE, font_size=24, center=False):
    """Helper function to draw text"""
    font = pygame.font.SysFont('Arial', font_size)
    text_surface = font.render(str(text), True, color)
    
    if center:
        x = x - text_surface.get_width() // 2
    
    win.blit(text_surface, (x, y))
    return text_surface.get_height()

def draw_menu():
    """Draw the main menu"""
    win.fill(BLACK)
    
    # Title
    draw_text("ENHANCED MAZE GAME", SCREEN_WIDTH // 2, 50, GOLD, 36, center=True)
    
    # Menu options
    menu_options = [
        "1. Start New Game",
        "2. View Leaderboard", 
        "3. Login/Signup",
        "4. View Statistics",
        "5. Friends & Social",  # NEW OPTION
        "6. Quit"
    ]
    
    if db_handler and db_handler.is_authenticated():
        user = db_handler.get_current_user()
        if user:
            draw_text(f"Logged in as: {user['username']}", SCREEN_WIDTH // 2, 100, GREEN, 18, center=True)
            menu_options[2] = "3. Logout"
    
    for i, option in enumerate(menu_options):
        color = YELLOW if i == menu_selection else WHITE
        draw_text(option, SCREEN_WIDTH // 2, 150 + i * 40, color, 20, center=True)   
    # Instructions
    draw_text("Use UP/DOWN arrows to navigate, ENTER to select", SCREEN_WIDTH // 2, 400, GRAY, 16, center=True)
    
    # Database status
    if db_handler:
        status_color = GREEN if db_handler.is_authenticated() else BLUE
        status_text = "Database: Connected" if db_handler.is_authenticated() else "Database: Available (Guest Mode)"
    else:
        status_color = RED
        status_text = "Database: Offline"
    draw_text(status_text, 10, SCREEN_HEIGHT - 30, status_color, 14)
    
    # Show messages
    if error_message:
        draw_text(error_message, SCREEN_WIDTH // 2, 350, RED, 16, center=True)
    if success_message:
        draw_text(success_message, SCREEN_WIDTH // 2, 350, GREEN, 16, center=True)

def draw_friends_menu():
    """Draw the friends and social menu"""
    win.fill(BLACK)
    
    draw_text("FRIENDS & SOCIAL", SCREEN_WIDTH // 2, 30, GOLD, 32, center=True)
    
    if not db_handler or not db_handler.is_authenticated():
        draw_text("Please log in to use social features", SCREEN_WIDTH // 2, 200, RED, 20, center=True)
        draw_text("Press ESC to go back", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50, GRAY, 16, center=True)
        return
    
    # Add friend section with clear visual feedback
    draw_text("Add Friend:", 50, 100, WHITE, 20)
    
    # Draw input box background
    input_box_color = YELLOW if input_mode == "friend_search" else WHITE
    pygame.draw.rect(win, (50, 50, 50), (200, 95, 400, 30))  # Background box
    pygame.draw.rect(win, input_box_color, (200, 95, 400, 30), 2)  # Border
    
    # Display text with cursor
    search_display = friend_search_text + ("_" if input_mode == "friend_search" else "")
    draw_text(search_display, 205, 100, input_box_color, 18)
    draw_text("(Click here to type username, ENTER to send request)", 50, 130, GRAY, 14)   
    # Friends list
    friends = db_handler.get_friends("accepted") if db_handler else []
    draw_text(f"Your Friends ({len(friends)}):", 50, 170, WHITE, 20)
    
    y_pos = 200
    if friends:
        for i, friend in enumerate(friends[:8]):  # Show max 8 friends
            friend_name = friend.get('friend_profile', {}).get('username', 'Unknown')
            friend_score = friend.get('friend_profile', {}).get('total_score', 0)
            draw_text(f"• {friend_name} (Score: {friend_score})", 70, y_pos, WHITE, 16)
            y_pos += 25
    else:
        draw_text("No friends yet. Add some friends to compete!", 70, y_pos, GRAY, 16)
    
    # Show messages
    if friend_message:
        color = GREEN if "sent" in friend_message.lower() else RED
        draw_text(friend_message, SCREEN_WIDTH // 2, 400, color, 16, center=True)
    
    # Instructions
    draw_text("Press ESC to go back", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50, GRAY, 16, center=True)

def draw_login():
    """Draw the login/signup screen"""
    win.fill(BLACK)
    
    # Title
    title = "SIGN UP" if login_mode == "signup" else "SIGN IN"
    draw_text(title, SCREEN_WIDTH // 2, 50, GOLD, 32, center=True)
    
    # Toggle between signin/signup
    toggle_text = "Switch to Sign In (TAB)" if login_mode == "signup" else "Switch to Sign Up (TAB)"
    draw_text(toggle_text, SCREEN_WIDTH // 2, 100, GRAY, 16, center=True)
    
    # Input fields
    y_pos = 150
    
    # Email field
    email_color = YELLOW if input_mode == "email" else WHITE
    draw_text("Email:", 100, y_pos, email_color)
    email_display = login_data["email"] + ("_" if input_mode == "email" else "")
    draw_text(email_display, 200, y_pos, email_color)
    y_pos += 40
    
    # Password field
    password_color = YELLOW if input_mode == "password" else WHITE
    draw_text("Password:", 100, y_pos, password_color)
    password_display = "*" * len(login_data["password"]) + ("_" if input_mode == "password" else "")
    draw_text(password_display, 200, y_pos, password_color)
    y_pos += 40
    
    # Username field (only for signup)
    if login_mode == "signup":
        username_color = YELLOW if input_mode == "username" else WHITE
        draw_text("Username:", 100, y_pos, username_color)
        username_display = login_data["username"] + ("_" if input_mode == "username" else "")
        draw_text(username_display, 200, y_pos, username_color)
        y_pos += 40
    
    # Instructions
    draw_text("Click on fields to edit, ENTER to submit, ESC to go back", SCREEN_WIDTH // 2, y_pos + 20, GRAY, 16, center=True)
    
    # Submit button
    submit_text = "Create Account" if login_mode == "signup" else "Sign In"
    draw_text(f"Press ENTER: {submit_text}", SCREEN_WIDTH // 2, y_pos + 60, GREEN, 18, center=True)
    
    # Guest option
    draw_text("Press F1: Continue as Guest", SCREEN_WIDTH // 2, y_pos + 90, BLUE, 18, center=True)
    
    # Show messages
    if error_message:
        draw_text(error_message, SCREEN_WIDTH // 2, y_pos + 130, RED, 16, center=True)
    if success_message:
        draw_text(success_message, SCREEN_WIDTH // 2, y_pos + 130, GREEN, 16, center=True)

def draw_leaderboard():
    """Draw the leaderboard screen"""
    win.fill(BLACK)
    
    draw_text("LEADERBOARD", SCREEN_WIDTH // 2, 30, GOLD, 32, center=True)
    
    if db_handler:
        leaderboard = db_handler.get_leaderboard(limit=10)
        
        if leaderboard:
            # Headers
            draw_text("Rank", 50, 80, WHITE, 18)
            draw_text("Player", 120, 80, WHITE, 18)
            draw_text("Score", 300, 80, WHITE, 18)
            draw_text("Time", 400, 80, WHITE, 18)
            draw_text("Date", 500, 80, WHITE, 18)
            
            # Draw line
            pygame.draw.line(win, WHITE, (50, 105), (SCREEN_WIDTH - 50, 105), 2)
            
            # Leaderboard entries
            for i, entry in enumerate(leaderboard):
                y = 120 + i * 25
                color = GOLD if i == 0 else WHITE
                
                draw_text(f"{i+1}", 50, y, color, 16)
                draw_text(entry['player_name'][:15], 120, y, color, 16)
                draw_text(str(entry['score']), 300, y, color, 16)
                
                if entry.get('completion_time'):
                    time_str = f"{entry['completion_time']:.1f}s"
                    draw_text(time_str, 400, y, color, 16)
                
                if entry.get('timestamp'):
                    date_str = entry['timestamp'][:10]  # Just the date part
                    draw_text(date_str, 500, y, color, 16)
        else:
            draw_text("No scores recorded yet!", SCREEN_WIDTH // 2, 200, GRAY, 20, center=True)
    else:
        draw_text("Database not available", SCREEN_WIDTH // 2, 200, RED, 20, center=True)
    
    draw_text("Press ESC to go back", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50, GRAY, 16, center=True)

def draw_stats():
    """Draw the statistics screen"""
    win.fill(BLACK)
    
    draw_text("STATISTICS", SCREEN_WIDTH // 2, 30, GOLD, 32, center=True)
    
    if db_handler and db_handler.is_authenticated():
        user = db_handler.get_current_user()
        analytics = db_handler.get_game_analytics()
        
        if user and analytics:
            y_pos = 100
            
            # User info
            draw_text(f"Player: {user['username']}", 100, y_pos, WHITE, 20)
            y_pos += 40
            
            # Game statistics
            stats = [
                f"Games Played: {analytics.get('total_games', 0)}",
                f"Best Score: {analytics.get('best_score', 0)}",
                f"Average Score: {analytics.get('average_score', 0):.1f}",
                f"Total Score: {analytics.get('total_score', 0)}",
                f"Best Time: {analytics.get('best_time', 0):.1f}s" if analytics.get('best_time') else "Best Time: N/A",
                f"Achievements: {analytics.get('achievements_count', 0)}",
                f"Recent Trend: {analytics.get('recent_trend', 'N/A').title()}"
            ]
            
            for stat in stats:
                draw_text(stat, 100, y_pos, WHITE, 18)
                y_pos += 30
            
            # Recent games
            recent_games = db_handler.get_user_progress(limit=5)
            if recent_games:
                draw_text("Recent Games:", 100, y_pos + 20, YELLOW, 20)
                y_pos += 50
                
                for game in recent_games:
                    game_text = f"Score: {game['score']}, Time: {game.get('completion_time', 0):.1f}s"
                    draw_text(game_text, 120, y_pos, GRAY, 16)
                    y_pos += 25
        else:
            draw_text("Unable to load statistics", SCREEN_WIDTH // 2, 200, RED, 20, center=True)
    else:
        draw_text("Please log in to view statistics", SCREEN_WIDTH // 2, 200, GRAY, 20, center=True)
    
    draw_text("Press ESC to go back", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50, GRAY, 16, center=True)

def draw_game_complete():
    """Draw the game completion screen"""
    win.fill(BLACK)
    
    draw_text("GAME COMPLETED!", SCREEN_WIDTH // 2, 100, GOLD, 36, center=True)
    
    final_score = calculate_score()
    completion_time = time.time() - game_start_time if game_start_time else 0
    
    draw_text(f"Final Score: {final_score}", SCREEN_WIDTH // 2, 180, WHITE, 24, center=True)
    draw_text(f"Completion Time: {completion_time:.1f} seconds", SCREEN_WIDTH // 2, 220, WHITE, 24, center=True)
    draw_text(f"Tiles Explored: {len(explored_tiles)}", SCREEN_WIDTH // 2, 260, WHITE, 24, center=True)
    
    # Check if it's a personal best
    if db_handler and db_handler.is_authenticated():
        personal_best = db_handler.get_personal_best()
        if personal_best and final_score > personal_best.get('score', 0):
            draw_text("🌟 NEW PERSONAL BEST! 🌟", SCREEN_WIDTH // 2, 300, GOLD, 28, center=True)
    
    # Options
    draw_text("Press SPACE to play again", SCREEN_WIDTH // 2, 360, GREEN, 20, center=True)
    draw_text("Press ESC to return to menu", SCREEN_WIDTH // 2, 390, GRAY, 20, center=True)

def handle_login_input(event):
    """Handle input for login screen"""
    global input_mode, login_data, error_message, success_message, game_state
    
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            game_state = "menu"
            input_mode = None
            error_message = ""
            success_message = ""
        
        elif event.key == pygame.K_TAB:
            # Toggle between signin and signup
            global login_mode
            login_mode = "signup" if login_mode == "signin" else "signin"
            input_mode = None
            error_message = ""
            success_message = ""
        
        elif event.key == pygame.K_F1:
            # Continue as guest
            game_state = "menu"
            success_message = "Playing as guest"
        
        elif event.key == pygame.K_RETURN:
            # Submit form
            if login_mode == "signin":
                if login_data["email"] and login_data["password"]:
                    result = db_handler.sign_in(login_data["email"], login_data["password"])
                    if result.get("success"):
                        success_message = f"Welcome back, {result.get('username', 'User')}!"
                        error_message = ""
                        game_state = "menu"
                    else:
                        error_message = result.get("error", "Sign in failed")
                        success_message = ""
                else:
                    error_message = "Please fill in all fields"
            
            elif login_mode == "signup":
                if login_data["email"] and login_data["password"]:
                    username = login_data["username"] if login_data["username"] else None
                    result = db_handler.sign_up(login_data["email"], login_data["password"], username)
                    if result.get("success"):
                        success_message = "Account created! Please check your email to verify."
                        error_message = ""
                        # Don't change state yet, let them sign in after verification
                    else:
                        error_message = result.get("error", "Sign up failed")
                        success_message = ""
                else:
                    error_message = "Please fill in email and password"
        
        elif input_mode and event.unicode.isprintable():
            # Add character to current field
            if len(login_data[input_mode]) < 50:  # Limit input length
                login_data[input_mode] += event.unicode
        
        elif event.key == pygame.K_BACKSPACE and input_mode:
            # Remove character from current field
            login_data[input_mode] = login_data[input_mode][:-1]
    
    elif event.type == pygame.MOUSEBUTTONDOWN:
        # Click to select input field
        mouse_x, mouse_y = event.pos
        
        if 150 <= mouse_y <= 190:  # Email field
            input_mode = "email"
        elif 190 <= mouse_y <= 230:  # Password field
            input_mode = "password"
        elif login_mode == "signup" and 230 <= mouse_y <= 270:  # Username field
            input_mode = "username"
        else:
            input_mode = None

def handle_menu_input(event):
    """Handle input for main menu"""
    global menu_selection, game_state, error_message, success_message
    
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP:
            menu_selection = (menu_selection - 1) % 6  # Changed from 5 to 6
        elif event.key == pygame.K_DOWN:
            menu_selection = (menu_selection + 1) % 6  # Changed from 5 to 6
        elif event.key == pygame.K_RETURN:
            error_message = ""
            success_message = ""
            
            if menu_selection == 0:  # Start New Game
                start_new_game()
            elif menu_selection == 1:  # View Leaderboard
                game_state = "leaderboard"
            elif menu_selection == 2:  # Login/Logout
                if db_handler and db_handler.is_authenticated():
                    # Logout
                    db_handler.sign_out()
                    success_message = "Logged out successfully"
                else:
                    # Go to login
                    game_state = "login"
            elif menu_selection == 3:  # View Statistics
                game_state = "stats"
            elif menu_selection == 4:  # Friends & Social
                game_state = "friends"
            elif menu_selection == 5:  # Quit
                pygame.quit()
                sys.exit(0)

def handle_friends_input(event):
    """Handle input for friends screen"""
    global input_mode, friend_search_text, friend_message, game_state
    
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            game_state = "menu"
            input_mode = None
            friend_message = ""
        
        elif event.key == pygame.K_RETURN and input_mode == "friend_search":
            # Send friend request
            if friend_search_text.strip() and db_handler and db_handler.is_authenticated():
                result = db_handler.add_friend(friend_search_text.strip())
                if result:
                    friend_message = f"Friend request sent to {friend_search_text}!"
                    friend_search_text = ""
                else:
                    friend_message = "Failed to send friend request. User may not exist."
            else:
                friend_message = "Please log in to add friends"
            input_mode = None
        
        elif input_mode == "friend_search" and event.unicode.isprintable():
            # Add character to search
            if len(friend_search_text) < 20:
                friend_search_text += event.unicode
        
        elif event.key == pygame.K_BACKSPACE and input_mode == "friend_search":
            # Remove character
            friend_search_text = friend_search_text[:-1]
    
    elif event.type == pygame.MOUSEBUTTONDOWN:
        # Click to select friend search field
        mouse_x, mouse_y = event.pos
        
        # Adjust these coordinates to match your text field position
        if 100 <= mouse_y <= 125 and 200 <= mouse_x <= 600:  # Friend search field area
            input_mode = "friend_search"
            print("Friend search field activated")  # Debug message
        else:
            input_mode = None

speed = 1.0

# Main game loop
while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Save any ongoing game before quitting
            if game_state == "game" and game_start_time:
                complete_game()
            pygame.quit()
            sys.exit(0)
        
        # Handle input based on current game state
        if game_state == "menu":
            handle_menu_input(event)
        
        elif game_state == "login":
            handle_login_input(event)
        
        elif game_state == "leaderboard" or game_state == "stats":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game_state = "menu"
        
        elif game_state == "friends":  # ADD THIS SECTION
            handle_friends_input(event)
        
        elif game_state == "game_complete":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    start_new_game()
                elif event.key == pygame.K_ESCAPE:
                    game_state = "menu"
        
        elif game_state == "game":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    show_minimap = not show_minimap
                    print(f"Minimap {'ON' if show_minimap else 'OFF'}")
                elif event.key == pygame.K_r:
                    regenerate_maze()
                elif event.key == pygame.K_ESCAPE:
                    # Pause game and return to menu
                    if game_start_time:
                        complete_game()
                    game_state = "menu"
                elif event.key == pygame.K_c:
                    # Complete game manually (for testing)
                    complete_game()
    
    # Clear messages after some time
    if time.time() % 5 < 0.1:  # Clear every 5 seconds
        error_message = ""
        success_message = ""
    
    # Game logic based on current state
    if game_state == "menu":
        draw_menu()
    
    elif game_state == "login":
        draw_login()
    
    elif game_state == "leaderboard":
        draw_leaderboard()
    
    elif game_state == "stats":
        draw_stats()
    
    elif game_state == "friends":  # ADD THIS SECTION
        draw_friends_menu()
    
    elif game_state == "game_complete":
        draw_game_complete()
    elif game_state == "game":
        # Update explored tiles based on current position
        update_explored_tiles()
        
        # Calculate current score
        calculate_score()
        
        # Clear screen
        win.fill((0, 0, 0))
        
        # Draw sky and floor for 3D view
        pygame.draw.rect(win, (0, 150, 200), (SCREEN_HEIGHT, 0, SCREEN_HEIGHT, SCREEN_HEIGHT // 2))  # Sky
        pygame.draw.rect(win, (100, 100, 75), (SCREEN_HEIGHT, SCREEN_HEIGHT // 2, SCREEN_HEIGHT, SCREEN_HEIGHT // 2))  # Floor
        
        # Cast rays first (for 3D view)
        cast_rays()
        
        # Draw map overlay (only if minimap is enabled)
        draw_map()
        
        # Handle keyboard input for movement
        keys = pygame.key.get_pressed()
        
        # Rotation
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: 
            player_angle -= 0.05
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: 
            player_angle += 0.05
        
        # Forward movement
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            new_x = player_x + (-math.sin(player_angle) * speed)
            new_y = player_y + (math.cos(player_angle) * speed)
            
            if is_valid_position(new_x, new_y):
                player_x = new_x
                player_y = new_y
            else:
                if is_valid_position(new_x, player_y):
                    player_x = new_x
                elif is_valid_position(player_x, new_y):
                    player_y = new_y
        
        # Backward movement
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            new_x = player_x - (-math.sin(player_angle) * speed)
            new_y = player_y - (math.cos(player_angle) * speed)
            
            if is_valid_position(new_x, new_y):
                player_x = new_x
                player_y = new_y
            else:
                if is_valid_position(new_x, player_y):
                    player_x = new_x
                elif is_valid_position(player_x, new_y):
                    player_y = new_y
        
        # Strafe movement
        if keys[pygame.K_q]:  # Strafe left
            new_x = player_x + math.cos(player_angle) * speed
            new_y = player_y + math.sin(player_angle) * speed
            
            if is_valid_position(new_x, new_y):
                player_x = new_x
                player_y = new_y
        
        if keys[pygame.K_e]:  # Strafe right
            new_x = player_x - math.cos(player_angle) * speed
            new_y = player_y - math.sin(player_angle) * speed
            
            if is_valid_position(new_x, new_y):
                player_x = new_x
                player_y = new_y
        
        # Check win condition (explored most of the maze)
        total_explorable_tiles = sum(1 for row in MAP for cell in row if cell == '.')
        exploration_percentage = len(explored_tiles) / total_explorable_tiles if total_explorable_tiles > 0 else 0
        
        if exploration_percentage >= 0.8:  # 80% exploration wins the game
            complete_game()
        
        # Display game UI
        font = pygame.font.SysFont('Monospace Regular', 16)
        
        # Game info
        game_info = [
            f"Score: {current_score}",
            f"Time: {int(time.time() - game_start_time)}s" if game_start_time else "Time: 0s",
            f"Explored: {len(explored_tiles)}/{total_explorable_tiles} ({exploration_percentage*100:.1f}%)",
            f"Position: ({int(player_x/TILE_SIZE)}, {int(player_y/TILE_SIZE)})"
        ]
        
        for i, info in enumerate(game_info):
            text_surface = font.render(info, False, WHITE)
            win.blit(text_surface, (10, 10 + i * 18))
        
        # Controls
        controls = [
            "WASD/Arrows=move, Q/E=strafe",
            "M=minimap, R=new maze, C=complete",
            "ESC=menu"
        ]
        
        for i, control in enumerate(controls):
            text_surface = font.render(control, False, GRAY)
            win.blit(text_surface, (10, SCREEN_HEIGHT - 60 + i * 18))
        
        # Minimap status
        minimap_status = f"Minimap: {'ON' if show_minimap else 'OFF'}"
        text_surface = font.render(minimap_status, False, WHITE)
        win.blit(text_surface, (10, 100))
        
        # Database status in game
        if db_handler:
            if db_handler.is_authenticated():
                user = db_handler.get_current_user()
                db_status = f"Player: {user['username'] if user else 'Unknown'}"
                color = GREEN
            else:
                db_status = "Playing as Guest"
                color = BLUE
        else:
            db_status = "Offline Mode"
            color = RED
        
        text_surface = font.render(db_status, False, color)
        win.blit(text_surface, (10, 120))
        
        
         # Auto-save progress periodically for authenticated users (FIXED VERSION)
        if db_handler and db_handler.is_authenticated() and game_start_time:
            # Save every 30 seconds
            current_game_time = int(time.time() - game_start_time)
            if current_game_time > 0 and current_game_time % 30 == 0:
                try:
                    # Only save once per 30-second interval
                    if not hasattr(db_handler, '_last_auto_save') or db_handler._last_auto_save != current_game_time:
                        db_handler._last_auto_save = current_game_time
                        
                        current_score_calc = calculate_score()
                        
                        # Save progress (remove player_name parameter)
                        db_handler.save_game_progress(
                            score=current_score_calc,
                            completion_time=time.time() - game_start_time,
                            maze_size=f"{MAP_WIDTH}x{MAP_HEIGHT}"
                        )
                        
                        # Show save indicator briefly
                        save_text = font.render("Auto-saved", False, GREEN)
                        win.blit(save_text, (SCREEN_WIDTH - 100, 10))
                        
                except Exception as e:
                    print(f"Auto-save failed: {e}")
    
    # Display FPS
    clock.tick(60)
    fps = str(int(clock.get_fps()))
    fps_font = pygame.font.SysFont('Monospace Regular', 30)
    fps_surface = fps_font.render(fps, False, WHITE)
    win.blit(fps_surface, (SCREEN_WIDTH - 60, 10))
    
    # Update display
    pygame.display.flip()

# Cleanup on exit
# Cleanup on exit
if db_handler and db_handler.is_authenticated():
    # Save final progress if game was in progress
    if game_state == "game" and game_start_time:
        try:
            completion_time = time.time() - game_start_time
            final_score = calculate_score()
            
            # Save progress (remove player_name parameter)
            db_handler.save_game_progress(
                score=final_score,
                completion_time=completion_time,
                maze_size=f"{MAP_WIDTH}x{MAP_HEIGHT}"
            )
            db_handler.end_game_session(final_score, completed=False)
            print("✅ Game progress saved on exit")
        except Exception as e:
            print(f"❌ Failed to save progress on exit: {e}")


print("👋 Thanks for playing!")
