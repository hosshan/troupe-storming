#!/usr/bin/env python3
"""
Add turn_count column to discussions table
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database():
    """Add turn_count column to discussions table"""
    
    # Database path
    db_path = Path("troupe_storming.db")
    
    if not db_path.exists():
        print(f"Error: Database file {db_path} not found")
        sys.exit(1)
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if turn_count column already exists
        cursor.execute("PRAGMA table_info(discussions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'turn_count' in columns:
            print("turn_count column already exists in discussions table")
            return
        
        # Add turn_count column with default value of 1
        print("Adding turn_count column to discussions table...")
        cursor.execute("ALTER TABLE discussions ADD COLUMN turn_count INTEGER DEFAULT 1")
        
        # Update existing discussions to have turn_count = 1
        cursor.execute("UPDATE discussions SET turn_count = 1 WHERE turn_count IS NULL")
        
        # Commit changes
        conn.commit()
        print("Successfully added turn_count column to discussions table")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(discussions)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"Current columns in discussions table: {columns_after}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()