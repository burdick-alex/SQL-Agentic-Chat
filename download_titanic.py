import pandas as pd
import sqlite3
import os
from urllib.request import urlretrieve

def download_titanic_dataset():
    """Download the Titanic dataset from a reliable source."""
    # URL for the Titanic dataset (using a reliable source)
    url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Download the dataset
    print("Downloading Titanic dataset...")
    try:
        urlretrieve(url, "data/titanic.csv")
        print("Dataset downloaded successfully!")
        return True
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        return False

def create_database():
    """Create SQLite database and load Titanic data."""
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect("data/titanic.db")
    cursor = conn.cursor()
    
    # Read the CSV file
    print("Reading Titanic dataset...")
    df = pd.read_csv("data/titanic.csv")
    
    # Display basic information about the dataset
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst few rows:")
    print(df.head())
    
    # Create table and insert data
    print("\nCreating database table...")
    
    # Write the dataframe to SQLite
    df.to_sql('titanic', conn, if_exists='replace', index=False)
    
    # Verify the data was inserted correctly
    cursor.execute("SELECT COUNT(*) FROM titanic")
    count = cursor.fetchone()[0]
    print(f"Successfully inserted {count} records into the database")
    
    # Show table schema
    cursor.execute("PRAGMA table_info(titanic)")
    columns = cursor.fetchall()
    print("\nTable schema:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Show some sample data
    cursor.execute("SELECT * FROM titanic LIMIT 5")
    sample_data = cursor.fetchall()
    print("\nSample data:")
    for row in sample_data:
        print(f"  {row}")
    
    # Close the connection
    conn.close()
    print("\nDatabase created successfully at data/titanic.db")

def main():
    """Main function to orchestrate the download and database creation."""
    print("=== Titanic Dataset Download and Database Creation ===")
    
    # Step 1: Download the dataset
    if download_titanic_dataset():
        # Step 2: Create the database
        create_database()
        print("\n=== Process completed successfully! ===")
        print("You can now query the database using SQLite commands or Python.")
        print("Database location: data/titanic.db")
        print("Table name: titanic")
    else:
        print("Failed to download dataset. Please check your internet connection.")

if __name__ == "__main__":
    main() 