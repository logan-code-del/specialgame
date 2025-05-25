import pygame
import sys
import math

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

# Debug: Print map and tile info
print(f"TILE_SIZE: {TILE_SIZE}")
print(f"Map dimensions: {MAP_HEIGHT} x {MAP_WIDTH}")
print(f"Starting position: ({player_x}, {player_y})")
print(f"Vision range: {VISION_RANGE} tiles ({RAY_RANGE} pixels)")

if RESIZEABLE_BOOL:
    win = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.RESIZABLE)
else:
    win = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))

pygame.display.set_caption("Raycasting Maze Explorer")
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

speed = 1.0

# Main game loop
while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                show_minimap = not show_minimap
                print(f"Minimap {'ON' if show_minimap else 'OFF'}")
            elif event.key == pygame.K_r:
                regenerate_maze()
    
    # Update explored tiles based on current position
    update_explored_tiles()
    
    # Clear screen
    win.fill((0, 0, 0))
    
    # Draw sky and floor for 3D view
    pygame.draw.rect(win, (0, 150, 200), (SCREEN_HEIGHT, 0, SCREEN_HEIGHT, SCREEN_HEIGHT // 2))  # Sky
    pygame.draw.rect(win, (100, 100, 75), (SCREEN_HEIGHT, SCREEN_HEIGHT // 2, SCREEN_HEIGHT, SCREEN_HEIGHT // 2))  # Floor
    
    # Cast rays first (for 3D view)
    cast_rays()
    
    # Draw map overlay (only if minimap is enabled)
    draw_map()
    
    # Handle keyboard input
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
    
    # Strafe movement (optional - makes navigation easier in mazes)
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
    
    # Display UI
    font = pygame.font.SysFont('Monospace Regular', 16)
    
    # Instructions
    instructions = [
        "Controls: WASD/Arrows=move, Q/E=strafe, M=minimap, R=new maze",
        f"Minimap: {'ON' if show_minimap else 'OFF'} | Maze: {MAP_WIDTH}x{MAP_HEIGHT}",
        f"Vision Range: {VISION_RANGE} tiles | Explored: {len(explored_tiles)} tiles",
        f"Position: ({int(player_x/TILE_SIZE)}, {int(player_y/TILE_SIZE)})"
    ]
    
    for i, instruction in enumerate(instructions):
        text_surface = font.render(instruction, False, (255,255,255))
        win.blit(text_surface, (10, 10 + i * 18))
    
    # Display FPS
    clock.tick(60)
    fps = str(int(clock.get_fps()))
    fps_font = pygame.font.SysFont('Monospace Regular', 30)
    fps_surface = fps_font.render(fps, False, (255,255,255))
    win.blit(fps_surface, (SCREEN_WIDTH - 60, 10))
    
    # Update display
    pygame.display.flip()
