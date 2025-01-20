"""
llm.py

Module to handle all interactions with the Large Language Model (LLM).
Uses Google Generative AI (Gemini) in this example.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env if present
load_dotenv()

# Configure the Gemini / Google Generative AI client
# Note: In production, do not hardcode API keys! Use environment variables.
api_key = os.getenv("GOOGLE_GENAI_API_KEY", "AIzaSyBvsMef-geqcJJDof6hZitpLWSUxhiR1Ds")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

def query_gpt(prompt, system_message=None):
    """
    Send user input to Gemini, optionally including a system_message for context,
    and return the AI's textual response.

    Args:
        prompt (str): The user's message or query.
        system_message (str, optional): Additional instructions or context.

    Returns:
        str: AI-generated response from the model.
    """
    if system_message:
        full_prompt = f"{system_message}\n\n{prompt}"
    else:
        full_prompt = prompt

    response = model.generate_content(full_prompt)
    return response.text

def build_dm_context(world_id, campaign_id, session_id=None):
    """
    Build a textual context string from the current game data:
      - World description
      - Campaign description
      - Player summaries
      - Recent events in the session log (if session_id is provided).

    This context is used to give the LLM better situational awareness.
    """
    from ai_dm.models import get_world_by_id, get_campaign_by_id, get_players_in_campaign, get_session
    
    # World details
    world = get_world_by_id(world_id)
    if not world:
        world_summary = "World: Unknown\nDescription: No data."
    else:
        world_summary = f"World: {world['name']}\nDescription: {world['description']}"

    # Campaign details
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        campaign_summary = "Campaign: Unknown\nDescription: No data."
    else:
        campaign_summary = f"Campaign: {campaign['title']}\nDescription: {campaign['description']}"

    # Player summaries
    players = get_players_in_campaign(campaign_id)
    player_lines = []
    for i, player in enumerate(players, start=1):
        char_name = player.get('character_name') or f"Unnamed-Char-{player['player_id']}"
        race = player.get('race') or "Unknown Race"
        char_class = player.get('class') or "Unknown Class"
        level = player.get('level', 1)

        line = (f"Player #{i} [ID {player['player_id']}]: "
                f"{char_name}, Level {level} {race} {char_class}")
        player_lines.append(line)
    if player_lines:
        players_text = "Party Members:\n" + "\n".join(player_lines)
    else:
        players_text = "No players found in this campaign."

    # Recent session events
    recent_events = ""
    if session_id:
        session = get_session(session_id)
        if session and session.get('session_log'):
            recent_events = f"\nRecent Events:\n{session['session_log']}"

    # Combine all context
    context = (
        f"{world_summary}\n\n{campaign_summary}\n\n{players_text}"
        f"{recent_events}"
    )
    return context
