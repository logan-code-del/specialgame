from maze_generator import generate_medium_maze, generate_large_maze, generate_huge_maze, generate_custom_maze
import random

# Choose which type of maze to generate
# Uncomment the one you want to use:

# Small maze (15x15) - good for testing
# MAP = generate_small_maze()

# Medium maze (25x25) - balanced gameplay
MAP = generate_medium_maze()

# Large maze (35x35) - more exploration
# MAP = generate_large_maze()

# Huge maze (51x51) - epic exploration
# MAP = generate_huge_maze()

# Custom size maze
# MAP = generate_custom_maze(41, 31)  # width, height

# Random size maze each time
# sizes = [(21, 21), (25, 25), (31, 31), (35, 35)]
# width, height = random.choice(sizes)
# MAP = generate_custom_maze(width, height)

print(f"Loaded maze: {len(MAP[0])} x {len(MAP)} tiles")

