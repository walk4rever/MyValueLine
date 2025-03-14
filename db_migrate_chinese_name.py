import sqlite3
from datetime import datetime

# Database file path
DB_PATH = 'app/portfolio.db'

def migrate():
    """Add chinese_name column to Stock table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting migration to add chinese_name column...")
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(stock)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'chinese_name' not in column_names:
        print("Adding chinese_name column...")
        cursor.execute("ALTER TABLE stock ADD COLUMN chinese_name TEXT")
        conn.commit()
        print("Column added successfully.")
    else:
        print("chinese_name column already exists. Skipping.")
        
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()