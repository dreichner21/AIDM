"""
db.py

Provides functions to initialize and connect to the SQLite database
that stores data for the AI Dungeon Master application.
"""

import sqlite3
import os

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dnd_ai_dm.db')

def get_connection():
    """
    Create and return a connection to the SQLite database.
    Configures row_factory to allow column access by name.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database tables if they don't already exist.
    Modify or extend the schema as needed for your application.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Create all needed tables
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS worlds (
            world_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            world_id INTEGER NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (world_id) REFERENCES worlds(world_id)
        );

        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            character_name TEXT NOT NULL,
            race TEXT,
            class TEXT,
            level INTEGER DEFAULT 1,
            stats TEXT,
            inventory TEXT,
            character_sheet TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            session_log TEXT,
            state_snapshot TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
        );

        -- Optional: Extra tables for locations, NPCs, etc.
        CREATE TABLE IF NOT EXISTS locations (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (world_id) REFERENCES worlds(world_id)
        );

        CREATE TABLE IF NOT EXISTS npcs (
            npc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            role TEXT,
            backstory TEXT,
            FOREIGN KEY (world_id) REFERENCES worlds(world_id)
        );
        """
    )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
