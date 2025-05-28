import os
from supabase import create_client, Client
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime
import hashlib
import time
from dotenv import load_dotenv

class GameSupabaseHandler:
    def __init__(self, url: str = None, key: str = None):
        """
        Initialize Supabase client with authentication and game features
        
        Args:
            url: Supabase project URL (if None, will try to get from environment)
            key: Supabase anon key (if None, will try to get from environment)
        """
        load_dotenv()

        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and KEY must be provided either as parameters or environment variables")
        
        self.supabase: Client = create_client(self.url, self.key)
        self.current_user = None
        self.current_session = None
        self.game_session_id = None
        self.game_start_time = None
        
        # Try to restore existing session
        self._restore_session()
    
    # ==================== AUTHENTICATION FUNCTIONS ====================
    
    def sign_up(self, email: str, password: str, username: str = None) -> Dict[str, Any]:
        """
        Sign up a new user
        
        Args:
            email: User's email address
            password: User's password
            username: Optional username (will use email if not provided)
            
        Returns:
            Dictionary containing user data or error information
        """
        try:
            # Prepare user metadata
            user_metadata = {}
            if username:
                user_metadata['username'] = username
            else:
                user_metadata['username'] = email.split('@')[0]  # Use email prefix as username
            
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })
            
            if response.user:
                self.current_user = response.user
                self.current_session = response.session
                
                # Create user profile
                self._create_user_profile(response.user.id, user_metadata['username'], email)
                
                print(f"✅ Successfully signed up user: {user_metadata['username']}")
                return {
                    "success": True,
                    "user": response.user,
                    "message": "Sign up successful! Please check your email for verification."
                }
            else:
                return {"success": False, "error": "Sign up failed"}
                
        except Exception as e:
            print(f"❌ Sign up error: {e}")
            return {"success": False, "error": str(e)}
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in an existing user
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary containing user data or error information
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                self.current_user = response.user
                self.current_session = response.session
                
                # Get user profile
                profile = self.get_user_profile()
                username = profile.get('username', email.split('@')[0]) if profile else email.split('@')[0]
                
                print(f"✅ Successfully signed in: {username}")
                return {
                    "success": True,
                    "user": response.user,
                    "profile": profile,
                    "message": f"Welcome back, {username}!"
                }
            else:
                return {"success": False, "error": "Invalid credentials"}
                
        except Exception as e:
            print(f"❌ Sign in error: {e}")
            return {"success": False, "error": str(e)}
    
    def sign_out(self) -> Dict[str, Any]:
        """
        Sign out the current user
        
        Returns:
            Dictionary containing success status
        """
        try:
            # End current game session if active
            if self.game_session_id:
                self.end_game_session()
            
            # Clean up any remaining sessions for this user
            if self.is_authenticated():
                try:
                    self.supabase.table("game_sessions").delete().eq("user_id", self.current_user.id).execute()
                except Exception as cleanup_error:
                    print(f"Note: Could not clean up sessions during sign out: {cleanup_error}")
            
            response = self.supabase.auth.sign_out()
            
            self.current_user = None
            self.current_session = None
            self.game_session_id = None
            self.game_start_time = None
            
            print("✅ Successfully signed out")
            return {"success": True, "message": "Successfully signed out"}
            
        except Exception as e:
            print(f"❌ Sign out error: {e}")
            return {"success": False, "error": str(e)}
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self.current_user is not None and self.current_session is not None
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current user information"""
        if self.current_user:
            profile = self.get_user_profile()
            return {
                "id": self.current_user.id,
                "email": self.current_user.email,
                "username": profile.get('username') if profile else self.current_user.email.split('@')[0],
                "profile": profile
            }
        return None
    
    def _restore_session(self):
        """Try to restore existing session"""
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                self.current_user = session.user
                self.current_session = session
                print(f"✅ Restored session for: {session.user.email}")
        except Exception as e:
            print(f"No existing session to restore: {e}")
    
    def _create_user_profile(self, user_id: str, username: str, email: str):
        """Create user profile in database"""
        try:
            profile_data = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "total_score": 0,
                "games_played": 0,
                "best_time": None,
                "favorite_maze_size": None,
                "created_at": datetime.now().isoformat()
            }
            
            return self.supabase.table("user_profiles").insert(profile_data).execute()
        except Exception as e:
            print(f"Error creating user profile: {e}")
    
    # ==================== USER PROFILE FUNCTIONS ====================
    
    def get_user_profile(self) -> Optional[Dict]:
        """Get current user's profile"""
        if not self.is_authenticated():
            return None
        
        try:
            response = self.supabase.table("user_profiles").select("*").eq("user_id", self.current_user.id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, updates: Dict[str, Any]) -> Optional[Dict]:
        """Update current user's profile"""
        if not self.is_authenticated():
            return None
        
        try:
            response = self.supabase.table("user_profiles").update(updates).eq("user_id", self.current_user.id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return None
    
    # ==================== GAME SESSION FUNCTIONS ====================
    def cleanup_user_sessions(self) -> bool:
        """Clean up any existing game sessions for the current user"""
        if not self.is_authenticated():
            return False
        
        try:
            response = self.supabase.table("game_sessions").delete().eq("user_id", self.current_user.id).execute()
            if response.data:
                print(f"🧹 Cleaned up {len(response.data)} session(s)")
            return True
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            return False

    def start_game_session(self, maze_width: int = None, maze_height: int = None, difficulty: str = "medium") -> Optional[str]:
        """
        Start a new game session
        
        Args:
            maze_width: Width of the maze (optional)
            maze_height: Height of the maze (optional)
            difficulty: Difficulty level (optional)
            
        Returns:
            Game session ID or None if failed
        """
        try:
            self.game_start_time = time.time()
            
            # First, check if there's an existing session for this user and clean it up
            if self.is_authenticated():
                try:
                    # Delete any existing sessions for this user
                    existing_sessions = self.supabase.table("game_sessions").delete().eq("user_id", self.current_user.id).execute()
                    if existing_sessions.data:
                        print(f"🧹 Cleaned up {len(existing_sessions.data)} existing session(s)")
                except Exception as cleanup_error:
                    print(f"Note: Could not clean up existing sessions: {cleanup_error}")
            
            session_data = {
                "player_name": self.get_current_user()['username'] if self.is_authenticated() else "Anonymous",
                "user_id": self.current_user.id if self.is_authenticated() else None,
                "session_start": datetime.now().isoformat()
            }
            
            response = self.supabase.table("game_sessions").insert(session_data).execute()
            
            if response.data:
                self.game_session_id = response.data[0]['id']
                print(f"✅ Started game session: {self.game_session_id}")
                return self.game_session_id
            
        except Exception as e:
            print(f"Error starting game session: {e}")
            
            # If we still get a duplicate key error, try to update the existing session instead
            if "duplicate key" in str(e) and self.is_authenticated():
                try:
                    print("🔄 Attempting to update existing session...")
                    update_data = {
                        "session_start": datetime.now().isoformat(),
                        "session_end": None  # Reset end time only (remove final_score reference)
                    }
                    
                    response = self.supabase.table("game_sessions").update(update_data).eq("user_id", self.current_user.id).execute()
                    
                    if response.data:
                        self.game_session_id = response.data[0]['id']
                        print(f"✅ Updated existing game session: {self.game_session_id}")
                        return self.game_session_id
                        
                except Exception as update_error:
                    print(f"Failed to update existing session: {update_error}")
        
        return None
    
    def end_game_session(self, final_score: int = 0, completed: bool = False) -> Optional[Dict]:
        """
        End the current game session
        
        Args:
            final_score: Final score achieved
            completed: Whether the maze was completed
            
        Returns:
            Updated session data or None if failed
        """
        if not self.game_session_id:
            return None
        
        try:
            session_duration = time.time() - self.game_start_time if self.game_start_time else 0
            
            update_data = {
                "session_end": datetime.now().isoformat()
                # Remove final_score and session_duration since these columns don't exist
            }
            
            response = self.supabase.table("game_sessions").update(update_data).eq("id", self.game_session_id).execute()
            
            # Update user profile stats if authenticated
            if self.is_authenticated() and completed:
                self._update_user_stats(final_score, session_duration)
            
            self.game_session_id = None
            self.game_start_time = None
            
            print(f"✅ Ended game session. Score: {final_score}, Duration: {session_duration:.1f}s")
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"Error ending game session: {e}")
            return None

    
    def _update_user_stats(self, score: int, duration: float):
        """Update user statistics after completing a game"""
        try:
            profile = self.get_user_profile()
            if not profile:
                return
            
            updates = {
                "total_score": profile.get("total_score", 0) + score,
                "games_played": profile.get("games_played", 0) + 1,
                "last_played": datetime.now().isoformat()
            }
            
            # Update best time if this is better
            if profile.get("best_time") is None or duration < profile.get("best_time", float('inf')):
                updates["best_time"] = duration
            
            self.update_user_profile(updates)
            
        except Exception as e:
            print(f"Error updating user stats: {e}")
    
    # ==================== GAME PROGRESS FUNCTIONS ====================
    
    def save_game_progress(self, score, completion_time=None, maze_size=None, completed=True):
        """Save game progress/results"""
        if not self.is_authenticated():
            return False
        
        try:
            user = self.get_current_user()
            if not user:
                return False
            
            # Prepare the basic progress data
            progress_data = {
                'user_id': user['id'],
                'player_name': user['username'],  # ADD THIS LINE - get player_name from user
                'score': score,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add optional fields only if provided
            if completion_time is not None:
                progress_data['completion_time'] = completion_time
            
            if maze_size is not None:
                progress_data['maze_size'] = maze_size
            
            if completed is not None:
                progress_data['completed'] = completed
            
            # Try to get current game session ID if it exists
            if hasattr(self, 'current_session_id') and self.current_session_id:
                progress_data['game_session_id'] = self.current_session_id
            
            # Insert the progress data
            result = self.supabase.table('player_progress').insert(progress_data).execute()
            
            if result.data:
                print(f"✅ Game progress saved: Score {score}")
                return True
            else:
                print("❌ No data returned from progress save")
                return False
                
        except Exception as e:
            print(f"Error saving game progress: {e}")
            # Try a simpler version without optional columns
            try:
                simple_data = {
                    'user_id': user['id'],
                    'player_name': user['username'],  # ADD THIS LINE HERE TOO
                    'score': score,
                    'timestamp': datetime.now().isoformat()
                }
                result = self.supabase.table('player_progress').insert(simple_data).execute()
                if result.data:
                    print(f"✅ Game progress saved (simple): Score {score}")
                    return True
            except Exception as e2:
                print(f"Error with simple save: {e2}")
            
            return False
    
    def save_guest_progress(self, player_name: str, score: int, completion_time: float = None, maze_size: str = None) -> bool:
        """Save progress for guest players"""
        try:
            progress_data = {
                'user_id': None,  # No user ID for guests
                'player_name': player_name,
                'score': score,
                'timestamp': datetime.now().isoformat()
            }
            
            if completion_time is not None:
                progress_data['completion_time'] = completion_time
            
            if maze_size is not None:
                progress_data['maze_size'] = maze_size
            
            result = self.supabase.table('player_progress').insert(progress_data).execute()
            
            if result.data:
                print(f"✅ Guest progress saved: {player_name} - Score {score}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error saving guest progress: {e}")
            return False
    
    def get_user_progress(self, limit: int = 10) -> List[Dict]:
        """Get current user's game progress history"""
        if not self.is_authenticated():
            return []
        
        try:
            # Fix ordering syntax here too
            response = self.supabase.table("player_progress").select("*").eq("user_id", self.current_user.id).order("timestamp", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Error getting user progress: {e}")
            return []

    def get_leaderboard(self, limit: int = 10, maze_size: str = None) -> List[Dict]:
        """
        Get leaderboard data
        
        Args:
            limit: Number of top scores to return
            maze_size: Filter by specific maze size (optional)
            
        Returns:
            List of top scores
        """
        try:
            query = self.supabase.table("player_progress").select("player_name, score, completion_time, maze_size, timestamp")
            
            if maze_size:
                query = query.eq("maze_size", maze_size)
            
            # Fix ordering syntax here too
            response = query.order("score", desc=True).limit(limit).execute()
            return response.data
            
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []
    
    def get_personal_best(self, maze_size: str = None) -> Optional[Dict]:
        """Get current user's personal best score"""
        if not self.is_authenticated():
            return None
        
        try:
            query = self.supabase.table("player_progress").select("*").eq("user_id", self.current_user.id)
            
            if maze_size:
                query = query.eq("maze_size", maze_size)
            
            # Fix: Use proper ordering syntax - just "score.desc" not "score.desc.asc"
            response = query.order("score", desc=True).limit(1).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"Error getting personal best: {e}")
            return None
    
    # ==================== MAZE FUNCTIONS ====================
    
    def save_maze(self, maze_name: str, maze_data: List[List[str]], 
                  difficulty: str = "medium", is_public: bool = True) -> Optional[Dict]:
        """
        Save a maze layout
        
        Args:
            maze_name: Name for the maze
            maze_data: 2D array representing the maze
            difficulty: Difficulty level
            is_public: Whether other users can access this maze
            
        Returns:
            Saved maze record or None if failed
        """
        try:
            current_user = self.get_current_user()
            
            maze_record = {
                "maze_name": maze_name,
                "maze_data": maze_data,  # Supabase handles JSON automatically
                "difficulty": difficulty,
                "width": len(maze_data[0]) if maze_data else 0,
                "height": len(maze_data) if maze_data else 0,
                "created_by": current_user['username'] if current_user else "Anonymous",
                "user_id": self.current_user.id if self.is_authenticated() else None,
                "is_public": is_public,
                "created_at": datetime.now().isoformat(),
                "play_count": 0,
                "average_score": 0
            }
            
            response = self.supabase.table("mazes").insert(maze_record).execute()
            
            if response.data:
                print(f"✅ Saved maze: {maze_name}")
                return response.data[0]
            
        except Exception as e:
            print(f"Error saving maze: {e}")
        
        return None
    
    def get_user_mazes(self) -> List[Dict]:
        """Get mazes created by current user"""
        if not self.is_authenticated():
            return []
        
        try:
            response = self.supabase.table("mazes").select("*").eq("user_id", self.current_user.id).order("created_at.desc").execute()
            return response.data
        except Exception as e:
            print(f"Error getting user mazes: {e}")
            return []
    
    def get_public_mazes(self, difficulty: str = None, limit: int = 20) -> List[Dict]:
        """
        Get public mazes
        
        Args:
            difficulty: Filter by difficulty (optional)
            limit: Maximum number of mazes to return
            
        Returns:
            List of public mazes
        """
        try:
            query = self.supabase.table("mazes").select("*").eq("is_public", True)
            
            if difficulty:
                query = query.eq("difficulty", difficulty)
            
            response = query.order("play_count.desc").limit(limit).execute()
            return response.data
            
        except Exception as e:
            print(f"Error getting public mazes: {e}")
            return []
    
    def load_maze(self, maze_id: int) -> Optional[Dict]:
        """
        Load a specific maze and increment play count
        
        Args:
            maze_id: ID of the maze to load
            
        Returns:
            Maze data or None if not found
        """
        try:
            # Get the maze
            response = self.supabase.table("mazes").select("*").eq("id", maze_id).execute()
            
            if response.data:
                maze = response.data[0]
                
                # Increment play count
                self.supabase.table("mazes").update({
                    "play_count": maze.get("play_count", 0) + 1
                }).eq("id", maze_id).execute()
                
                return maze
            
        except Exception as e:
            print(f"Error loading maze: {e}")
        
        return None
    
    def rate_maze(self, maze_id: int, rating: int, comment: str = None) -> Optional[Dict]:
        """
        Rate a maze (1-5 stars)
        
        Args:
            maze_id: ID of the maze to rate
            rating: Rating from 1-5
            comment: Optional comment
            
        Returns:
            Rating record or None if failed
        """
        if not self.is_authenticated():
            return None
        
        if not 1 <= rating <= 5:
            print("Rating must be between 1 and 5")
            return None
        
        try:
            rating_data = {
                "maze_id": maze_id,
                "user_id": self.current_user.id,
                "rating": rating,
                "comment": comment,
                "created_at": datetime.now().isoformat()
            }
            
            # Use upsert to allow users to update their rating
            response = self.supabase.table("maze_ratings").upsert(rating_data).execute()
            
            # Update maze average rating
            self._update_maze_rating(maze_id)
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"Error rating maze: {e}")
            return None
    
    def _update_maze_rating(self, maze_id: int):
        """Update average rating for a maze"""
        try:
            # Get all ratings for this maze
            ratings_response = self.supabase.table("maze_ratings").select("rating").eq("maze_id", maze_id).execute()
            
            if ratings_response.data:
                ratings = [r["rating"] for r in ratings_response.data]
                average_rating = sum(ratings) / len(ratings)
                
                # Update maze with new average
                self.supabase.table("mazes").update({
                    "average_rating": round(average_rating, 2),
                    "rating_count": len(ratings)
                }).eq("id", maze_id).execute()
                
        except Exception as e:
            print(f"Error updating maze rating: {e}")
    
    # ==================== SOCIAL FEATURES ====================
    
    def add_friend(self, friend_username: str) -> Optional[Dict]:
        """
        Send a friend request
        
        Args:
            friend_username: Username of the person to add as friend
            
        Returns:
            Friend request record or None if failed
        """
        if not self.is_authenticated():
            return None
        
        try:
            # Find the friend's user profile
            friend_response = self.supabase.table("user_profiles").select("user_id, username").eq("username", friend_username).execute()
            
            if not friend_response.data:
                print(f"User '{friend_username}' not found")
                return None
            
            friend_user_id = friend_response.data[0]["user_id"]
            
            if friend_user_id == self.current_user.id:
                print("You cannot add yourself as a friend")
                return None
            
            # Check if friendship already exists (in either direction)
            existing = self.supabase.table("friendships").select("*").or_(
                f"and(user_id.eq.{self.current_user.id},friend_id.eq.{friend_user_id}),"
                f"and(user_id.eq.{friend_user_id},friend_id.eq.{self.current_user.id})"
            ).execute()
            
            if existing.data:
                print("Friendship already exists or request pending")
                return None
            
            # Create friend request
            friendship_data = {
                "user_id": self.current_user.id,
                "friend_id": friend_user_id,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table("friendships").insert(friendship_data).execute()
            
            if response.data:
                print(f"✅ Friend request sent to {friend_username}")
                return response.data[0]
            
        except Exception as e:
            print(f"Error adding friend: {e}")
        
        return None
    
    def get_friends(self, status: str = "accepted") -> List[Dict]:
        """
        Get user's friends
        
        Args:
            status: Filter by status (pending, accepted, blocked)
            
        Returns:
            List of friends
        """
        if not self.is_authenticated():
            return []
        
        try:
            # Get friendships and join with user profiles manually
            friendships_response = self.supabase.table("friendships").select(
                "id, friend_id, status, created_at"
            ).eq("user_id", self.current_user.id).eq("status", status).execute()
            
            if not friendships_response.data:
                return []
            
            # Get friend profiles separately
            friend_ids = [f["friend_id"] for f in friendships_response.data]
            
            if friend_ids:
                profiles_response = self.supabase.table("user_profiles").select(
                    "user_id, username, total_score, games_played"
                ).in_("user_id", friend_ids).execute()
                
                # Combine the data
                profiles_by_id = {p["user_id"]: p for p in profiles_response.data}
                
                friends = []
                for friendship in friendships_response.data:
                    friend_profile = profiles_by_id.get(friendship["friend_id"])
                    if friend_profile:
                        friends.append({
                            "id": friendship["id"],
                            "friend_id": friendship["friend_id"],
                            "status": friendship["status"],
                            "created_at": friendship["created_at"],
                            "friend_profile": friend_profile
                        })
                
                return friends
            
            return []
            
        except Exception as e:
            print(f"Error getting friends: {e}")
            return []

    def get_friend_leaderboard(self) -> List[Dict]:
        """Get leaderboard of friends' best scores"""
        friends = self.get_friends("accepted")
        if not friends:
            return []
        
        try:
            friend_ids = [f["friend_id"] for f in friends]
            friend_ids.append(self.current_user.id)  # Include current user
            
            # Get best scores for each friend
            response = self.supabase.table("player_progress").select(
                "user_id, player_name, score, completion_time, maze_size, timestamp"
            ).in_("user_id", friend_ids).order("score", desc=True).execute()
            
            # Group by user and get their best score
            user_best = {}
            for record in response.data:
                user_id = record["user_id"]
                if user_id not in user_best or record["score"] > user_best[user_id]["score"]:
                    user_best[user_id] = record
            
            return sorted(user_best.values(), key=lambda x: x["score"], reverse=True)
            
        except Exception as e:
            print(f"Error getting friend leaderboard: {e}")
            return []
    
    # ==================== ACHIEVEMENTS SYSTEM ====================
    
    def check_achievements(self, score: int, completion_time: float, maze_size: str) -> List[Dict]:
        """
        Check and award achievements based on game performance
        
        Args:
            score: Score achieved
            completion_time: Time taken to complete
            maze_size: Size of maze completed
            
        Returns:
            List of newly earned achievements
        """
        if not self.is_authenticated():
            return []
        
        new_achievements = []
        
        try:
            # Get user's current achievements
            current_achievements = self.supabase.table("user_achievements").select("achievement_id").eq("user_id", self.current_user.id).execute()
            earned_ids = [a["achievement_id"] for a in current_achievements.data] if current_achievements.data else []
            
            # Define achievement conditions
            achievements_to_check = [
                {"id": "first_completion", "name": "First Steps", "condition": lambda: len(self.get_user_progress()) == 1},
                {"id": "speed_demon", "name": "Speed Demon", "condition": lambda: completion_time < 30},
                {"id": "high_scorer", "name": "High Scorer", "condition": lambda: score > 1000},
                {"id": "maze_master", "name": "Maze Master", "condition": lambda: len(self.get_user_progress()) >= 10},
                {"id": "perfectionist", "name": "Perfectionist", "condition": lambda: score > 2000 and completion_time < 60},
            ]
            
            for achievement in achievements_to_check:
                if achievement["id"] not in earned_ids and achievement["condition"]():
                    # Award achievement
                    achievement_data = {
                        "user_id": self.current_user.id,
                        "achievement_id": achievement["id"],
                        "achievement_name": achievement["name"],
                        "earned_at": datetime.now().isoformat(),
                        "game_score": score,
                        "game_time": completion_time
                    }
                    
                    result = self.supabase.table("user_achievements").insert(achievement_data).execute()
                    if result.data:
                        new_achievements.append(achievement)
                        print(f"🏆 Achievement unlocked: {achievement['name']}")
            
        except Exception as e:
            print(f"Error checking achievements: {e}")
        
        return new_achievements
    
    def get_user_achievements(self) -> List[Dict]:
        """Get all achievements earned by current user"""
        if not self.is_authenticated():
            return []
        
        try:
            # Fix: Use proper ordering syntax
            response = self.supabase.table("user_achievements").select("*").eq("user_id", self.current_user.id).order("earned_at", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Error getting achievements: {e}")
            return []
    
    # ==================== ANALYTICS AND STATS ====================
    
    def get_game_analytics(self) -> Dict[str, Any]:
        """Get comprehensive game analytics for current user"""
        if not self.is_authenticated():
            return {}
        
        try:
            progress = self.get_user_progress(limit=100)  # Get more data for analytics
            profile = self.get_user_profile()
            
            if not progress:
                return {"message": "No game data available"}
            
            # Calculate statistics
            scores = [p["score"] for p in progress if p["score"]]
            times = [p["completion_time"] for p in progress if p["completion_time"]]
            
            analytics = {
                "total_games": len(progress),
                "total_score": sum(scores),
                "average_score": sum(scores) / len(scores) if scores else 0,
                "best_score": max(scores) if scores else 0,
                "worst_score": min(scores) if scores else 0,
                "average_time": sum(times) / len(times) if times else 0,
                "best_time": min(times) if times else 0,
                "favorite_maze_size": self._get_most_common([p["maze_size"] for p in progress if p["maze_size"]]),
                "recent_trend": self._calculate_score_trend(progress[-10:] if len(progress) >= 10 else progress),
                "achievements_count": len(self.get_user_achievements()),
                "profile_stats": profile
            }
            
            return analytics
            
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {}
    
    def _get_most_common(self, items: List) -> str:
        """Get most common item from list"""
        if not items:
            return "None"
        return max(set(items), key=items.count)
    
    def _calculate_score_trend(self, recent_games: List[Dict]) -> str:
        """Calculate if scores are trending up, down, or stable"""
        if len(recent_games) < 3:
            return "insufficient_data"
        
        scores = [g["score"] for g in recent_games if g["score"]]
        if len(scores) < 3:
            return "insufficient_data"
        
        # Simple trend calculation
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        if avg_second > avg_first * 1.1:
            return "improving"
        elif avg_second < avg_first * 0.9:
            return "declining"
        else:
            return "stable"
    
    # ==================== BACKUP AND EXPORT FUNCTIONS ====================
    
    def export_user_data(self) -> Dict[str, Any]:
        """Export all user data for backup purposes"""
        if not self.is_authenticated():
            return {}
        
        try:
            export_data = {
                "user_profile": self.get_user_profile(),
                "game_progress": self.get_user_progress(limit=1000),
                "achievements": self.get_user_achievements(),
                "created_mazes": self.get_user_mazes(),
                "friends": self.get_friends(),
                "analytics": self.get_game_analytics(),
                "export_date": datetime.now().isoformat()
            }
            
            print("✅ User data exported successfully")
            return export_data
            
        except Exception as e:
            print(f"Error exporting user data: {e}")
            return {}
    
    def backup_game_state(self, current_maze: List[List[str]], player_position: Tuple[float, float], 
                         player_angle: float, current_score: int, game_time: float) -> Optional[Dict]:
        """
        Save current game state for resuming later
        
        Args:
            current_maze: Current maze layout
            player_position: Player's current position (x, y)
            player_angle: Player's current viewing angle
            current_score: Current score
            game_time: Time elapsed in current game
            
        Returns:
            Backup record or None if failed
        """
        if not self.is_authenticated():
            return None
        
        try:
            backup_data = {
                "user_id": self.current_user.id,
                "game_session_id": self.game_session_id,
                "maze_data": current_maze,
                "player_x": player_position[0],
                "player_y": player_position[1],
                "player_angle": player_angle,
                "current_score": current_score,
                "game_time": game_time,
                "saved_at": datetime.now().isoformat()
            }
            
            # Delete any existing backup for this user (only keep latest)
            self.supabase.table("game_backups").delete().eq("user_id", self.current_user.id).execute()
            
            # Insert new backup
            response = self.supabase.table("game_backups").insert(backup_data).execute()
            
            if response.data:
                print("✅ Game state backed up")
                return response.data[0]
            
        except Exception as e:
            print(f"Error backing up game state: {e}")
        
        return None
    
    def restore_game_state(self) -> Optional[Dict]:
        """Restore the most recent game state backup"""
        if not self.is_authenticated():
            return None
        
        try:
            response = self.supabase.table("game_backups").select("*").eq("user_id", self.current_user.id).order("saved_at.desc").limit(1).execute()
            
            if response.data:
                backup = response.data[0]
                print("✅ Game state restored")
                return backup
            else:
                print("No game backup found")
                return None
            
        except Exception as e:
            print(f"Error restoring game state: {e}")
            return None
    
    def delete_game_backup(self) -> bool:
        """Delete current user's game backup"""
        if not self.is_authenticated():
            return False
        
        try:
            response = self.supabase.table("game_backups").delete().eq("user_id", self.current_user.id).execute()
            print("✅ Game backup deleted")
            return True
        except Exception as e:
            print(f"Error deleting game backup: {e}")
            return False
    
    # ==================== UTILITY AND ADMIN FUNCTIONS ====================
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global game statistics"""
        try:
            # Get total games played
            total_games = self.supabase.table("player_progress").select("id", count="exact").execute()
            
            # Get total users
            total_users = self.supabase.table("user_profiles").select("user_id", count="exact").execute()
            
            # Get average score
            scores_response = self.supabase.table("player_progress").select("score").execute()
            scores = [s["score"] for s in scores_response.data if s["score"]]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Get most popular maze size
            maze_sizes = [p["maze_size"] for p in scores_response.data if p["maze_size"]]
            popular_size = self._get_most_common(maze_sizes)
            
            return {
                "total_games_played": total_games.count,
                "total_registered_users": total_users.count,
                "average_score": round(avg_score, 2),
                "highest_score": max(scores) if scores else 0,
                "most_popular_maze_size": popular_size,
                "total_mazes_created": len(self.get_public_mazes(limit=1000))
            }
            
        except Exception as e:
            print(f"Error getting global stats: {e}")
            return {}
    
    def search_players(self, search_term: str, limit: int = 10) -> List[Dict]:
        """
        Search for players by username
        
        Args:
            search_term: Username to search for
            limit: Maximum results to return
            
        Returns:
            List of matching player profiles
        """
        try:
            response = self.supabase.table("user_profiles").select("username, total_score, games_played, created_at").ilike("username", f"%{search_term}%").limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Error searching players: {e}")
            return []
    
    def report_issue(self, issue_type: str, description: str, game_data: Dict = None) -> Optional[Dict]:
        """
        Report a bug or issue
        
        Args:
            issue_type: Type of issue (bug, suggestion, etc.)
            description: Description of the issue
            game_data: Optional game state data
            
        Returns:
            Issue report record or None if failed
        """
        try:
            current_user = self.get_current_user()
            
            report_data = {
                "user_id": self.current_user.id if self.is_authenticated() else None,
                "username": current_user['username'] if current_user else "Anonymous",
                "issue_type": issue_type,
                "description": description,
                "game_data": game_data,
                "reported_at": datetime.now().isoformat(),
                "status": "open"
            }
            
            response = self.supabase.table("issue_reports").insert(report_data).execute()
            
            if response.data:
                print("✅ Issue reported successfully")
                return response.data[0]
            
        except Exception as e:
            print(f"Error reporting issue: {e}")
        
        return None


# ==================== GAME INTEGRATION CLASS ====================

class MazeGameIntegration:
    """
    High-level integration class for the maze game
    Provides simplified methods for common game operations
    """
    
    def __init__(self, db_handler: GameSupabaseHandler):
        self.db = db_handler
        self.current_game_start = None
        self.current_score = 0
        
    def login_flow(self) -> Dict[str, Any]:
        """Interactive login flow"""
        print("\n=== MAZE GAME LOGIN ===")
        print("1. Sign In")
        print("2. Sign Up")
        print("3. Play as Guest")
        
        choice = input("Choose an option (1-3): ").strip()
        
        if choice == "1":
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            return self.db.sign_in(email, password)
            
        elif choice == "2":
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            username = input("Username (optional): ").strip() or None
            return self.db.sign_up(email, password, username)
            
        elif choice == "3":
            print("Playing as guest - progress won't be saved")
            return {"success": True, "guest": True}
            
        else:
            print("Invalid choice")
            return {"success": False, "error": "Invalid choice"}
    
    def start_new_game(self, maze_width: int, maze_height: int, difficulty: str = "medium"):
        """Start a new game session"""
        self.current_game_start = time.time()
        self.current_score = 0
        
        if self.db.is_authenticated():
            self.db.start_game_session(maze_width, maze_height, difficulty)
        
        print(f"🎮 Started new {difficulty} game: {maze_width}x{maze_height}")
    
    def update_score(self, points: int):
        """Update current game score"""
        self.current_score += points
    
    def complete_game(self, final_score: int = None) -> Dict[str, Any]:
        """Complete the current game and save progress"""
        if final_score is not None:
            self.current_score = final_score
        
        completion_time = time.time() - self.current_game_start if self.current_game_start else 0
        
        result = {"score": self.current_score, "time": completion_time}
        
        if self.db.is_authenticated():
            # Save progress
            progress = self.db.save_game_progress(
                score=self.current_score,
                completion_time=completion_time
            )
            
            # End game session
            session = self.db.end_game_session(self.current_score, completed=True)
            
            # Check achievements
            achievements = self.db.check_achievements(
                self.current_score, 
                completion_time, 
                f"{20}x{20}"  # You can make this dynamic
            )
            
            result.update({
                "progress_saved": progress is not None,
                "new_achievements": achievements,
                "session_ended": session is not None
            })
            
            # Show results
            self.show_game_results(result)
        
        return result
    
    def show_game_results(self, result: Dict[str, Any]):
        """Display game completion results"""
        print(f"\n🎉 GAME COMPLETED! 🎉")
        print(f"Final Score: {result['score']}")
        print(f"Completion Time: {result['time']:.1f} seconds")
        
        if result.get("new_achievements"):
            print("\n🏆 NEW ACHIEVEMENTS:")
            for achievement in result["new_achievements"]:
                print(f"  • {achievement['name']}")
        
        if self.db.is_authenticated():
            personal_best = self.db.get_personal_best()
            if personal_best and result['score'] > personal_best['score']:
                print("🌟 NEW PERSONAL BEST!")
    
    def show_leaderboard(self, limit: int = 10):
        """Display current leaderboard"""
        leaderboard = self.db.get_leaderboard(limit)
        
        print(f"\n🏆 TOP {limit} SCORES 🏆")
        print("-" * 40)
        
        for i, entry in enumerate(leaderboard, 1):
            time_str = f" ({entry['completion_time']:.1f}s)" if entry.get('completion_time') else ""
            print(f"{i:2d}. {entry['player_name']:<15} {entry['score']:>6}{time_str}")
        
        if not leaderboard:
            print("No scores recorded yet!")
    
    def show_user_stats(self):
        """Display current user's statistics"""
        if not self.db.is_authenticated():
            print("Sign in to view your statistics!")
            return
        
        analytics = self.db.get_game_analytics()
        
        print(f"\n📊 YOUR STATISTICS 📊")
        print("-" * 30)
        print(f"Games Played: {analytics.get('total_games', 0)}")
        print(f"Best Score: {analytics.get('best_score', 0)}")
        print(f"Average Score: {analytics.get('average_score', 0):.1f}")
        print(f"Best Time: {analytics.get('best_time', 0):.1f}s")
        print(f"Achievements: {analytics.get('achievements_count', 0)}")
        print(f"Trend: {analytics.get('recent_trend', 'N/A').title()}")


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Example usage of the enhanced handler
    try:
        # Initialize the handler
        db = GameSupabaseHandler()
        game = MazeGameIntegration(db)
        
        print("🎮 Enhanced Maze Game Database Handler")
        print("=====================================")
        
        # Example login flow
        # login_result = game.login_flow()
        
        # Example game session
        # if login_result.get("success"):
        #     game.start_new_game(20, 20, "medium")
        #     game.update_score(100)
        #     game.complete_game(1250)
        #     game.show_leaderboard()
        #     game.show_user_stats()
        
        print("✅ Enhanced handler initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure to set SUPABASE_URL and SUPABASE_KEY environment variables")

