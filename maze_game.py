import pygame
import sys
import math
import time
import json
import os
from datetime import datetime
from supabase_handler import GameSupabaseHandler
from game_map import MAP

# Game constants
SCREEN_HEIGHT = 480
SCREEN_WIDTH = SCREEN_HEIGHT * 2
FOV = math.pi / 3
HALF_FOV = FOV / 2
CASTED_RAYS = 120
STEP_ANGLE = FOV / CASTED_RAYS
SCALE = (SCREEN_WIDTH / 2) / CASTED_RAYS
VISION_RANGE = 6

class MazeGame:
    def __init__(self, game_config=None):
        pygame.init()
        
        # Load configuration passed from menu
        self.config = game_config or {}
        self.player_name = self.config.get('player_name', 'Guest')
        self.user_id = self.config.get('user_id')
        self.session_data = self.config.get('session_data')
        
        # Initialize database if user is authenticated
        self.db_handler = None
        if self.user_id and self.session_data:
            try:
                self.db_handler = GameSupabaseHandler()
                # Restore session using session data
                if self.session_data.get('access_token'):
                    success = self.db_handler.restore_session(
                        self.session_data['access_token'],
                        self.session_data.get('refresh_token')
                    )
                    if not success:
                        print("❌ Failed to restore session, continuing as guest")
                        self.db_handler = None
                        self.player_name = 'Guest'
                        self.user_id = None
            except Exception as e:
                print(f"Database connection failed: {e}")
                self.db_handler = None
                self.player_name = 'Guest'
                self.user_id = None
        
        # Calculate map dimensions
        self.MAP = MAP
        self.MAP_WIDTH = len(MAP[0])
        self.MAP_HEIGHT = len(MAP)
        self.TILE_SIZE = ((SCREEN_WIDTH / 2) / max(self.MAP_WIDTH, self.MAP_HEIGHT))
        self.MAX_DEPTH = int(max(self.MAP_WIDTH, self.MAP_HEIGHT) * self.TILE_SIZE)
        self.RAY_RANGE = VISION_RANGE * self.TILE_SIZE
        
        # Game state
        self.player_x, self.player_y = self.find_spawn_position()
        self.player_angle = math.pi
        self.explored_tiles = set()
        self.current_score = 0
        self.game_start_time = time.time()
        self.show_minimap = False
        
        # Player collision radius
        self.player_radius = 8  # Smaller radius for better movement
        
        # Display setup
        self.win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Maze Game")
        self.clock = pygame.time.Clock()
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        self.GREEN = (0, 200, 0)
        self.RED = (200, 0, 0)
        
        # Start game session
        if self.db_handler and self.db_handler.is_authenticated():
            self.db_handler.start_game_session()
    
    def is_tile_visible(self, tile_x, tile_y):
        """Check if a tile should be visible based on player's current position and vision range"""
        player_tile_x = int(self.player_x / self.TILE_SIZE)
        player_tile_y = int(self.player_y / self.TILE_SIZE)
        
        dx = tile_x - player_tile_x
        dy = tile_y - player_tile_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance <= VISION_RANGE

    def find_spawn_position(self):
        """Find a good spawn position in the maze"""
        for y in range(1, min(5, self.MAP_HEIGHT - 1)):
            for x in range(1, min(5, self.MAP_WIDTH - 1)):
                if self.MAP[y][x] == '.':
                    return (x + 0.5) * self.TILE_SIZE, (y + 0.5) * self.TILE_SIZE
        return self.TILE_SIZE * 1.5, self.TILE_SIZE * 1.5
    
    def is_wall_at_position(self, x, y):
        """Check if there's a wall at the given position"""
        col = int(x / self.TILE_SIZE)
        row = int(y / self.TILE_SIZE)
        
        # Check bounds
        if not (0 <= row < self.MAP_HEIGHT and 0 <= col < self.MAP_WIDTH):
            return True
        
        return self.MAP[row][col] == '#'
    
    def check_collision(self, x, y):
        """Check if the player would collide with a wall at position (x, y)"""
        # Check collision using a circle around the player
        # Test multiple points around the player's radius
        test_points = [
            (x, y),  # Center
            (x - self.player_radius, y),  # Left
            (x + self.player_radius, y),  # Right
            (x, y - self.player_radius),  # Top
            (x, y + self.player_radius),  # Bottom
            (x - self.player_radius * 0.7, y - self.player_radius * 0.7),  # Top-left
            (x + self.player_radius * 0.7, y - self.player_radius * 0.7),  # Top-right
            (x - self.player_radius * 0.7, y + self.player_radius * 0.7),  # Bottom-left
            (x + self.player_radius * 0.7, y + self.player_radius * 0.7),  # Bottom-right
        ]
        
        for test_x, test_y in test_points:
            if self.is_wall_at_position(test_x, test_y):
                return True
        
        return False
    
    def move_player(self, new_x, new_y):
        """Move player with wall sliding collision detection"""
        # Try to move to the new position
        if not self.check_collision(new_x, new_y):
            self.player_x = new_x
            self.player_y = new_y
            return True
        
        # If direct movement fails, try sliding along walls
        # Try moving only in X direction
        if not self.check_collision(new_x, self.player_y):
            self.player_x = new_x
            return True
        
        # Try moving only in Y direction
        if not self.check_collision(self.player_x, new_y):
            self.player_y = new_y
            return True
        
        # No movement possible
        return False
    
    def update_explored_tiles(self):
        """Update explored tiles based on player position"""
        player_tile_x = int(self.player_x / self.TILE_SIZE)
        player_tile_y = int(self.player_y / self.TILE_SIZE)
        
        for dy in range(-VISION_RANGE, VISION_RANGE + 1):
            for dx in range(-VISION_RANGE, VISION_RANGE + 1):
                tile_x = player_tile_x + dx
                tile_y = player_tile_y + dy
                
                if 0 <= tile_y < self.MAP_HEIGHT and 0 <= tile_x < self.MAP_WIDTH:
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance <= VISION_RANGE:
                        self.explored_tiles.add((tile_x, tile_y))
    
    def cast_rays(self):
        """Cast rays for 3D rendering"""
        start_angle = self.player_angle - HALF_FOV
        
        for ray in range(CASTED_RAYS):
            hit_wall = False
            wall_distance = 0
            
            for depth in range(self.MAX_DEPTH):
                target_x = self.player_x - math.sin(start_angle) * depth
                target_y = self.player_y + math.cos(start_angle) * depth
                
                col = int(target_x / self.TILE_SIZE)
                row = int(target_y / self.TILE_SIZE)
                
                if 0 <= row < self.MAP_HEIGHT and 0 <= col < self.MAP_WIDTH:
                    if self.MAP[row][col] == '#':
                        hit_wall = True
                        wall_distance = depth
                        break
                else:
                    hit_wall = True
                    wall_distance = depth
                    break
            
            if hit_wall:
                if wall_distance <= self.RAY_RANGE:
                    color = 255 / (1 + wall_distance * wall_distance * 0.0001)
                else:
                    color = max(0, 50 / (1 + wall_distance * wall_distance * 0.001))
                
                corrected_distance = wall_distance * math.cos(self.player_angle - start_angle)
                wall_height = 21000 / (corrected_distance + 0.0001)
                
                if wall_height > SCREEN_HEIGHT:
                    wall_height = SCREEN_HEIGHT
                
                pygame.draw.rect(self.win, (color, color, color),
                               (SCREEN_HEIGHT + ray * SCALE,
                               (SCREEN_HEIGHT / 2) - wall_height / 2,
                               SCALE, wall_height))
            
            start_angle += STEP_ANGLE
    
    def draw_map(self):
        """Draw the minimap with fog of war"""
        if not self.show_minimap:
            return
        
        # Calculate minimap size to fit screen
        minimap_size = min(SCREEN_HEIGHT, SCREEN_WIDTH // 2)
        minimap_tile_size = minimap_size / max(self.MAP_WIDTH, self.MAP_HEIGHT)
        
        # Draw background for the map area
        pygame.draw.rect(self.win, (50, 50, 50), (0, 0, minimap_size, minimap_size))
        
        # Draw the map with fog of war
        for row in range(self.MAP_HEIGHT):
            for col in range(self.MAP_WIDTH):
                tile_pos = (col, row)
                
                if tile_pos in self.explored_tiles:
                    if self.is_tile_visible(col, row):
                        color = (200,200,200) if self.MAP[row][col] == '#' else (100,100,100)
                        alpha = 255
                    else:
                        color = (100,100,100) if self.MAP[row][col] == '#' else (50,50,50)
                        alpha = 128
                    
                    tile_surface = pygame.Surface((minimap_tile_size - 1, minimap_tile_size - 1))
                    tile_surface.fill(color)
                    tile_surface.set_alpha(alpha)
                    
                    self.win.blit(tile_surface, (col * minimap_tile_size, row * minimap_tile_size))
                else:
                    pygame.draw.rect(self.win, (20, 20, 20), 
                                (col * minimap_tile_size, row * minimap_tile_size, 
                                    minimap_tile_size - 1, minimap_tile_size - 1))
        
        # Draw player on minimap
        minimap_player_x = (self.player_x / self.TILE_SIZE) * minimap_tile_size
        minimap_player_y = (self.player_y / self.TILE_SIZE) * minimap_tile_size
        pygame.draw.circle(self.win, (255, 0, 0), (int(minimap_player_x), int(minimap_player_y)), 4)
        
        # Draw direction line
        end_x = minimap_player_x - math.sin(self.player_angle) * 20
        end_y = minimap_player_y + math.cos(self.player_angle) * 20
        pygame.draw.line(self.win, (0,255,0), (minimap_player_x, minimap_player_y), (end_x, end_y), 2)
        
    def calculate_score(self):
        """Calculate current score"""
        if self.game_start_time:
            time_bonus = max(0, 1000 - int(time.time() - self.game_start_time))
            exploration_bonus = len(self.explored_tiles) * 10
            self.current_score = time_bonus + exploration_bonus
        return self.current_score
    
    def save_and_exit(self, completed=False):
        """Save progress and exit to menu"""
        completion_time = time.time() - self.game_start_time
        final_score = self.calculate_score()
        
        # Prepare result data
        result_data = {
            'completed': completed,
            'score': final_score,
            'completion_time': completion_time,
            'tiles_explored': len(self.explored_tiles),
            'player_name': self.player_name,
            'user_id': self.user_id,
            'maze_size': f"{self.MAP_WIDTH}x{self.MAP_HEIGHT}"
        }
        
        # Save to database if authenticated
        if self.db_handler and self.db_handler.is_authenticated():
            try:
                self.db_handler.save_game_progress(
                    score=final_score,
                    completion_time=completion_time,
                    maze_size=f"{self.MAP_WIDTH}x{self.MAP_HEIGHT}"
                )
                self.db_handler.end_game_session(final_score, completed=completed)
                result_data['saved_to_db'] = True
            except Exception as e:
                print(f"Failed to save to database: {e}")
                result_data['saved_to_db'] = False
        else:
            # Save guest progress
            result_data['saved_to_db'] = False
        
        # Write result to file for menu to read
        with open('game_result.json', 'w') as f:
            json.dump(result_data, f)
        
        pygame.quit()
        sys.exit(0)
    
    def run(self):
        """Main game loop"""
        speed = 1.5  # Slightly increased speed for better movement feel
        
        while True:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_and_exit(completed=False)
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.save_and_exit(completed=False)
                    elif event.key == pygame.K_m:
                        self.show_minimap = not self.show_minimap
                        print(f"Minimap {'ON' if self.show_minimap else 'OFF'}")
            
            # Handle movement
            keys = pygame.key.get_pressed()
            
            # Rotation
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.player_angle -= 0.05
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.player_angle += 0.05
            
            # Movement
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                new_x = self.player_x + (-math.sin(self.player_angle) * speed)
                new_y = self.player_y + (math.cos(self.player_angle) * speed)
                if self.is_valid_position(new_x, new_y):
                    self.player_x, self.player_y = new_x, new_y
            
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                new_x = self.player_x - (-math.sin(self.player_angle) * speed)
                new_y = self.player_y - (math.cos(self.player_angle) * speed)
                if self.is_valid_position(new_x, new_y):
                    self.player_x, self.player_y = new_x, new_y
            
            # Strafe movement
            if keys[pygame.K_q]:  # Strafe left
                new_x = self.player_x + math.cos(self.player_angle) * speed
                new_y = self.player_y + math.sin(self.player_angle) * speed
                if self.is_valid_position(new_x, new_y):
                    self.player_x, self.player_y = new_x, new_y
            
            if keys[pygame.K_e]:  # Strafe right
                new_x = self.player_x - math.cos(self.player_angle) * speed
                new_y = self.player_y - math.sin(self.player_angle) * speed
                if self.is_valid_position(new_x, new_y):
                    self.player_x, self.player_y = new_x, new_y
            
            # Update game state
            self.update_explored_tiles()
            self.calculate_score()
            
            # Check win condition
            total_explorable = sum(1 for row in self.MAP for cell in row if cell == '.')
            exploration_percentage = len(self.explored_tiles) / total_explorable if total_explorable > 0 else 0
            
            if exploration_percentage >= 0.8:
                self.save_and_exit(completed=True)
            
            # Render
            self.win.fill(self.BLACK)
            
            # Draw sky and floor
            pygame.draw.rect(self.win, (0, 150, 200), (SCREEN_HEIGHT, 0, SCREEN_HEIGHT, SCREEN_HEIGHT // 2))
            pygame.draw.rect(self.win, (100, 100, 75), (SCREEN_HEIGHT, SCREEN_HEIGHT // 2, SCREEN_HEIGHT, SCREEN_HEIGHT // 2))
            
            # Cast rays
            self.cast_rays()
            
            # Draw minimap (ADD THIS LINE)
            self.draw_map()
            
            # Draw UI
            font = pygame.font.SysFont('Arial', 16)
            
            ui_elements = [
                f"Score: {self.current_score}",
                f"Time: {int(time.time() - self.game_start_time)}s",
                f"Explored: {len(self.explored_tiles)}/{total_explorable} ({exploration_percentage*100:.1f}%)",
                f"Player: {self.player_name}",
                f"Minimap: {'ON' if self.show_minimap else 'OFF'}"  # Add minimap status
            ]
            
            for i, text in enumerate(ui_elements):
                surface = font.render(text, True, self.WHITE)
                self.win.blit(surface, (10, 10 + i * 20))
            
            # Controls
            controls = ["WASD=move", "Q/E=strafe", "M=minimap", "ESC=quit"]
            for i, control in enumerate(controls):
                surface = font.render(control, True, self.GRAY)
                self.win.blit(surface, (10, SCREEN_HEIGHT - 80 + i * 18))
            
            # FPS
            fps_surface = font.render(str(int(self.clock.get_fps())), True, self.WHITE)
            self.win.blit(fps_surface, (SCREEN_WIDTH - 60, 10))
            
            pygame.display.flip()
            self.clock.tick(60)  # Target 60 FPS
