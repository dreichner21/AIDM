import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dnd_ai_dm.db')

def get_connection():
    """
    Return a connection to the SQLite database using Row objects
    for convenient column access by name.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database and create tables if they don't exist.
    You can adjust the schema as desired (add columns, tables, etc.).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS worlds (
            world_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

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

        CREATE TABLE IF NOT EXISTS campaigns (
            campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            world_id INTEGER NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (world_id) REFERENCES worlds (world_id)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            session_log TEXT,
            state_snapshot TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (campaign_id)
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
            FOREIGN KEY (campaign_id) REFERENCES campaigns (campaign_id)
        );
        """
    )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db() 