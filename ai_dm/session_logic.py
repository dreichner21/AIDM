"""
session_logic.py

Provides higher-level functions for starting, recording, and ending
game sessions, including AI-based recaps.
"""

import json
from ai_dm.models import (
    create_session, get_session, update_session_log
)
from ai_dm.llm import query_gpt
from ai_dm.db import get_connection

def start_session(campaign_id):
    """
    Create a new session for a given campaign and return its ID.
    """
    return create_session(campaign_id)

def record_interaction(session_id, user_input, ai_response, player_id=None):
    """
    Append an interaction (player + DM response) to the session's log.
    
    Args:
        session_id (int): The session being updated.
        user_input (str): The player's input text.
        ai_response (str): The DM's response text (from the AI).
        player_id (int, optional): If provided, attempts to label the log with the player's character name.
    """
    session = get_session(session_id)
    existing_log = session["session_log"] if session["session_log"] else ""

    # Attempt to retrieve the player's actual name from the DB
    player_label = "Player"
    if player_id:
        from ai_dm.models import get_player_by_id
        player_data = get_player_by_id(player_id)
        if player_data and player_data.get('character_name'):
            player_label = player_data['character_name']
        else:
            # Fallback if no character name is set
            player_label = f"Player {player_id}"

    # Create a new chunk of text to add to the log
    new_interaction = f"\n{player_label}: {user_input}\nDM: {ai_response}\n"
    updated_log = existing_log + new_interaction

    # Save updated log to the database
    update_session_log(session_id, updated_log)

def end_session(session_id):
    """
    End a session by generating a short recap from the AI 
    and storing it in the session's 'state_snapshot' JSON.

    Returns:
        str: The AI-generated session recap.
    """
    session = get_session(session_id)
    full_log = session["session_log"] if session else ""

    # Ask the AI to create a summary
    recap_prompt = (
        "Please provide a concise summary of this D&D session, highlighting key events, "
        "important decisions, and any significant character developments:\n\n" + full_log
    )

    recap = query_gpt(
        prompt=recap_prompt,
        system_message="You are a D&D session summarizer. Provide a clear, engaging recap."
    )

    # Store the recap in the session's state_snapshot
    state = {
        "recap": recap,
        "ended_at": "NOW"  # You can store an actual timestamp or use any other marker
    }
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE sessions SET state_snapshot = ? WHERE session_id = ?",
        (json.dumps(state), session_id)
    )
    conn.commit()
    conn.close()

    return recap

def get_session_recap(session_id):
    """
    Retrieve the recap from the session's state_snapshot JSON, if present.
    """
    session = get_session(session_id)
    if session and session["state_snapshot"]:
        state = json.loads(session["state_snapshot"])
        return state.get("recap")
    return None
