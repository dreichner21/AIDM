"""
models.py

Contains helper functions to interact with the SQLite database
for worlds, campaigns, players, sessions, etc.
"""

import json
from ai_dm.db import get_connection

#
# 1) WORLDS
#

def create_world(name, description):
    """
    Create a new world record in the database.
    Returns the newly inserted row's ID.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO worlds (name, description)
        VALUES (?, ?)
        """,
        (name, description)
    )
    world_id = cur.lastrowid
    conn.commit()
    conn.close()
    return world_id

def get_world_by_id(world_id):
    """
    Retrieve a single world by ID, or None if not found.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM worlds WHERE world_id = ?", (world_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

#
# 2) CAMPAIGNS
#

def create_campaign(title, world_id, description):
    """
    Create a new campaign record tied to a specific world.
    Returns the newly inserted row's ID.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO campaigns (title, world_id, description)
        VALUES (?, ?, ?)
        """,
        (title, world_id, description)
    )
    campaign_id = cur.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def get_campaign_by_id(campaign_id):
    """
    Retrieve a single campaign by ID, or None if not found.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM campaigns WHERE campaign_id = ?", (campaign_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

#
# 3) PLAYERS
#

def create_player(campaign_id, name, character_name, race, char_class, level, stats=None, inventory=None, character_sheet=None):
    """
    Create a new player in a given campaign with basic character info.

    Args:
        campaign_id (int): The campaign ID to attach this player to.
        name (str): Real-life player's name.
        character_name (str): In-game character name.
        race (str): Character's race (e.g., Dwarf).
        char_class (str): Character's class (e.g., Fighter).
        level (int): Character's current level.
        stats (dict): Optional dictionary of stats (e.g. STR, DEX).
        inventory (dict): Optional dictionary of items.
        character_sheet (dict): Optional dictionary for more complex data.
    Returns:
        int: The newly inserted player ID.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO players (campaign_id, name, character_name, race, class, level, stats, inventory, character_sheet)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            campaign_id,
            name,
            character_name,
            race,
            char_class,
            level,
            json.dumps(stats) if stats else None,
            json.dumps(inventory) if inventory else None,
            json.dumps(character_sheet) if character_sheet else None
        ),
    )
    player_id = cur.lastrowid
    conn.commit()
    conn.close()
    return player_id

def get_players_in_campaign(campaign_id):
    """
    Return a list of all players in a specific campaign,
    parsing JSON fields into Python objects.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE campaign_id = ?", (campaign_id,))
    rows = cur.fetchall()
    conn.close()

    players = []
    for row in rows:
        player_dict = dict(row)
        # Convert JSON strings to Python dicts if present
        if player_dict.get('stats'):
            player_dict['stats'] = json.loads(player_dict['stats'])
        if player_dict.get('inventory'):
            player_dict['inventory'] = json.loads(player_dict['inventory'])
        if player_dict.get('character_sheet'):
            player_dict['character_sheet'] = json.loads(player_dict['character_sheet'])
        players.append(player_dict)

    return players

def get_player_by_id(player_id):
    """
    Retrieve a single player by ID, or None if not found.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    player = dict(row)
    if player.get('stats'):
        player['stats'] = json.loads(player['stats'])
    if player.get('inventory'):
        player['inventory'] = json.loads(player['inventory'])
    if player.get('character_sheet'):
        player['character_sheet'] = json.loads(player['character_sheet'])
    return player

def update_character_sheet(player_id, sheet_data):
    """
    Update a player's character_sheet JSON data in the database.
    """
    conn = get_connection()
    cur = conn.cursor()
    json_data = json.dumps(sheet_data)
    cur.execute(
        """
        UPDATE players
        SET character_sheet = ?
        WHERE player_id = ?
        """,
        (json_data, player_id)
    )
    conn.commit()
    conn.close()

#
# 4) SESSIONS
#

def create_session(campaign_id):
    """
    Create a new session record for a given campaign.
    Returns the newly inserted session ID.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sessions (campaign_id)
        VALUES (?)
        """,
        (campaign_id,)
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_session(session_id):
    """
    Retrieve a single session by ID, or None if not found.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM sessions WHERE session_id = ?",
        (session_id,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def update_session_log(session_id, updated_log):
    """
    Update the text log of a given session by ID.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE sessions
        SET session_log = ?
        WHERE session_id = ?
        """,
        (updated_log, session_id)
    )
    conn.commit()
    conn.close()

def get_sessions_by_campaign(campaign_id):
    """
    Retrieve all sessions for a particular campaign, ordered by creation time descending.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM sessions
        WHERE campaign_id = ?
        ORDER BY created_at DESC
        """,
        (campaign_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
