import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini API
genai.configure(api_key="AIzaSyBvsMef-geqcJJDof6hZitpLWSUxhiR1Ds")
model = genai.GenerativeModel("gemini-2.0-flash-exp")

def query_gpt(prompt, system_message=None, model_name="gemini-2.0-flash-exp"):
    """
    Send a conversation to the Gemini API and return the assistant's response.
    Args:
        prompt (str): The user's input
        system_message (str, optional): Context/instructions for the AI
        model_name (str): The model to use (ignored as we're using gemini-2.0-flash-exp)
    Returns:
        str: The AI's response
    """
    # Combine system message and prompt if provided
    full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
    
    # Generate response
    response = model.generate_content(full_prompt)
    return response.text

def build_dm_context(world_id, campaign_id, session_id=None):
    from models import get_world_by_id, get_campaign_by_id, get_players_in_campaign, get_session
    
    # 1) World details
    world = get_world_by_id(world_id)
    world_summary = f"World: {world['name']}\nDescription: {world['description']}"
    
    # 2) Campaign details
    campaign = get_campaign_by_id(campaign_id)
    campaign_summary = f"Campaign: {campaign['title']}\nDescription: {campaign['description']}"
    
    # 3) Player information
    players = get_players_in_campaign(campaign_id)
    player_summaries = []
    for i, player in enumerate(players, start=1):
        # Build a descriptive line for each player
        char_name = player['character_name'] or f"Unnamed-Char-{player['player_id']}"
        race = player['race'] or "Unknown Race"
        char_class = player['class'] or "Unknown Class"
        level = player['level'] or 1
        
        line = (f"Player #{i} [ID: {player['player_id']}]: "
                f"{char_name}, a Level {level} {race} {char_class}")
        player_summaries.append(line)
    
    players_text = "Party Members:\n" + "\n".join(player_summaries)
    
    # 4) Recent events (session log)
    recent_events = ""
    if session_id:
        session = get_session(session_id)
        if session and session['session_log']:
            recent_events = f"\nRecent Events:\n{session['session_log']}"
    
    # 5) Combine everything
    context = (
        f"{world_summary}\n\n{campaign_summary}\n\n{players_text}"
        f"{recent_events}"
    )
    return context
