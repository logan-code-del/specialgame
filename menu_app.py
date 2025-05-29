import pygame
import sys
import subprocess
import json
import os
import time
from supabase_handler import GameSupabaseHandler
from chat_interface import ChatInterface, FriendChatWindow

class MenuApplication:
    def __init__(self):
        pygame.init()
        
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 600
        self.win = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Maze Game - Main Menu")
        self.clock = pygame.time.Clock()
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        self.BLUE = (0, 100, 200)
        self.GREEN = (0, 200, 0)
        self.RED = (200, 0, 0)
        self.YELLOW = (255, 255, 0)
        self.GOLD = (255, 215, 0)
        
        # Initialize database
        try:
            self.db_handler = GameSupabaseHandler()
            print("✅ Database connected successfully!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.db_handler = None
        
        # Menu state
        self.game_state = "menu"
        self.menu_selection = 0
        self.error_message = ""
        self.success_message = ""
        
        # Login state
        self.login_mode = "signin"
        self.input_mode = None
        self.login_data = {"email": "", "password": "", "username": ""}
        
        # Friends state
        self.show_friends_menu = False
        self.friend_menu_tab = "friends"
        self.friend_search_text = ""
        self.friend_message = ""
        self.selected_request = 0
        
        # Chat interfaces
        self.chat_interface = ChatInterface(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.db_handler)
        self.friend_chat_window = FriendChatWindow(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.db_handler)
        
        # Chat state
        self.chat_visible = False
        self.chat_type = "game"  # "game", "global", "friend"
        self.selected_friend_id = None
    
    def draw_text(self, text, x, y, color=None, font_size=24, center=False):
        """Helper function to draw text"""
        if color is None:
            color = self.WHITE
        font = pygame.font.SysFont('Arial', font_size)
        text_surface = font.render(str(text), True, color)
        
        if center:
            x = x - text_surface.get_width() // 2
        
        self.win.blit(text_surface, (x, y))
        return text_surface.get_height()
    
    def start_game(self):
        """Launch the game application"""
        try:
            # Prepare game configuration
            config = {
                'player_name': 'Guest',
                'user_id': None,
                'session_data': None
            }
            
            # Add user data if authenticated
            if self.db_handler and self.db_handler.is_authenticated():
                user = self.db_handler.get_current_user()
                if user:
                    config['player_name'] = user['username']
                    config['user_id'] = user['id']
                    config['session_data'] = self.db_handler.get_session_data()
            
            # Save config to file
            with open('game_config.json', 'w') as f:
                json.dump(config, f)
            
            print("🎮 Launching game...")
            
            # Launch game process
            subprocess.run([sys.executable, 'maze_game.py'], check=True)
            
            # Game has returned, check for results
            self.process_game_result()
            
        except subprocess.CalledProcessError as e:
            self.error_message = f"Game crashed: {e}"
            print(f"❌ Game process failed: {e}")
        except Exception as e:
            self.error_message = f"Failed to start game: {e}"
            print(f"❌ Failed to start game: {e}")
    
    def process_game_result(self):
        """Process the result from the completed game"""
        try:
            if os.path.exists('game_result.json'):
                with open('game_result.json', 'r') as f:
                    result = json.load(f)
                
                # Display result message
                if result['completed']:
                    self.success_message = f"Game completed! Score: {result['score']}, Time: {result['completion_time']:.1f}s"
                else:
                    self.success_message = f"Game ended. Score: {result['score']}"
                
                # Save guest progress if not saved to database
                if not result.get('saved_to_db', False) and self.db_handler:
                    try:
                        self.db_handler.save_guest_progress(
                            player_name=result['player_name'],
                            score=result['score'],
                            completion_time=result['completion_time'],
                            maze_size=result['maze_size']
                        )
                        print("✅ Guest progress saved to database")
                    except Exception as e:
                        print(f"❌ Failed to save guest progress: {e}")
                
                # Clean up
                os.remove('game_result.json')
                if os.path.exists('game_config.json'):
                    os.remove('game_config.json')
                
                print(f"🎮 Game result processed: {result}")
                
        except Exception as e:
            self.error_message = f"Failed to process game result: {e}"
            print(f"❌ Failed to process game result: {e}")
    
    def draw_menu(self):
        """Draw the main menu"""
        self.win.fill(self.BLACK)
        
        # Title
        self.draw_text("MAZE GAME", self.SCREEN_WIDTH // 2, 50, self.GOLD, 36, center=True)
        
        # Menu options
        menu_options = [
            "1. Start New Game",
            "2. View Leaderboard", 
            "3. Login/Signup",
            "4. View Statistics",
            "5. Friends & Social",
            "6. Chat",
            "7. Quit"
        ]
        
        if self.db_handler and self.db_handler.is_authenticated():
            user = self.db_handler.get_current_user()
            if user:
                self.draw_text(f"Logged in as: {user['username']}", self.SCREEN_WIDTH // 2, 100, self.GREEN, 18, center=True)
                menu_options[2] = "3. Logout"
        
        for i, option in enumerate(menu_options):
            color = self.YELLOW if i == self.menu_selection else self.WHITE
            self.draw_text(option, self.SCREEN_WIDTH // 2, 150 + i * 40, color, 20, center=True)
        
        # Instructions
        self.draw_text("Use UP/DOWN arrows to navigate, ENTER to select", self.SCREEN_WIDTH // 2, 400, self.GRAY, 16, center=True)
        
        # Database status
        if self.db_handler:
            status_color = self.GREEN if self.db_handler.is_authenticated() else self.BLUE
            status_text = "Database: Connected" if self.db_handler.is_authenticated() else "Database: Available (Guest Mode)"
        else:
            status_color = self.RED
            status_text = "Database: Offline"
        self.draw_text(status_text, 10, self.SCREEN_HEIGHT - 30, status_color, 14)
        
        # Show messages
        if self.error_message:
            self.draw_text(self.error_message, self.SCREEN_WIDTH // 2, 350, self.RED, 16, center=True)
        if self.success_message:
            self.draw_text(self.success_message, self.SCREEN_WIDTH // 2, 350, self.GREEN, 16, center=True)
        
        # Draw chat interface if visible
        if self.chat_visible:
            self.chat_interface.draw(self.win)
    
    def draw_login(self):
        """Draw the login/signup screen"""
        self.win.fill(self.BLACK)
        
        title = "SIGN UP" if self.login_mode == "signup" else "SIGN IN"
        self.draw_text(title, self.SCREEN_WIDTH // 2, 50, self.GOLD, 32, center=True)
        
        toggle_text = "Switch to Sign In (TAB)" if self.login_mode == "signup" else "Switch to Sign Up (TAB)"
        self.draw_text(toggle_text, self.SCREEN_WIDTH // 2, 100, self.GRAY, 16, center=True)
        
        # Input fields
        y_pos = 150
        
        # Email field
        email_color = self.YELLOW if self.input_mode == "email" else self.WHITE
        self.draw_text("Email:", 100, y_pos, email_color)
        email_display = self.login_data["email"] + ("_" if self.input_mode == "email" else "")
        self.draw_text(email_display, 200, y_pos, email_color)
        y_pos += 40
        
        # Password field
        password_color = self.YELLOW if self.input_mode == "password" else self.WHITE
        self.draw_text("Password:", 100, y_pos, password_color)
        password_display = "*" * len(self.login_data["password"]) + ("_" if self.input_mode == "password" else "")
        self.draw_text(password_display, 200, y_pos, password_color)
        y_pos += 40
        
        # Username field (only for signup)
        if self.login_mode == "signup":
            username_color = self.YELLOW if self.input_mode == "username" else self.WHITE
            self.draw_text("Username:", 100, y_pos, username_color)
            username_display = self.login_data["username"] + ("_" if self.input_mode == "username" else "")
            self.draw_text(username_display, 200, y_pos, username_color)
            y_pos += 40
        
        # Instructions
        self.draw_text("Click on fields to edit, ENTER to submit, ESC to go back", self.SCREEN_WIDTH // 2, y_pos + 20, self.GRAY, 16, center=True)
        
        # Submit button
        submit_text = "Create Account" if self.login_mode == "signup" else "Sign In"
        self.draw_text(f"Press ENTER: {submit_text}", self.SCREEN_WIDTH // 2, y_pos + 60, self.GREEN, 18, center=True)
        
        # Guest option
        self.draw_text("Press F1: Continue as Guest", self.SCREEN_WIDTH // 2, y_pos + 90, self.BLUE, 18, center=True)
        
        # Show messages
        if self.error_message:
            self.draw_text(self.error_message, self.SCREEN_WIDTH // 2, y_pos + 130, self.RED, 16, center=True)
        if self.success_message:
            self.draw_text(self.success_message, self.SCREEN_WIDTH // 2, y_pos + 130, self.GREEN, 16, center=True)
    
    def draw_leaderboard(self):
        """Draw the leaderboard screen"""
        self.win.fill(self.BLACK)
        
        self.draw_text("LEADERBOARD", self.SCREEN_WIDTH // 2, 30, self.GOLD, 32, center=True)
        
        if self.db_handler:
            leaderboard = self.db_handler.get_leaderboard(limit=10)
            
            if leaderboard:
                # Headers
                self.draw_text("Rank", 50, 80, self.WHITE, 18)
                self.draw_text("Player", 120, 80, self.WHITE, 18)
                self.draw_text("Score", 300, 80, self.WHITE, 18)
                self.draw_text("Time", 400, 80, self.WHITE, 18)
                self.draw_text("Date", 500, 80, self.WHITE, 18)
                
                # Draw line
                pygame.draw.line(self.win, self.WHITE, (50, 105), (self.SCREEN_WIDTH - 50, 105), 2)
                
                # Leaderboard entries
                for i, entry in enumerate(leaderboard):
                    y = 120 + i * 25
                    color = self.GOLD if i == 0 else self.WHITE
                    
                    self.draw_text(f"{i+1}", 50, y, color, 16)
                    self.draw_text(entry['player_name'][:15], 120, y, color, 16)
                    self.draw_text(str(entry['score']), 300, y, color, 16)
                    
                    if entry.get('completion_time'):
                        time_str = f"{entry['completion_time']:.1f}s"
                        self.draw_text(time_str, 400, y, color, 16)
                    
                    if entry.get('timestamp'):
                        date_str = entry['timestamp'][:10]
                        self.draw_text(date_str, 500, y, color, 16)
            else:
                self.draw_text("No scores recorded yet!", self.SCREEN_WIDTH // 2, 200, self.GRAY, 20, center=True)
        else:
            self.draw_text("Database not available", self.SCREEN_WIDTH // 2, 200, self.RED, 20, center=True)
        
        self.draw_text("Press ESC to go back", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50, self.GRAY, 16, center=True)
    
    def draw_stats(self):
        """Draw the statistics screen"""
        self.win.fill(self.BLACK)
        
        self.draw_text("STATISTICS", self.SCREEN_WIDTH // 2, 30, self.GOLD, 32, center=True)
        
        if self.db_handler and self.db_handler.is_authenticated():
            user = self.db_handler.get_current_user()
            analytics = self.db_handler.get_game_analytics()
            
            if user and analytics:
                y_pos = 100
                
                # User info
                self.draw_text(f"Player: {user['username']}", 100, y_pos, self.WHITE, 20)
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
                    self.draw_text(stat, 100, y_pos, self.WHITE, 18)
                    y_pos += 30
            else:
                self.draw_text("Unable to load statistics", self.SCREEN_WIDTH // 2, 200, self.RED, 20, center=True)
        else:
            self.draw_text("Please log in to view statistics", self.SCREEN_WIDTH // 2, 200, self.GRAY, 20, center=True)
        
        self.draw_text("Press ESC to go back", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50, self.GRAY, 16, center=True)
    
    def draw_friends_menu(self):
        """Draw the friends and social menu"""
        self.win.fill(self.BLACK)
        
        self.draw_text("FRIENDS & SOCIAL", self.SCREEN_WIDTH // 2, 30, self.GOLD, 32, center=True)
        
        if not self.db_handler or not self.db_handler.is_authenticated():
            self.draw_text("Please log in to use social features", self.SCREEN_WIDTH // 2, 200, self.RED, 20, center=True)
            self.draw_text("Press ESC to go back", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50, self.GRAY, 16, center=True)
            return
        
        # Tab navigation
        tabs = ["Friends", "Incoming", "Sent"]
        tab_width = 120
        start_x = self.SCREEN_WIDTH // 2 - (len(tabs) * tab_width) // 2
        
        for i, tab in enumerate(tabs):
            x = start_x + i * tab_width
            color = self.YELLOW if (i == 0 and self.friend_menu_tab == "friends") or \
                                (i == 1 and self.friend_menu_tab == "requests") or \
                                (i == 2 and self.friend_menu_tab == "sent") else self.WHITE
            self.draw_text(f"{i+1}. {tab}", x, 70, color, 18)
        
        self.draw_text("Press 1/2/3 to switch tabs", self.SCREEN_WIDTH // 2, 95, self.GRAY, 14, center=True)
        
        if self.friend_menu_tab == "friends":
            self.draw_friends_tab()
        elif self.friend_menu_tab == "requests":
            self.draw_requests_tab()
        elif self.friend_menu_tab == "sent":
            self.draw_sent_tab()
        
        # Show messages
        if self.friend_message:
            color = self.GREEN if any(word in self.friend_message.lower() for word in ["sent", "accepted", "success"]) else self.RED
            self.draw_text(self.friend_message, self.SCREEN_WIDTH // 2, 400, color, 16, center=True)
        
        # Instructions
        self.draw_text("Press ESC to go back", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50, self.GRAY, 16, center=True)
        self.draw_text("Press C to open chat with selected friend", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 30, self.GRAY, 16, center=True)
    
    def draw_friends_tab(self):
        """Draw the friends list tab"""
        # Add friend section
        self.draw_text("Add Friend:", 50, 120, self.WHITE, 20)
        
        # Draw input box
        input_box_color = self.YELLOW if self.input_mode == "friend_search" else self.WHITE
        pygame.draw.rect(self.win, (50, 50, 50), (200, 115, 400, 30))
        pygame.draw.rect(self.win, input_box_color, (200, 115, 400, 30), 2)
        
        search_display = self.friend_search_text + ("_" if self.input_mode == "friend_search" else "")
        self.draw_text(search_display, 205, 120, input_box_color, 18)
        self.draw_text("(Click to type, ENTER to send)", 50, 150, self.GRAY, 14)
        
        # Friends list
        friends = self.db_handler.get_friends("accepted") if self.db_handler else []
        self.draw_text(f"Your Friends ({len(friends)}):", 50, 180, self.WHITE, 20)
        
        y_pos = 210
        if friends:
            for i, friend in enumerate(friends[:6]):
                friend_name = friend.get('friend_profile', {}).get('username', 'Unknown')
                friend_score = friend.get('friend_profile', {}).get('total_score', 0)
                
                # Highlight selected friend
                color = self.YELLOW if i == self.selected_request else self.WHITE
                prefix = "→ " if i == self.selected_request else "  "
                
                self.draw_text(f"{prefix}{friend_name} (Score: {friend_score})", 70, y_pos, color, 16)
                y_pos += 25
                
            # Store selected friend ID for chat
            if 0 <= self.selected_request < len(friends):
                self.selected_friend_id = friends[self.selected_request]['friend_id']
            else:
                self.selected_friend_id = None
        else:
            self.draw_text("No friends yet. Add some!", 70, y_pos, self.GRAY, 16)
            self.selected_friend_id = None
    
    def draw_requests_tab(self):
        """Draw incoming friend requests tab"""
        pending_requests = self.db_handler.get_pending_friend_requests() if self.db_handler else []
        self.draw_text(f"Incoming Friend Requests ({len(pending_requests)}):", 50, 120, self.WHITE, 20)
        
        if pending_requests:
            self.draw_text("Use UP/DOWN arrows, ENTER to accept, DELETE to decline", 50, 145, self.GRAY, 14)
            
            y_pos = 170
            for i, request in enumerate(pending_requests[:8]):
                sender_name = request.get('sender_profile', {}).get('username', 'Unknown')
                sender_score = request.get('sender_profile', {}).get('total_score', 0)
                
                # Highlight selected request
                color = self.YELLOW if i == self.selected_request else self.WHITE
                prefix = "→ " if i == self.selected_request else "  "
                
                self.draw_text(f"{prefix}{sender_name} (Score: {sender_score})", 70, y_pos, color, 16)
                y_pos += 25
            
            if self.selected_request < len(pending_requests):
                self.draw_text("ENTER = Accept | DELETE = Decline", self.SCREEN_WIDTH // 2, 350, self.GREEN, 16, center=True)
        else:
            self.draw_text("No pending requests", 70, 170, self.GRAY, 16)

    def draw_sent_tab(self):
        """Draw sent friend requests tab"""
        sent_requests = self.db_handler.get_sent_friend_requests() if self.db_handler else []
        self.draw_text(f"Sent Friend Requests ({len(sent_requests)}):", 50, 120, self.WHITE, 20)
        
        y_pos = 150
        if sent_requests:
            for request in sent_requests[:8]:
                recipient_name = request.get('recipient_profile', {}).get('username', 'Unknown')
                self.draw_text(f"• {recipient_name} (Pending...)", 70, y_pos, self.GRAY, 16)
                y_pos += 25
        else:
            self.draw_text("No pending sent requests", 70, y_pos, self.GRAY, 16)
    
    def draw_chat_screen(self):
        """Draw the chat screen"""
        self.win.fill(self.BLACK)
        
        # Title
        self.draw_text("CHAT", self.SCREEN_WIDTH // 2, 30, self.GOLD, 32, center=True)
        
        if not self.db_handler or not self.db_handler.is_authenticated():
            self.draw_text("Please log in to use chat features", self.SCREEN_WIDTH // 2, 200, self.RED, 20, center=True)
            self.draw_text("Press ESC to go back", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50, self.GRAY, 16, center=True)
            return
        
        # Chat type tabs
        tabs = ["Game Chat", "Global Chat", "Friend Chat"]
        tab_width = 150
        start_x = self.SCREEN_WIDTH // 2 - (len(tabs) * tab_width) // 2
        
        for i, tab in enumerate(tabs):
            x = start_x + i * tab_width
            is_selected = (i == 0 and self.chat_type == "game") or \
                          (i == 1 and self.chat_type == "global") or \
                          (i == 2 and self.chat_type == "friend")
            color = self.YELLOW if is_selected else self.WHITE
            self.draw_text(f"{i+1}. {tab}", x, 70, color, 18)
        
        # Instructions
        self.draw_text("Press 1/2/3 to switch chat types", self.SCREEN_WIDTH // 2, 95, self.GRAY, 14, center=True)
        
        # Draw the appropriate chat interface
        if self.chat_type == "friend" and self.selected_friend_id:
            # Draw friend chat window
            self.friend_chat_window.is_visible = True
            self.friend_chat_window.select_friend(self.selected_friend_id)
            self.friend_chat_window.draw(self.win)
        else:
            # Draw regular chat interface
            self.chat_interface.is_visible = True
            self.chat_interface.set_chat_type(self.chat_type, self.selected_friend_id)
            self.chat_interface.draw(self.win)
        
        # Back button
        self.draw_text("Press ESC to go back", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 30, self.GRAY, 16, center=True)
    
    def handle_friends_input(self, event):
        """Handle input for friends screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_state = "menu"
                self.input_mode = None
                self.friend_message = ""
            
            # Tab switching
            elif event.key == pygame.K_1:
                self.friend_menu_tab = "friends"
                self.selected_request = 0
            elif event.key == pygame.K_2:
                self.friend_menu_tab = "requests"
                self.selected_request = 0
            elif event.key == pygame.K_3:
                self.friend_menu_tab = "sent"
                self.selected_request = 0
            
            # Open chat with selected friend
            elif event.key == pygame.K_c and self.friend_menu_tab == "friends" and self.selected_friend_id:
                self.chat_type = "friend"
                self.game_state = "chat"
                return
            
            # Handle requests tab navigation
            elif self.friend_menu_tab == "requests":
                pending_requests = self.db_handler.get_pending_friend_requests() if self.db_handler else []
                
                if event.key == pygame.K_UP and pending_requests:
                    self.selected_request = (self.selected_request - 1) % len(pending_requests)
                elif event.key == pygame.K_DOWN and pending_requests:
                    self.selected_request = (self.selected_request + 1) % len(pending_requests)
                elif event.key == pygame.K_RETURN and pending_requests and self.selected_request < len(pending_requests):
                    # Accept friend request
                    request = pending_requests[self.selected_request]
                    if self.db_handler.respond_to_friend_request(request["id"], True):
                        sender_name = request.get('sender_profile', {}).get('username', 'Unknown')
                        self.friend_message = f"Accepted friend request from {sender_name}!"
                    else:
                        self.friend_message = "Failed to accept friend request"
                elif event.key == pygame.K_DELETE and pending_requests and self.selected_request < len(pending_requests):
                    # Decline friend request
                    request = pending_requests[self.selected_request]
                    if self.db_handler.respond_to_friend_request(request["id"], False):
                        sender_name = request.get('sender_profile', {}).get('username', 'Unknown')
                        self.friend_message = f"Declined friend request from {sender_name}"
                    else:
                        self.friend_message = "Failed to decline friend request"
            
            # Handle friends tab navigation
            elif self.friend_menu_tab == "friends":
                friends = self.db_handler.get_friends("accepted") if self.db_handler else []
                
                if event.key == pygame.K_UP and friends:
                    self.selected_request = (self.selected_request - 1) % len(friends)
                elif event.key == pygame.K_DOWN and friends:
                    self.selected_request = (self.selected_request + 1) % len(friends)
                elif event.key == pygame.K_RETURN and self.input_mode == "friend_search":
                    if self.friend_search_text.strip() and self.db_handler and self.db_handler.is_authenticated():
                        result = self.db_handler.add_friend(self.friend_search_text.strip())
                        if result:
                            self.friend_message = f"Friend request sent to {self.friend_search_text}!"
                            self.friend_search_text = ""
                        else:
                            self.friend_message = "Failed to send request. User may not exist."
                    else:
                        self.friend_message = "Please log in to add friends"
                    self.input_mode = None
                
                elif self.input_mode == "friend_search" and event.unicode.isprintable():
                    if len(self.friend_search_text) < 20:
                        self.friend_search_text += event.unicode
                
                elif event.key == pygame.K_BACKSPACE and self.input_mode == "friend_search":
                    self.friend_search_text = self
                    self.friend_search_text = self.friend_search_text[:-1]
        
        elif event.type == pygame.MOUSEBUTTONDOWN and self.friend_menu_tab == "friends":
            mouse_x, mouse_y = event.pos
            if 115 <= mouse_y <= 145 and 200 <= mouse_x <= 600:
                self.input_mode = "friend_search"
            else:
                self.input_mode = None

    def handle_menu_input(self, event):
        """Handle input for main menu"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_selection = (self.menu_selection - 1) % 7  # Updated for new menu item
            elif event.key == pygame.K_DOWN:
                self.menu_selection = (self.menu_selection + 1) % 7  # Updated for new menu item
            elif event.key == pygame.K_RETURN:
                self.error_message = ""
                self.success_message = ""
                
                if self.menu_selection == 0:  # Start New Game
                    self.start_game()
                elif self.menu_selection == 1:  # View Leaderboard
                    self.game_state = "leaderboard"
                elif self.menu_selection == 2:  # Login/Logout
                    if self.db_handler and self.db_handler.is_authenticated():
                        # Logout
                        self.db_handler.sign_out()
                        self.success_message = "Logged out successfully"
                    else:
                        # Go to login
                        self.game_state = "login"
                elif self.menu_selection == 3:  # View Statistics
                    self.game_state = "stats"
                elif self.menu_selection == 4:  # Friends & Social
                    self.game_state = "friends"
                elif self.menu_selection == 5:  # Chat
                    if self.db_handler and self.db_handler.is_authenticated():
                        self.game_state = "chat"
                        self.chat_type = "game"  # Default to game chat
                    else:
                        self.error_message = "Please log in to use chat"
                elif self.menu_selection == 6:  # Quit
                    pygame.quit()
                    sys.exit(0)
            
            # Quick chat toggle with C key
            elif event.key == pygame.K_c:
                if self.db_handler and self.db_handler.is_authenticated():
                    self.chat_visible = not self.chat_visible
                    self.chat_interface.toggle_visibility()
    
    def handle_login_input(self, event):
        """Handle input for login screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_state = "menu"
                self.input_mode = None
                self.error_message = ""
                self.success_message = ""
            
            elif event.key == pygame.K_TAB:
                # Toggle between signin and signup
                self.login_mode = "signup" if self.login_mode == "signin" else "signin"
                self.input_mode = None
                self.error_message = ""
                self.success_message = ""
            
            elif event.key == pygame.K_F1:
                # Continue as guest
                self.game_state = "menu"
                self.success_message = "Playing as guest"
            
            elif event.key == pygame.K_RETURN:
                # Submit form
                if self.login_mode == "signin":
                    if self.login_data["email"] and self.login_data["password"]:
                        result = self.db_handler.sign_in(self.login_data["email"], self.login_data["password"])
                        if result.get("success"):
                            self.success_message = f"Welcome back, {result.get('username', 'User')}!"
                            self.error_message = ""
                            self.game_state = "menu"
                        else:
                            self.error_message = result.get("error", "Sign in failed")
                            self.success_message = ""
                    else:
                        self.error_message = "Please fill in all fields"
                
                elif self.login_mode == "signup":
                    if self.login_data["email"] and self.login_data["password"]:
                        username = self.login_data["username"] if self.login_data["username"] else None
                        result = self.db_handler.sign_up(self.login_data["email"], self.login_data["password"], username)
                        if result.get("success"):
                            self.success_message = "Account created! Please check your email to verify."
                            self.error_message = ""
                        else:
                            self.error_message = result.get("error", "Sign up failed")
                            self.success_message = ""
                    else:
                        self.error_message = "Please fill in email and password"
            
            elif self.input_mode and event.unicode.isprintable():
                # Add character to current field
                if len(self.login_data[self.input_mode]) < 50:
                    self.login_data[self.input_mode] += event.unicode
            
            elif event.key == pygame.K_BACKSPACE and self.input_mode:
                # Remove character from current field
                self.login_data[self.input_mode] = self.login_data[self.input_mode][:-1]
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Click to select input field
            mouse_x, mouse_y = event.pos
            
            if 150 <= mouse_y <= 190:  # Email field
                self.input_mode = "email"
            elif 190 <= mouse_y <= 230:  # Password field
                self.input_mode = "password"
            elif self.login_mode == "signup" and 230 <= mouse_y <= 270:  # Username field
                self.input_mode = "username"
            else:
                self.input_mode = None
    
    def handle_chat_input(self, event):
        """Handle input for chat screen"""
        # First check if the chat interface or friend chat window wants to handle this event
        if self.chat_type == "friend" and self.selected_friend_id:
            if self.friend_chat_window.handle_event(event):
                return
        else:
            if self.chat_interface.handle_event(event):
                return
        
        # Handle our own events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_state = "menu"
                self.chat_interface.is_visible = False
                self.friend_chat_window.is_visible = False
            
            # Tab switching
            elif event.key == pygame.K_1:
                self.chat_type = "game"
                self.chat_interface.set_chat_type("game")
            elif event.key == pygame.K_2:
                self.chat_type = "global"
                self.chat_interface.set_chat_type("global")
            elif event.key == pygame.K_3:
                if self.selected_friend_id:
                    self.chat_type = "friend"
                    self.chat_interface.set_chat_type("friend", self.selected_friend_id)
                else:
                    self.error_message = "Select a friend first"
    
    def run(self):
        """Main menu loop"""
        while True:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                
                # Handle input based on current state
                if self.game_state == "menu":
                    # Check if chat interface should handle the event
                    if self.chat_visible and self.chat_interface.handle_event(event):
                        pass  # Event was handled by chat
                    else:
                        self.handle_menu_input(event)
                elif self.game_state == "login":
                    self.handle_login_input(event)
                elif self.game_state == "friends":
                    self.handle_friends_input(event)
                elif self.game_state == "chat":
                    self.handle_chat_input(event)
                elif self.game_state in ["leaderboard", "stats"]:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.game_state = "menu"
            
            # Update chat if visible
            if self.chat_visible or self.game_state == "chat":
                self.chat_interface.update()
                self.friend_chat_window.refresh_data()
            
            # Clear messages after some time
            if time.time() % 5 < 0.1:
                self.error_message = ""
                self.success_message = ""
            
            # Render based on current state
            if self.game_state == "menu":
                self.draw_menu()
            elif self.game_state == "login":
                self.draw_login()
            elif self.game_state == "leaderboard":
                self.draw_leaderboard()
            elif self.game_state == "stats":
                self.draw_stats()
            elif self.game_state == "friends":
                self.draw_friends_menu()
            elif self.game_state == "chat":
                self.draw_chat_screen()
            
            pygame.display.flip()
            self.clock.tick(30)  # Lower FPS for menu is fine


if __name__ == "__main__":
    menu = MenuApplication()
    menu.run()