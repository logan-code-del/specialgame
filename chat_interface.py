import pygame
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional
from supabase_handler import GameSupabaseHandler

class ChatInterface:
    def __init__(self, screen_width: int, screen_height: int, db_handler: GameSupabaseHandler):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.db_handler = db_handler
        
        # Chat settings
        self.chat_width = 300
        self.chat_height = 200
        self.chat_x = screen_width - self.chat_width - 10
        self.chat_y = screen_height - self.chat_height - 10
        
        # Chat state
        self.is_visible = False
        self.chat_type = "game"  # "game", "friend", "global"
        self.current_friend_id = None
        self.messages = []
        self.input_text = ""
        self.input_active = False
        self.scroll_offset = 0
        self.last_update = 0
        
        # Colors
        self.bg_color = (0, 0, 0, 180)  # Semi-transparent black
        self.border_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.input_bg_color = (50, 50, 50)
        self.input_active_color = (70, 70, 70)
        self.my_message_color = (0, 100, 200)
        self.other_message_color = (100, 100, 100)
        
        # Fonts
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 12)
        self.small_font = pygame.font.SysFont('Arial', 10)
        
        # Auto-refresh timer
        self.refresh_interval = 2.0  # Refresh every 2 seconds
        
    def toggle_visibility(self):
        """Toggle chat visibility"""
        self.is_visible = not self.is_visible
        if self.is_visible:
            self.refresh_messages()
    
    def set_chat_type(self, chat_type: str, friend_id: str = None):
        """Set the chat type and refresh messages"""
        self.chat_type = chat_type
        self.current_friend_id = friend_id
        self.refresh_messages()
    
    def refresh_messages(self):
        """Refresh messages based on current chat type"""
        try:
            if self.chat_type == "friend" and self.current_friend_id:
                self.messages = self.db_handler.get_friend_messages(self.current_friend_id)
            elif self.chat_type == "game":
                self.messages = self.db_handler.get_game_messages()
            elif self.chat_type == "global":
                self.messages = self.db_handler.get_global_messages()
            else:
                self.messages = []
            
            self.last_update = time.time()
            
        except Exception as e:
            print(f"Error refreshing messages: {e}")
            self.messages = []
    
    def send_message(self):
        """Send the current input message"""
        if not self.input_text.strip():
            return
        
        try:
            message = self.input_text.strip()
            
            if self.chat_type == "friend" and self.current_friend_id:
                self.db_handler.send_friend_message(self.current_friend_id, message)
            elif self.chat_type == "game":
                self.db_handler.send_game_message(message)
            elif self.chat_type == "global":
                self.db_handler.send_global_message(message)
            
            self.input_text = ""
            self.refresh_messages()
            
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def handle_event(self, event):
        """Handle pygame events for chat"""
        if not self.is_visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    self.send_message()
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self.input_active = False
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                    return True
                else:
                    self.input_text += event.unicode
                    return True
            else:
                if event.key == pygame.K_RETURN:
                    self.input_active = True
                    return True
                elif event.key == pygame.K_TAB:
                    # Cycle through chat types
                    if self.chat_type == "game":
                        self.set_chat_type("global")
                    elif self.chat_type == "global":
                        self.set_chat_type("game")
                    return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            
            # Check if click is in chat area
            if (self.chat_x <= mouse_x <= self.chat_x + self.chat_width and
                self.chat_y <= mouse_y <= self.chat_y + self.chat_height):
                
                # Check if click is in input area
                input_y = self.chat_y + self.chat_height - 25
                if input_y <= mouse_y <= input_y + 20:
                    self.input_active = True
                else:
                    self.input_active = False
                return True
        
        return False
    
    def update(self):
        """Update chat (auto-refresh messages)"""
        if self.is_visible and time.time() - self.last_update > self.refresh_interval:
            self.refresh_messages()
    
    def draw(self, screen):
        """Draw the chat interface"""
        if not self.is_visible:
            return
        
        # Create semi-transparent surface
        chat_surface = pygame.Surface((self.chat_width, self.chat_height))
        chat_surface.set_alpha(200)
        chat_surface.fill((0, 0, 0))
        
        # Draw border
        pygame.draw.rect(chat_surface, self.border_color, (0, 0, self.chat_width, self.chat_height), 2)
        
        # Draw title bar
        title_text = f"Chat - {self.chat_type.title()}"
        if self.chat_type == "friend" and self.current_friend_id:
            # Get friend name
            friends = self.db_handler.get_friends()
            friend_name = "Friend"
            for friend in friends:
                if friend['friend_id'] == self.current_friend_id:
                    friend_name = friend['friend_profile']['username']
                    break
            title_text = f"Chat - {friend_name}"
        
        title_surface = self.font.render(title_text, True, self.text_color)
        chat_surface.blit(title_surface, (5, 5))
        
        # Draw messages area
        message_area_height = self.chat_height - 50
        message_y = 25
        
        # Draw messages
        if self.messages:
            visible_messages = self.messages[-10:]  # Show last 10 messages
            for i, message in enumerate(visible_messages):
                y_pos = message_y + (i * 15)
                if y_pos > message_area_height:
                    break
                
                # Determine message color and prefix
                current_user = self.db_handler.get_current_user()
                is_my_message = current_user and message['sender_id'] == current_user['id']
                
                if is_my_message:
                    color = self.my_message_color
                    prefix = "You: "
                else:
                    color = self.other_message_color
                    prefix = f"{message['sender_name']}: "
                
                # Truncate long messages
                max_chars = 35
                display_message = message['message']
                if len(display_message) > max_chars:
                    display_message = display_message[:max_chars] + "..."
                
                message_text = prefix + display_message
                message_surface = self.small_font.render(message_text, True, color)
                chat_surface.blit(message_surface, (5, y_pos))
        
        # Draw input area
        input_y = self.chat_height - 25
        input_color = self.input_active_color if self.input_active else self.input_bg_color
        pygame.draw.rect(chat_surface, input_color, (5, input_y, self.chat_width - 10, 20))
        
        # Draw input text
        display_text = self.input_text
        if len(display_text) > 30:
            display_text = display_text[-30:]  # Show last 30 characters
        
        if self.input_active and int(time.time() * 2) % 2:  # Blinking cursor
            display_text += "|"
        
        input_surface = self.small_font.render(display_text, True, self.text_color)
        chat_surface.blit(input_surface, (7, input_y + 2))
        
        # Draw instructions
        if not self.input_active:
            instruction_text = "Enter=type, Tab=switch chat"
            instruction_surface = self.small_font.render(instruction_text, True, (150, 150, 150))
            chat_surface.blit(instruction_surface, (5, input_y + 2))
        
        # Blit to main screen
        screen.blit(chat_surface, (self.chat_x, self.chat_y))


class FriendChatWindow:
    """Dedicated window for friend chat management"""
    
    def __init__(self, screen_width: int, screen_height: int, db_handler: GameSupabaseHandler):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.db_handler = db_handler
        
        # Window settings
        self.window_width = 400
        self.window_height = 300
        self.window_x = (screen_width - self.window_width) // 2
        self.window_y = (screen_height - self.window_height) // 2
        
        # State
        self.is_visible = False
        self.selected_friend = None
        self.friends_list = []
        self.conversations = []
        self.current_messages = []
        self.input_text = ""
        self.input_active = False
        
        # Colors and fonts
        self.bg_color = (30, 30, 30)
        self.border_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.selected_color = (0, 100, 200)
        
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 14)
        self.small_font = pygame.font.SysFont('Arial', 12)
    
    def toggle_visibility(self):
        """Toggle window visibility"""
        self.is_visible = not self.is_visible
        if self.is_visible:
            self.refresh_data()
    
    def refresh_data(self):
        """Refresh friends list and conversations"""
        try:
            self.friends_list = self.db_handler.get_friends()
            self.conversations = self.db_handler.get_recent_conversations()
        except Exception as e:
            print(f"Error refreshing friend chat data: {e}")
    
    def select_friend(self, friend_id: str):
        """Select a friend to chat with"""
        self.selected_friend = friend_id
        try:
            self.current_messages = self.db_handler.get_friend_messages(friend_id)
            self.db_handler.mark_messages_as_read(friend_id)
        except Exception as e:
            print(f"Error loading friend messages: {e}")
    
    def send_message(self):
        """Send message to selected friend"""
        if not self.selected_friend or not self.input_text.strip():
            return
        
        try:
            self.db_handler.send_friend_message(self.selected_friend, self.input_text.strip())
            self.input_text = ""
            self.current_messages = self.db_handler.get_friend_messages(self.selected_friend)
        except Exception as e:
            print(f"Error sending friend message: {e}")
    
    def handle_event(self, event):
        """Handle events for friend chat window"""
        if not self.is_visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    self.send_message()
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self.input_active = False
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                    return True
                else:
                    self.input_text += event.unicode
                    return True
            else:
                if event.key == pygame.K_ESCAPE:
                    self.is_visible = False
                    return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            
            # Check if click is in window
            if (self.window_x <= mouse_x <= self.window_x + self.window_width and
                self.window_y <= mouse_y <= self.window_y + self.window_height):
                
                # Check friends list area (left side)
                friends_area_width = self.window_width // 3
                if self.window_x <= mouse_x <= self.window_x + friends_area_width:
                    # Calculate which friend was clicked
                    relative_y = mouse_y - self.window_y - 30
                    friend_index = relative_y // 25
                    
                    if 0 <= friend_index < len(self.friends_list):
                        friend = self.friends_list[friend_index]
                        self.select_friend(friend['friend_id'])
                        return True
                
                # Check input area
                input_y = self.window_y + self.window_height - 30
                if input_y <= mouse_y <= input_y + 25:
                    self.input_active = True
                    return True
                
                return True
        
        return False
    
    def draw(self, screen):
        """Draw the friend chat window"""
        if not self.is_visible:
            return
        
        # Draw main window
        pygame.draw.rect(screen, self.bg_color, 
                        (self.window_x, self.window_y, self.window_width, self.window_height))
        pygame.draw.rect(screen, self.border_color, 
                        (self.window_x, self.window_y, self.window_width, self.window_height), 2)
        
        # Draw title
        title_surface = self.font.render("Friend Chat", True, self.text_color)
        screen.blit(title_surface, (self.window_x + 10, self.window_y + 5))
        
        # Draw friends list (left panel)
        friends_area_width = self.window_width // 3
        pygame.draw.line(screen, self.border_color, 
                        (self.window_x + friends_area_width, self.window_y + 25),
                        (self.window_x + friends_area_width, self.window_y + self.window_height - 35), 1)
        
        # Draw friends
        for i, friend in enumerate(self.friends_list[:8]):  # Show max 8 friends
            y_pos = self.window_y + 30 + (i * 25)
            
            # Highlight selected friend
            if friend['friend_id'] == self.selected_friend:
                pygame.draw.rect(screen, self.selected_color,
                               (self.window_x + 2, y_pos - 2, friends_area_width - 4, 22))
            
            friend_name = friend['friend_profile']['username'][:12]  # Truncate long names
            friend_surface = self.small_font.render(friend_name, True, self.text_color)
            screen.blit(friend_surface, (self.window_x + 5, y_pos))
        
        # Draw chat area (right panel)
        chat_x = self.window_x + friends_area_width + 5
        chat_width = self.window_width - friends_area_width - 10
        
        if self.selected_friend and self.current_messages:
            # Draw messages
            visible_messages = self.current_messages[-8:]  # Show last 8 messages
            for i, message in enumerate(visible_messages):
                y_pos = self.window_y + 30 + (i * 25)
                
                current_user = self.db_handler.get_current_user()
                is_my_message = current_user and message['sender_id'] == current_user['id']
                
                prefix = "You: " if is_my_message else f"{message['sender_name']}: "
                color = self.selected_color if is_my_message else self.text_color
                
                # Truncate message
                max_chars = 25
                display_message = message['message']
                if len(display_message) > max_chars:
                    display_message = display_message[:max_chars] + "..."
                
                message_text = prefix + display_message
                message_surface = self.small_font.render(message_text, True, color)
                screen.blit(message_surface, (chat_x, y_pos))
        
        # Draw input area
        input_y = self.window_y + self.window_height - 30
        input_color = (70, 70, 70) if self.input_active else (50, 50, 50)
        pygame.draw.rect(screen, input_color, 
                        (chat_x, input_y, chat_width - 5, 25))
        
        # Draw input text
        if self.selected_friend:
            display_text = self.input_text
            if len(display_text) > 20:
                display_text = display_text[-20:]
            
            if self.input_active and int(time.time() * 2) % 2:
                display_text += "|"
            
            input_surface = self.small_font.render(display_text, True, self.text_color)
            screen.blit(input_surface, (chat_x + 5, input_y + 5))
        else:
            placeholder_surface = self.small_font.render("Select a friend to chat", True, (150, 150, 150))
            screen.blit(placeholder_surface, (chat_x + 5, input_y + 5))
