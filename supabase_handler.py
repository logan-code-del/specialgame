import os
from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

class SupabaseHandler:
    def __init__(self, url: str = None, key: str = None):
        """
        Initialize Supabase client
        
        Args:
            url: Supabase project URL (if None, will try to get from environment)
            key: Supabase anon key (if None, will try to get from environment)
        """
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and KEY must be provided either as parameters or environment variables")
        
        self.supabase: Client = create_client(self.url, self.key)
    
    # ==================== RETRIEVE DATA FUNCTIONS ====================
    
    def get_all_records(self, table_name: str) -> List[Dict]:
        """
        Retrieve all records from a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of dictionaries containing all records
        """
        try:
            response = self.supabase.table(table_name).select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error retrieving all records from {table_name}: {e}")
            return []
    
    def get_record_by_id(self, table_name: str, record_id: int) -> Optional[Dict]:
        """
        Retrieve a single record by ID
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to retrieve
            
        Returns:
            Dictionary containing the record or None if not found
        """
        try:
            response = self.supabase.table(table_name).select("*").eq("id", record_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error retrieving record {record_id} from {table_name}: {e}")
            return None
    
    def get_records_by_filter(self, table_name: str, column: str, value: Any) -> List[Dict]:
        """
        Retrieve records that match a filter condition
        
        Args:
            table_name: Name of the table
            column: Column name to filter by
            value: Value to match
            
        Returns:
            List of dictionaries containing matching records
        """
        try:
            response = self.supabase.table(table_name).select("*").eq(column, value).execute()
            return response.data
        except Exception as e:
            print(f"Error retrieving records from {table_name} where {column}={value}: {e}")
            return []
    
    def get_records_with_custom_query(self, table_name: str, select_columns: str = "*", 
                                    filters: Dict[str, Any] = None, 
                                    order_by: str = None, 
                                    limit: int = None) -> List[Dict]:
        """
        Retrieve records with custom query parameters
        
        Args:
            table_name: Name of the table
            select_columns: Columns to select (default: "*")
            filters: Dictionary of column:value pairs for filtering
            order_by: Column name to order by
            limit: Maximum number of records to return
            
        Returns:
            List of dictionaries containing matching records
        """
        try:
            query = self.supabase.table(table_name).select(select_columns)
            
            # Apply filters
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)
            
            # Apply ordering
            if order_by:
                query = query.order(order_by)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error executing custom query on {table_name}: {e}")
            return []
    
    # ==================== ADD DATA FUNCTIONS ====================
    
    def add_record(self, table_name: str, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Add a single record to a table
        
        Args:
            table_name: Name of the table
            data: Dictionary containing the data to insert
            
        Returns:
            Dictionary containing the inserted record or None if failed
        """
        try:
            response = self.supabase.table(table_name).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error adding record to {table_name}: {e}")
            return None
    
    def add_multiple_records(self, table_name: str, data_list: List[Dict[str, Any]]) -> List[Dict]:
        """
        Add multiple records to a table
        
        Args:
            table_name: Name of the table
            data_list: List of dictionaries containing the data to insert
            
        Returns:
            List of dictionaries containing the inserted records
        """
        try:
            response = self.supabase.table(table_name).insert(data_list).execute()
            return response.data
        except Exception as e:
            print(f"Error adding multiple records to {table_name}: {e}")
            return []
    
    # ==================== UPDATE DATA FUNCTIONS ====================
    
    def update_record_by_id(self, table_name: str, record_id: int, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Update a record by ID
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            data: Dictionary containing the data to update
            
        Returns:
            Dictionary containing the updated record or None if failed
        """
        try:
            response = self.supabase.table(table_name).update(data).eq("id", record_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating record {record_id} in {table_name}: {e}")
            return None
    
    def update_records_by_filter(self, table_name: str, filter_column: str, 
                               filter_value: Any, data: Dict[str, Any]) -> List[Dict]:
        """
        Update multiple records that match a filter condition
        
        Args:
            table_name: Name of the table
            filter_column: Column name to filter by
            filter_value: Value to match for filtering
            data: Dictionary containing the data to update
            
        Returns:
            List of dictionaries containing the updated records
        """
        try:
            response = self.supabase.table(table_name).update(data).eq(filter_column, filter_value).execute()
            return response.data
        except Exception as e:
            print(f"Error updating records in {table_name} where {filter_column}={filter_value}: {e}")
            return []
    
    def upsert_record(self, table_name: str, data: Dict[str, Any], 
                     conflict_columns: List[str] = None) -> Optional[Dict]:
        """
        Insert or update a record (upsert)
        
        Args:
            table_name: Name of the table
            data: Dictionary containing the data to upsert
            conflict_columns: List of columns to check for conflicts
            
        Returns:
            Dictionary containing the upserted record or None if failed
        """
        try:
            query = self.supabase.table(table_name).upsert(data)
            if conflict_columns:
                query = query.on_conflict(','.join(conflict_columns))
            
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error upserting record in {table_name}: {e}")
            return None
    
    # ==================== DELETE DATA FUNCTIONS ====================
    
    def delete_record_by_id(self, table_name: str, record_id: int) -> bool:
        """
        Delete a record by ID
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.supabase.table(table_name).delete().eq("id", record_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deleting record {record_id} from {table_name}: {e}")
            return False
    
    def delete_records_by_filter(self, table_name: str, column: str, value: Any) -> int:
        """
        Delete records that match a filter condition
        
        Args:
            table_name: Name of the table
            column: Column name to filter by
            value: Value to match
            
        Returns:
            Number of records deleted
        """
        try:
            response = self.supabase.table(table_name).delete().eq(column, value).execute()
            return len(response.data)
        except Exception as e:
            print(f"Error deleting records from {table_name} where {column}={value}: {e}")
            return 0
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def get_table_count(self, table_name: str) -> int:
        """
        Get the total number of records in a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Number of records in the table
        """
        try:
            response = self.supabase.table(table_name).select("id", count="exact").execute()
            return response.count
        except Exception as e:
            print(f"Error getting count for {table_name}: {e}")
            return 0
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            self.supabase.table(table_name).select("*").limit(1).execute()
            return True
        except Exception as e:
            return False


# ==================== EXAMPLE USAGE FUNCTIONS ====================

def example_game_data_operations():
    """
    Example functions for game-specific data operations
    """
    # Initialize the handler (make sure to set your environment variables)
    db = SupabaseHandler()
    
    # Example: Player data operations
    def save_player_progress(player_name: str, level: int, score: int, maze_size: str):
        """Save player progress to database"""
        player_data = {
            "player_name": player_name,
            "level": level,
            "score": score,
            "maze_size": maze_size,
            "timestamp": datetime.now().isoformat()
        }
        return db.add_record("player_progress", player_data)
    
    def get_player_high_scores(player_name: str):
        """Get all high scores for a specific player"""
        return db.get_records_by_filter("player_progress", "player_name", player_name)
    
    def get_leaderboard(limit: int = 10):
        """Get top scores across all players"""
        return db.get_records_with_custom_query(
            "player_progress", 
            select_columns="player_name, score, level, maze_size, timestamp",
            order_by="score.desc",
            limit=limit
        )
    
    def update_player_score(player_id: int, new_score: int):
        """Update a player's score"""
        return db.update_record_by_id("player_progress", player_id, {"score": new_score})
    
    # Example: Maze data operations
    def save_maze_layout(maze_name: str, maze_data: List[List[str]], difficulty: str):
        """Save a maze layout to database"""
        maze_record = {
            "maze_name": maze_name,
            "maze_data": json.dumps(maze_data),  # Store maze as JSON string
            "difficulty": difficulty,
            "width": len(maze_data[0]),
            "height": len(maze_data),
            "created_at": datetime.now().isoformat()
        }
        return db.add_record("mazes", maze_record)
    
    def get_maze_by_difficulty(difficulty: str):
        """Get all mazes of a specific difficulty"""
        return db.get_records_by_filter("mazes", "difficulty", difficulty)
    
    def load_maze_layout(maze_id: int):
        """Load a specific maze layout"""
        maze_record = db.get_record_by_id("mazes", maze_id)
        if maze_record:
            maze_record["maze_data"] = json.loads(maze_record["maze_data"])
        return maze_record


if __name__ == "__main__":
    # Example usage
    try:
        # You'll need to set these environment variables or pass them directly
        # export SUPABASE_URL="your-supabase-url"
        # export SUPABASE_KEY="your-supabase-anon-key"
        
        db = SupabaseHandler()
        
        # Test connection
        print("Testing Supabase connection...")
        
        # Example operations (uncomment and modify as needed)
        print(db.get_all_records("User_info"))
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to set SUPABASE_URL and SUPABASE_KEY environment variables")
