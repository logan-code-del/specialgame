import random
import sys

class MazeGenerator:
    def __init__(self, width=21, height=21):
        # Ensure odd dimensions for proper maze generation
        self.width = width if width % 2 == 1 else width + 1
        self.height = height if height % 2 == 1 else height + 1
        self.maze = []
        self.generate_maze()
    
    def generate_maze(self):
        """Generate a maze using recursive backtracking algorithm"""
        # Initialize maze with all walls
        self.maze = [['#' for _ in range(self.width)] for _ in range(self.height)]
        
        # Starting position (must be odd coordinates)
        start_x, start_y = 1, 1
        self.maze[start_y][start_x] = '.'
        
        # Stack for backtracking
        stack = [(start_x, start_y)]
        
        # Directions: right, down, left, up
        directions = [(2, 0), (0, 2), (-2, 0), (0, -2)]
        
        while stack:
            current_x, current_y = stack[-1]
            
            # Get all valid neighbors
            neighbors = []
            for dx, dy in directions:
                new_x, new_y = current_x + dx, current_y + dy
                
                # Check if neighbor is within bounds and is a wall
                if (0 < new_x < self.width - 1 and 
                    0 < new_y < self.height - 1 and 
                    self.maze[new_y][new_x] == '#'):
                    neighbors.append((new_x, new_y, dx, dy))
            
            if neighbors:
                # Choose random neighbor
                new_x, new_y, dx, dy = random.choice(neighbors)
                
                # Carve path to neighbor
                self.maze[new_y][new_x] = '.'
                # Carve the wall between current and neighbor
                self.maze[current_y + dy // 2][current_x + dx // 2] = '.'
                
                # Add neighbor to stack
                stack.append((new_x, new_y))
            else:
                # Backtrack
                stack.pop()
        
        # Ensure there's always a clear starting area
        self.create_starting_area()
        
        # Add some random openings for more interesting gameplay
        self.add_random_openings()
    
    def create_starting_area(self):
        """Create a small clear area at the start"""
        start_x, start_y = 1, 1
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                x, y = start_x + dx, start_y + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    if not (x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1):
                        self.maze[y][x] = '.'
    
    def add_random_openings(self):
        """Add some random openings to make the maze less linear"""
        num_openings = max(1, (self.width * self.height) // 100)
        
        for _ in range(num_openings):
            # Pick a random wall that's not on the border
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            
            # Only remove walls that are between paths
            if self.maze[y][x] == '#':
                # Check if removing this wall connects two paths
                adjacent_paths = 0
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    if self.maze[y + dy][x + dx] == '.':
                        adjacent_paths += 1
                
                # Remove wall if it would connect paths but not create too open areas
                if adjacent_paths >= 2 and random.random() < 0.3:
                    self.maze[y][x] = '.'
    
    def get_maze(self):
        """Return the maze as a list of strings"""
        return [''.join(row) for row in self.maze]
    
    def print_maze(self):
        """Print the maze to console"""
        for row in self.maze:
            print(''.join(row))
    
    def get_spawn_position(self):
        """Get a good spawn position (in tiles, not pixels)"""
        # Find the first open space near the starting area
        for y in range(1, min(4, self.height - 1)):
            for x in range(1, min(4, self.width - 1)):
                if self.maze[y][x] == '.':
                    return x, y
        return 1, 1  # Fallback

def generate_small_maze():
    """Generate a small maze (good for testing)"""
    generator = MazeGenerator(15, 15)
    return generator.get_maze()

def generate_medium_maze():
    """Generate a medium maze"""
    generator = MazeGenerator(25, 25)
    return generator.get_maze()

def generate_large_maze():
    """Generate a large maze"""
    generator = MazeGenerator(35, 35)
    return generator.get_maze()

def generate_huge_maze():
    """Generate a huge maze"""
    generator = MazeGenerator(51, 51)
    return generator.get_maze()

def generate_custom_maze(width, height):
    """Generate a maze with custom dimensions"""
    generator = MazeGenerator(width, height)
    return generator.get_maze()

# Generate the maze when this module is imported
# You can change this to generate different sized mazes
MAP = generate_medium_maze()

# Optional: Print maze info when generated
if __name__ == "__main__":
    print(f"Generated maze: {len(MAP[0])} x {len(MAP)} tiles")
    print("Maze preview:")
    for i, row in enumerate(MAP[:10]):  # Show first 10 rows
        print(f"{i:2}: {row}")
    if len(MAP) > 10:
        print("...")
    
    # Show spawn position
    generator = MazeGenerator(len(MAP[0]), len(MAP))
    spawn_x, spawn_y = generator.get_spawn_position()
    print(f"Recommended spawn position: ({spawn_x}, {spawn_y})")
else:
    print(f"Maze generated: {len(MAP[0])} x {len(MAP)} tiles")
