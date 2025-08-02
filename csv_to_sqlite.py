#!/usr/bin/env python3
"""
CSV to SQLite Database Loader

This script loads data from a CSV file into a SQLite database.
Usage: python csv_to_sqlite.py <csv_file_path> [database_name]
"""

import sys
import sqlite3
import pandas as pd
import os
from pathlib import Path


def load_csv_to_sqlite(csv_file_path, db_name=None):
    """
    Load CSV data into a SQLite database.
    
    Args:
        csv_file_path (str): Path to the CSV file
        db_name (str, optional): Name for the SQLite database file. 
                                If not provided, uses the CSV filename with .db extension
    
    Returns:
        str: Path to the created database file
    """
    # Validate CSV file exists
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    # Generate database name if not provided
    if db_name is None:
        csv_path = Path(csv_file_path)
        db_name = csv_path.stem + ".db"
    
    # Ensure .db extension
    if not db_name.endswith('.db'):
        db_name += '.db'
    
    print(f"Loading CSV file: {csv_file_path}")
    print(f"Creating database: {db_name}")
    
    try:
        # Read CSV file
        print("Reading CSV file...")
        df = pd.read_csv(csv_file_path)
        
        print(f"CSV loaded successfully!")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"Data types: {df.dtypes.to_dict()}")
        
        # Create SQLite connection
        conn = sqlite3.connect(db_name)
        
        # Get table name from CSV filename
        table_name = Path(csv_file_path).stem.lower()
        # Replace non-alphanumeric characters with underscore
        table_name = ''.join(c if c.isalnum() else '_' for c in table_name)
        # Remove leading/trailing underscores
        table_name = table_name.strip('_')
        
        print(f"Creating table: {table_name}")
        
        # Load data into SQLite
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Get table info
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        print(f"Database created successfully!")
        print(f"Table: {table_name}")
        print(f"Rows: {row_count}")
        print(f"Columns: {len(columns_info)}")
        
        # Show column details
        print("\nColumn details:")
        for col in columns_info:
            print(f"  {col[1]} ({col[2]})")
        
        conn.close()
        
        return db_name
        
    except Exception as e:
        print(f"Error loading CSV to SQLite: {e}")
        raise


def main():
    """Main function to handle command line arguments and execute the script."""
    if len(sys.argv) < 2:
        print("Usage: python csv_to_sqlite.py <csv_file_path> [database_name]")
        print("Example: python csv_to_sqlite.py data/titanic.csv titanic_database.db")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    db_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        db_path = load_csv_to_sqlite(csv_file_path, db_name)
        print(f"\n✅ Successfully created database: {db_path}")
        print(f"You can now use this database file for your SQL operations.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 