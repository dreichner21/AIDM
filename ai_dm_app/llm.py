import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini API
genai.configure(api_key="AIzaSyBvsMef-geqcJJDof6hZitpLWSUxhiR1Ds")
model = genai.GenerativeModel("gemini-1.5-flash")

def query_gpt(prompt, system_message=None, model_name="gemini-1.5-flash"):
    """
    Send a conversation to the Gemini API and return the assistant's response.
    Args:
        prompt (str): The user's input
        system_message (str, optional): Context/instructions for the AI
        model_name (str): The model to use (ignored as we're using gemini-1.5-flash)
    Returns:
        str: The AI's response
    """
    # Combine system message and prompt if provided
    full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
    
    # Generate response
    response = model.generate_content(full_prompt)
    return response.text

def build_dm_context(world_id, campaign_id, session_id=None):
    """
    Build context for the DM from the current game state.
    Args:
        world_id (int): ID of the current world
        campaign_id (int): ID of the current campaign
        session_id (int, optional): ID of the current session
    Returns:
        str: Formatted context string for the LLM
    """
    from models import get_world_by_id, get_campaign_by_id, get_players_in_campaign, get_session
    
    # Get world details
    world = get_world_by_id(world_id)
    world_summary = f"World: {world['name']}\nDescription: {world['description']}"
    
    # Get campaign details
    campaign = get_campaign_by_id(campaign_id)
    campaign_summary = f"Campaign: {campaign['title']}\nDescription: {campaign['description']}"
    
    # Get player information
    players = get_players_in_campaign(campaign_id)
    player_summaries = []
    for player in players:
        player_summary = (
            f"{player['character_name']} ({player['race']} {player['class']}, "
            f"Level {player['level']})"
        )
        player_summaries.append(player_summary)
    
    players_text = "Party Members:\n" + "\n".join(player_summaries)
    
    # Get recent events if session_id is provided
    recent_events = ""
    if session_id:
        session = get_session(session_id)
        if session and session['session_log']:
            recent_events = f"\nRecent Events:\n{session['session_log']}"
    
    # Combine all context
    context = f"{world_summary}\n\n{campaign_summary}\n\n{players_text}{recent_events}"
    
    return context 