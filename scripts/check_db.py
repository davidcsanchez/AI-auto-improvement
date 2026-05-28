import sqlite3
import pandas as pd

def inspect_database(db_path: str):
    # Connect to your SQLite database
    conn = sqlite3.connect(db_path)
    
    try:
        # Check what tables exist in the database
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table';", conn
        )
        print("Available Tables:\n", tables, "\n" + "-"*40)
        
        # Replace 'processed_tickets' with your actual table name
        df_processed = pd.read_sql_query("SELECT * FROM ticketsample LIMIT 10", conn)
        print("--- Recently Processed Tickets ---")
        print(df_processed)
        
        df_golden = pd.read_sql_query("SELECT * FROM goldensample", conn)
        print(df_golden)
        
    finally:
        conn.close()

if __name__ == "__main__":
    # Point this to your actual local database file
    inspect_database("test.db")