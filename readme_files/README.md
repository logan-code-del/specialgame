# Enhanced Maze Game

A 3D raycasting maze game with database integration, user accounts, leaderboards, and statistics tracking.

## Features

### Core Gameplay
- **3D Raycasting Engine**: First-person perspective maze exploration
- **Fog of War**: Limited vision range for added challenge
- **Dynamic Mazes**: Procedurally generated mazes
- **Minimap**: Toggle-able overhead view
- **Score System**: Points for exploration and speed

### Database Features
- **User Accounts**: Sign up/sign in with email verification
- **Leaderboards**: Global high scores and rankings
- **Statistics**: Personal game analytics and progress tracking
- **Game Saves**: Auto-save and backup functionality
- **Guest Mode**: Play without an account

### Social Features
- **Achievements**: Unlock achievements for various accomplishments
- **Friends System**: Add friends and compare scores
- **Custom Mazes**: Create and share your own mazes
- **Ratings**: Rate and review community mazes

## Installation

### Quick Setup
1. Run the setup script:
   ```bash
   python setup_game.py
   ```

### Manual Setup
1. **Install Python 3.7+**

2. **Install required packages:**
   ```bash
   pip install pygame supabase python-dotenv
   ```

3. **Set up Supabase (optional for database features):**
   - Create a project at [supabase.com](https://supabase.com)
   - Copy your project URL and anon key
   - Run the SQL schema from `simple_database_schema.sql` in your Supabase SQL editor

4. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Add your Supabase credentials:
     ```
     SUPABASE_URL=your_project_url
     SUPABASE_KEY=your_anon_key
     ```

## How to Play

### Starting the Game
```bash
python Raycasting_test.py
```

### Controls
- **Movement**: WASD or Arrow Keys
- **Strafe**: Q (left) / E (right)
- **Look**: A/D or Left/Right arrows
- **Minimap**: M to toggle
- **New Maze**: R to regenerate
- **Menu**: ESC

### Objective
Explore the maze and discover as many tiles as possible. The game ends when you've explored 80% of the maze or manually complete it.

### Scoring
- **Exploration Points**: 10 points per tile discovered
- **Time Bonus**: Up to 1000 points for fast completion
- **Total Score**: Exploration + Time bonus

## Game Modes

### Guest Mode
- Play without creating an account
- Scores saved locally to leaderboard
- No persistent statistics or achievements

### Authenticated Mode
- Create an account with email verification
- Persistent statistics and progress tracking
- Achievements and social features
- Auto-save and game backups
- Global leaderboards

## Database Schema

The game uses the following main tables:
- `user_profiles` - User account information
- `game_sessions` - Individual game sessions
- `player_progress` - Score and completion data
- `mazes` - Custom maze storage
- `user_achievements` - Achievement tracking

## File Structure

```
aaronsgame/
├── Raycasting_test.py  # Main game file
├── supabase_handler.py           # Database integration    
├── maze_generator.py             # Maze generator
├── game_map.py                   # Maze generation
├── config.py                     # Game configuration
├── setup_game.py                 # Setup script
├── simple_database_schema.sql    # Database schema
├── database_schema.sql           # Full database schema
├── .env                          # Environment variables
├── README_DATABASE.md            # Database documentation
└── README.md                     # Game documentation

```

## Configuration

Edit `config.py` to customize:
- Screen resolution and game settings
- Scoring parameters
- UI colors and themes
- Control key bindings
- Achievement definitions

## Troubleshooting

### Common Issues

**"Database connection failed"**
- Check your `.env` file has correct Supabase credentials
- Verify your Supabase project is active
- Game will work in offline mode without database features

**"Module not found" errors**
- Run `python setup_game.py` to install missing packages
- Or manually install: `pip install pygame supabase python-dotenv`

**Performance issues**
- Reduce `CASTED_RAYS` in the main game file
- Lower screen resolution in `config.py`
- Disable minimap if not needed

**Maze generation problems**
- Check that `game_map.py` exists and contains a valid `MAP` variable
- The MAP should be a 2D list with '#' for walls and '.' for paths

### Debug Mode

Set `DEBUG_MODE=True` in your `.env` file for additional logging and debug information.

## Development

### Adding New Features

1. **New Achievements**: Add to `ACHIEVEMENTS` in `config.py`
2. **Custom Scoring**: Modify the `calculate_score()` function
3. **New Controls**: Update `CONTROLS` in `config.py`
4. **UI Changes**: Modify the draw functions in the main game file

### Database Modifications

If you need to modify the database schema:
1. Update `simple_database_schema.sql`
2. Add corresponding methods to `supabase_handler.py`
3. Update the game logic to use new features

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to modify and distribute.

## Support

For issues or questions:
1. Check this README
2. Run `python setup_game.py` to verify setup
3. Check the console output for error messages
4. Ensure all required files are present

## Credits

- Raycasting engine inspired by classic FPS games
- Built with Pygame for graphics
- Supabase for backend services
- Python for game logic

Enjoy exploring the mazes! 🎮
