#!/usr/bin/env python3
"""
Setup script for Automated Network Inventory
"""

import os
import subprocess
import sys


def install_requirements():
    """Install required Python packages."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully!")
    except subprocess.CalledProcessError:
        print("Failed to install requirements.")
        return False
    return True


def initialize_database():
    """Initialize the database with sample data if needed."""
    print("Initializing database...")
    # Import here to avoid issues if requirements aren't installed yet
    import sqlite3
    
    conn = sqlite3.connect('network_inventory.db')
    cursor = conn.cursor()
    
    # Check if table exists and create if not
    cursor.execute('''
        SELECT count(name) FROM sqlite_master WHERE type='table' AND name='devices'
    ''')
    
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            CREATE TABLE devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                hostname TEXT,
                mac_address TEXT,
                vendor TEXT,
                os_type TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Database initialized successfully!")
    else:
        print("Database already exists.")
    
    conn.commit()
    conn.close()


def main():
    print("Setting up Automated Network Inventory...")
    
    if not install_requirements():
        print("Could not install requirements. Exiting.")
        sys.exit(1)
    
    initialize_database()
    
    print("\nSetup completed successfully!")
    print("To run the network inventory scanner:")
    print("python network_inventory.py <network_range>")
    print("Example: python network_inventory.py 192.168.1.0/24")


if __name__ == "__main__":
    main()