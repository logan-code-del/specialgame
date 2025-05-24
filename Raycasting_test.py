import pygame
import sys
import math
pygame.init()
SCREEN_HEIGHT = 480
SCREEN_WIDTH = SCREEN_HEIGHT * 2
MAP_SIZE = 11
RESIZEABLE_BOOL = True
TILE_SIZE = ((SCREEN_WIDTH / 2) / MAP_SIZE)
MAX_DEPTH = int(MAP_SIZE * TILE_SIZE)
FOV = math.pi / 3
HALF_FOV = FOV / 2
CASTED_RAYS = 120
STEP_ANGLE = FOV / CASTED_RAYS
SCALE = (SCREEN_WIDTH / 2) / CASTED_RAYS
player_x = (SCREEN_WIDTH / 2) / 2
player_y = (SCREEN_WIDTH / 2) / 2
player_angle = math.pi
from game_map import MAP
# Convert MAP to a list of strings for easier 2D access

if RESIZEABLE_BOOL:
    win = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.RESIZABLE)
else:
    win = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("Raycasting Demonstration")
clock = pygame.time.Clock()

def draw_map():
    # Draw background for the map area
    pygame.draw.rect(win, (50, 50, 50), (0, 0, SCREEN_HEIGHT, SCREEN_HEIGHT))
    
    # Draw the map
    for row in range(len(MAP)):
        for col in range(len(MAP[0])):
            pygame.draw.rect(
                win,
                (200,200,200) if MAP[row][col] == '#' else (100,100,100),
                (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE - 2, TILE_SIZE - 2)
            )
    
    # Draw player
    pygame.draw.circle(win, (255, 0, 0), (int(player_x), int(player_y)), 8)
    
    # Draw direction lines
    pygame.draw.line(win, (0,255,0), (player_x,player_y), 
                    (player_x - math.sin(player_angle) * 50, player_y + math.cos(player_angle) * 50), 3)
    pygame.draw.line(win, (0,255,0), (player_x,player_y), 
                    (player_x - math.sin(player_angle - HALF_FOV) * 50, player_y + math.cos(player_angle - HALF_FOV) * 50), 3)
    pygame.draw.line(win, (0,255,0), (player_x,player_y), 
                    (player_x - math.sin(player_angle + HALF_FOV) * 50, player_y + math.cos(player_angle + HALF_FOV) * 50), 3)

def cast_rays():
    start_angle = player_angle - HALF_FOV
    
    for ray in range(CASTED_RAYS):
        for depth in range(MAX_DEPTH):
            target_x = player_x - math.sin(start_angle) * depth
            target_y = player_y + math.cos(start_angle) * depth
            
            # Convert to map coordinates
            col = int(target_x / TILE_SIZE)
            row = int(target_y / TILE_SIZE)
            
            # Check if ray is within map bounds
            if 0 <= row < len(MAP) and 0 <= col < len(MAP[0]):
                if MAP[row][col] == '#':
                    # Draw hit point on map
                    pygame.draw.rect(win, (0,255,0), (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE - 2, TILE_SIZE - 2))
                    
                    # Draw ray
                    pygame.draw.line(win, (255,255,0), (player_x,player_y), (target_x,target_y))
                    
                    # Calculate wall height
                    color = 50 / (1 + depth * depth * 0.0001)
                    depth *= math.cos(player_angle - start_angle)  # Fix fisheye effect
                    wall_height = 21000 / (depth + 0.0001)
                    
                    # Cap wall height
                    if wall_height > SCREEN_HEIGHT:
                        wall_height = SCREEN_HEIGHT
                    
                    # Draw 3D wall
                    pygame.draw.rect(win, (color,color,color), 
                                    (SCREEN_HEIGHT + ray * SCALE, 
                                    (SCREEN_HEIGHT / 2) - wall_height / 2,
                                    SCALE, wall_height))
                    break
        
        start_angle += STEP_ANGLE

forward = True
speed = 2  # Define movement speed

# Main game loop
while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
    
    # Clear screen
    win.fill((0, 0, 0))  # Fill with black to clear previous frame
    
    # Draw sky and floor for 3D view
    pygame.draw.rect(win, (0, 150, 200), (480, 0, SCREEN_HEIGHT, SCREEN_HEIGHT // 2))  # Sky
    pygame.draw.rect(win, (100, 100, 75), (480, SCREEN_HEIGHT // 2, SCREEN_HEIGHT, SCREEN_HEIGHT // 2))  # Floor
    
    # Draw map and rays
    draw_map()
    cast_rays()
    
    # Handle keyboard input
    keys = pygame.key.get_pressed()
    
    # Rotation
    if keys[pygame.K_a] or keys[pygame.K_LEFT]: player_angle -= 0.05
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]: player_angle += 0.05
    
    # Forward movement
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        forward = True
        # Calculate new position
        new_x = player_x + (-math.sin(player_angle) * speed)
        new_y = player_y + (math.cos(player_angle) * speed)
        
        # Check if new position is valid
        new_col = int(new_x / TILE_SIZE)
        new_row = int(new_y / TILE_SIZE)
        
        # Only move if not hitting a wall and within bounds
        if 0 <= new_row < len(MAP) and 0 <= new_col < len(MAP[0]) and MAP[new_row][new_col] != '#':
            player_x = new_x
            player_y = new_y
    
    # Backward movement
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        forward = False
        # Calculate new position
        new_x = player_x - (-math.sin(player_angle) * speed)
        new_y = player_y - (math.cos(player_angle) * speed)
        
        # Check if new position is valid
        new_col = int(new_x / TILE_SIZE)
        new_row = int(new_y / TILE_SIZE)
        
        # Only move if not hitting a wall and within bounds
        if 0 <= new_row < len(MAP) and 0 <= new_col < len(MAP[0]) and MAP[new_row][new_col] != '#':
            player_x = new_x
            player_y = new_y
    
    # Display FPS
    clock.tick(60)
    fps = str(int(clock.get_fps()))
    font = pygame.font.SysFont('Monospace Regular', 30)
    textsurface = font.render(fps, False, (255,255,255))
    win.blit(textsurface,(0,0))
    
    # Update display
    pygame.display.flip()
