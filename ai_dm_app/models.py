import json
from db import get_connection

#
# 1) WORLDS
#
def create_world(name, description):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO worlds (name, description)
        VALUES (?, ?)
        """,
        (name, description),
    )
    world_id = cur.lastrowid
    conn.commit()
    conn.close()
    return world_id

def get_world_by_id(world_id):
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO campaigns (title, world_id, description)
        VALUES (?, ?, ?)
        """,
        (title, world_id, description),
    )
    campaign_id = cur.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def get_campaign_by_id(campaign_id):
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO players (campaign_id, name, character_name, race, class, level, stats, inventory, character_sheet)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (campaign_id, name, character_name, race, char_class, level, 
         json.dumps(stats) if stats else None,
         json.dumps(inventory) if inventory else None,
         json.dumps(character_sheet) if character_sheet else None),
    )
    player_id = cur.lastrowid
    conn.commit()
    conn.close()
    return player_id

def get_players_in_campaign(campaign_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM players WHERE campaign_id = ?", (campaign_id,)
    )
    rows = cur.fetchall()
    conn.close()
    # Convert each row to a dict and parse JSON fields
    players = []
    for row in rows:
        player = dict(row)
        if player['stats']:
            player['stats'] = json.loads(player['stats'])
        if player['inventory']:
            player['inventory'] = json.loads(player['inventory'])
        if player['character_sheet']:
            player['character_sheet'] = json.loads(player['character_sheet'])
        players.append(player)
    return players

def get_player_by_id(player_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    player = dict(row)
    if player['stats']:
        player['stats'] = json.loads(player['stats'])
    if player['inventory']:
        player['inventory'] = json.loads(player['inventory'])
    if player['character_sheet']:
        player['character_sheet'] = json.loads(player['character_sheet'])
    return player

def update_character_sheet(player_id, sheet_data):
    """
    Update a player's character sheet with new data.
    
    Args:
        player_id (int): The ID of the player to update
        sheet_data (dict): The character sheet data to store
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sessions (campaign_id)
        VALUES (?)
        """,
        (campaign_id,),
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_session(session_id):
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE sessions
        SET session_log = ?
        WHERE session_id = ?
        """,
        (updated_log, session_id),
    )
    conn.commit()
    conn.close()

def get_sessions_by_campaign(campaign_id):
    """
    Get all sessions for a campaign.
    Args:
        campaign_id (int): ID of the campaign
    Returns:
        list: List of session dictionaries
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