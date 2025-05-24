import pygame
import sys
import os

# Initialize pygame
pygame.init()

# Constants
GRID_SIZE = 11  # Default grid size (same as your game's MAP_SIZE)
CELL_SIZE = 40  # Size of each cell in pixels
PADDING = 50    # Padding around the grid
WINDOW_WIDTH = GRID_SIZE * CELL_SIZE + PADDING * 2
WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + PADDING * 2 + 100  # Extra space for buttons

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Create the window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Raycasting Map Editor")

# Font
font = pygame.font.SysFont('Arial', 20)

# Initialize the grid with spaces
grid = [['#' if (i == 0 or i == GRID_SIZE-1 or j == 0 or j == GRID_SIZE-1) 
         else ' ' for i in range(GRID_SIZE)] for j in range(GRID_SIZE)]

# Button definitions
save_button = pygame.Rect(PADDING, WINDOW_HEIGHT - 80, 100, 40)
load_button = pygame.Rect(PADDING + 120, WINDOW_HEIGHT - 80, 100, 40)
clear_button = pygame.Rect(PADDING + 240, WINDOW_HEIGHT - 80, 100, 40)
resize_button = pygame.Rect(PADDING + 360, WINDOW_HEIGHT - 80, 100, 40)

def draw_grid():
    """Draw the grid with walls and spaces"""
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rect = pygame.Rect(
                PADDING + x * CELL_SIZE, 
                PADDING + y * CELL_SIZE, 
                CELL_SIZE, 
                CELL_SIZE
            )
            
            # Draw cell
            if grid[y][x] == '#':
                pygame.draw.rect(screen, LIGHT_GRAY, rect)
            else:
                pygame.draw.rect(screen, GRAY, rect)
            
            # Draw border
            pygame.draw.rect(screen, BLACK, rect, 1)

def draw_buttons():
    """Draw the UI buttons"""
    pygame.draw.rect(screen, GREEN, save_button)
    save_text = font.render("Save", True, BLACK)
    screen.blit(save_text, (save_button.x + 30, save_button.y + 10))
    
    pygame.draw.rect(screen, BLUE, load_button)
    load_text = font.render("Load", True, BLACK)
    screen.blit(load_text, (load_button.x + 30, load_button.y + 10))
    
    pygame.draw.rect(screen, RED, clear_button)
    clear_text = font.render("Clear", True, BLACK)
    screen.blit(clear_text, (clear_button.x + 30, clear_button.y + 10))
    
    pygame.draw.rect(screen, LIGHT_GRAY, resize_button)
    resize_text = font.render("Resize", True, BLACK)
    screen.blit(resize_text, (resize_button.x + 25, resize_button.y + 10))

def save_map():
    """Save the current map to a file"""
    filename = "custom_map.txt"
    with open(filename, 'w') as f:
        for row in grid:
            f.write(''.join(row) + '\n')
    print(f"Map saved to {filename}")
    
    # Also save in the format used by your game
    with open("game_map.py", 'w') as f:
        f.write("MAP = [\n")
        for row in grid:
            f.write(f"    '{(''.join(row))}',\n")
        f.write("]\n")
    print("Map saved in game format to game_map.py")

def load_map():
    """Load a map from a file"""
    global grid, GRID_SIZE
    filename = "custom_map.txt"
    
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return
    
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
    
    # Update grid size if needed
    if lines:
        GRID_SIZE = max(len(lines), len(lines[0]))
        
        # Resize the window
        global WINDOW_WIDTH, WINDOW_HEIGHT
        WINDOW_WIDTH = GRID_SIZE * CELL_SIZE + PADDING * 2
        WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + PADDING * 2 + 100
        pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # Create new grid
        grid = [[' ' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Fill with loaded data
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if x < GRID_SIZE and y < GRID_SIZE:
                    grid[y][x] = char
    
    print(f"Map loaded from {filename}")

def clear_map():
    """Clear the map, keeping only the border walls"""
    global grid
    grid = [['#' if (i == 0 or i == GRID_SIZE-1 or j == 0 or j == GRID_SIZE-1) 
             else ' ' for i in range(GRID_SIZE)] for j in range(GRID_SIZE)]
    print("Map cleared")

def resize_map():
    """Prompt user for new grid size and resize the map"""
    global GRID_SIZE, grid, WINDOW_WIDTH, WINDOW_HEIGHT
    
    # Simple text-based input for now
    try:
        new_size = int(input("Enter new grid size (5-30): "))
        if 5 <= new_size <= 30:
            # Save the old grid
            old_grid = grid
            old_size = GRID_SIZE
            
            # Update size
            GRID_SIZE = new_size
            WINDOW_WIDTH = GRID_SIZE * CELL_SIZE + PADDING * 2
            WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + PADDING * 2 + 100
            screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            
            # Create new grid with border walls
            grid = [['#' if (i == 0 or i == GRID_SIZE-1 or j == 0 or j == GRID_SIZE-1) 
                     else ' ' for i in range(GRID_SIZE)] for j in range(GRID_SIZE)]
            
            # Copy over the old grid data where possible
            for y in range(min(old_size, GRID_SIZE)):
                for x in range(min(old_size, GRID_SIZE)):
                    if y < len(old_grid) and x < len(old_grid[y]):
                        grid[y][x] = old_grid[y][x]
            
            print(f"Grid resized to {GRID_SIZE}x{GRID_SIZE}")
        else:
            print("Size must be between 5 and 30")
    except ValueError:
        print("Please enter a valid number")

# Main loop
running = True
drawing = False  # Track if we're drawing or erasing

while running:
    screen.fill(WHITE)
    
    # Draw the grid and buttons
    draw_grid()
    draw_buttons()
    
    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check if clicking on the grid
            mouse_pos = pygame.mouse.get_pos()
            x = (mouse_pos[0] - PADDING) // CELL_SIZE
            y = (mouse_pos[1] - PADDING) // CELL_SIZE
            
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                # Toggle the cell
                drawing = True
                if grid[y][x] == '#':
                    # Don't allow erasing border walls
                    if not (x == 0 or x == GRID_SIZE-1 or y == 0 or y == GRID_SIZE-1):
                        grid[y][x] = ' '
                else:
                    grid[y][x] = '#'
            
            # Check if clicking on buttons
            elif save_button.collidepoint(mouse_pos):
                save_map()
            elif load_button.collidepoint(mouse_pos):
                load_map()
            elif clear_button.collidepoint(mouse_pos):
                clear_map()
            elif resize_button.collidepoint(mouse_pos):
                resize_map()
        
        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
        
        elif event.type == pygame.MOUSEMOTION and drawing:
            # Continue drawing/erasing while mouse button is held
            mouse_pos = pygame.mouse.get_pos()
            x = (mouse_pos[0] - PADDING) // CELL_SIZE
            y = (mouse_pos[1] - PADDING) // CELL_SIZE
            
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                # Don't allow erasing border walls
                if not (x == 0 or x == GRID_SIZE-1 or y == 0 or y == GRID_SIZE-1):
                    # Set to the same value as the initial cell
                    if grid[y][x] != '#':
                        grid[y][x] = '#'
    
    # Display instructions
    instructions = font.render("Click to place/remove walls. Border walls cannot be removed.", True, BLACK)
    screen.blit(instructions, (PADDING, WINDOW_HEIGHT - 30))
    
    pygame.display.flip()

pygame.quit()
sys.exit()