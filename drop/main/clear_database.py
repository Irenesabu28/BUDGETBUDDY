import sqlite3
import mysql.connector
import os

# Import MySQL configuration
try:
    from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, USE_MYSQL
    DB_CONFIG = {
        'host': MYSQL_HOST,
        'user': MYSQL_USER,
        'password': MYSQL_PASSWORD,
        'database': MYSQL_DATABASE,
        'use_sqlite': not USE_MYSQL
    }
except ImportError:
    # Default configuration if config.py doesn't exist
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'clothing_shop',
        'use_sqlite': True
    }

def clear_database():
    """Clear all transactions from the database"""
    # Check if we should use SQLite (from config)
    use_sqlite = DB_CONFIG.get('use_sqlite', True)
    
    if use_sqlite:
        # Use SQLite database
        print("Connecting to SQLite database...")
        sqlite_path = 'shop_data/transactions.db'
        
        if not os.path.exists(sqlite_path):
            print("Database file does not exist. Nothing to clear.")
            return
            
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        try:
            # Delete all records from transactions table
            cursor.execute("DELETE FROM transactions")
            conn.commit()
            print("All transactions deleted from SQLite database.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        finally:
            conn.close()
    else:
        # Use MySQL database
        print("Connecting to MySQL database...")
        try:
            conn = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
            cursor = conn.cursor()
            
            # Delete all records from transactions table
            cursor.execute("DELETE FROM transactions")
            conn.commit()
            print("All transactions deleted from MySQL database.")
            
            cursor.close()
            conn.close()
        except mysql.connector.Error as e:
            print(f"MySQL error: {e}")

if __name__ == "__main__":
    # Ask for confirmation
    confirm = input("This will delete ALL transactions from the database. Are you sure? (y/n): ")
    if confirm.lower() == 'y':
        clear_database()
    else:
        print("Operation cancelled.")
