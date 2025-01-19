import json
from models import create_session, get_session, update_session_log
from llm import query_gpt
from db import get_connection

def start_session(campaign_id):
    """
    Start a new game session.
    Args:
        campaign_id (int): ID of the campaign
    Returns:
        int: ID of the new session
    """
    session_id = create_session(campaign_id)
    return session_id

def record_interaction(session_id, user_input, ai_response):
    """
    Record a player-DM interaction in the session log.
    Args:
        session_id (int): ID of the current session
        user_input (str): Player's input/action
        ai_response (str): DM's (AI) response
    """
    session = get_session(session_id)
    existing_log = session["session_log"] if session["session_log"] else ""
    
    # Format the new interaction
    new_interaction = f"\nPlayer: {user_input}\nDM: {ai_response}\n"
    updated_log = existing_log + new_interaction if existing_log else new_interaction
    
    # Save to database
    update_session_log(session_id, updated_log)

def end_session(session_id):
    """
    End a game session and generate a recap.
    Args:
        session_id (int): ID of the session to end
    Returns:
        str: Session recap
    """
    session = get_session(session_id)
    full_log = session["session_log"]
    
    # Generate recap using GPT
    recap_prompt = (
        "Please provide a concise summary of this D&D session, highlighting key events, "
        "important decisions, and any significant character developments:\n\n" + full_log
    )
    
    recap = query_gpt(
        prompt=recap_prompt,
        system_message="You are a D&D session summarizer. Create a clear, engaging recap "
                      "that players can use to remember what happened in their last session."
    )
    
    # Update session with recap in state_snapshot
    state = {"recap": recap, "ended_at": "NOW"}
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
    Retrieve the recap for a completed session.
    Args:
        session_id (int): ID of the session
    Returns:
        str: Session recap or None if not available
    """
    session = get_session(session_id)
    if session and session["state_snapshot"]:
        state = json.loads(session["state_snapshot"])
        return state.get("recap")
    return None 