#!/usr/bin/env python3
"""
Private AI Database Setup Script
Creates and initializes the SQLite database required by the proxy
"""

import os
import sqlite3
from pathlib import Path

def setup_database():
    """Set up the database required by the proxy"""
    print("Setting up Private AI database...")
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Path to the database
    db_path = data_dir / "mapping_store.db"
    
    # Create database and tables
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create mappings table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mappings (
        original TEXT PRIMARY KEY,
        replacement TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create settings table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create statistics table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS statistics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        detected_count INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database created at {db_path}")
    return str(db_path)

if __name__ == "__main__":
    setup_database() 