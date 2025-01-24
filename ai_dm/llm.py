"""
llm.py

Module to handle all interactions with Google's Gemini 1.5 Pro model.
"""

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from ai_dm.models_orm import World, Campaign, Player, Session
from datetime import datetime
from sqlalchemy import desc
from ai_dm.models_orm import World, Campaign, Player, Session, PlayerAction

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_GENAI_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_GENAI_API_KEY environment variable is not set")
genai.configure(api_key=api_key)

# Use single model for all operations
model = genai.GenerativeModel("gemini-exp-1206")

# Enhanced DM function schema with roll requests
dm_function = {
    "name": "DMResponse",
    "description": "Return a JSON object containing the Dungeon Master's response to the players.",
    "parameters": {
        "type": "object",
        "properties": {
            "dm_message": {
                "type": "string",
                "description": "A single string that represents the DM's message"
            },
            "speaking_player": {
                "type": "object",
                "required": ["character_name", "player_id"],
                "properties": {
                    "character_name": {"type": "string"},
                    "player_id": {"type": "string"}
                },
                "description": "Information about which player character is speaking"
            },
            "roll_request": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["ability_check", "saving_throw", "attack_roll", "skill_check"]},
                    "ability": {"type": "string", "enum": ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]},
                    "skill": {"type": "string"},
                    "dc": {"type": "integer"},
                    "advantage": {"type": "boolean"},
                    "disadvantage": {"type": "boolean"}
                },
                "description": "Details about any dice roll required from the player"
            },
            "referenced_players": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "character_name": {"type": "string"},
                        "player_id": {"type": "string"}
                    }
                },
                "description": "List of players referenced in the DM's response"
            }
        },
        "required": ["dm_message", "speaking_player"]
    }
}

def validate_dm_response(response_json, active_players):
    """Validates the DM's response JSON against active players."""
    if not isinstance(active_players, dict):
        return False, "Invalid active players format"

    # Validate speaking player
    speaking_player = response_json.get("speaking_player")
    if not speaking_player or not isinstance(speaking_player, dict):
        return False, "Missing or invalid speaking player"

    player_id = str(speaking_player.get("player_id"))
    if player_id not in active_players:
        return False, f"Unknown player ID: {player_id}"

    # Validate referenced players
    if "referenced_players" in response_json:
        for player in response_json["referenced_players"]:
            ref_id = str(player.get("player_id"))
            if ref_id not in active_players:
                return False, f"Referenced unknown player ID: {ref_id}"
            
            # Verify character name matches
            if player.get("character_name") != active_players[ref_id]["character_name"]:
                return False, "Character name mismatch"

    # Validate roll request if present
    if "roll_request" in response_json:
        roll_request = response_json["roll_request"]
        if not isinstance(roll_request, dict):
            return False, "Invalid roll request format"
            
        required_roll_fields = ["type"]
        if not all(field in roll_request for field in required_roll_fields):
            return False, "Missing required roll request fields"
            
        valid_roll_types = ["ability_check", "saving_throw", "attack_roll", "skill_check"]
        if roll_request["type"] not in valid_roll_types:
            return False, "Invalid roll type"

    return True, None

def determine_roll_type(action_text):
    """Simplified helper function that no longer enforces scripted roll responses"""
    return None  # Let the LLM handle roll detection naturally

def query_dm_function(user_input, context, speaking_player_id=None, roll_result=None):
    """Enhanced function calling version for DM responses with roll context"""
    system_instructions = """
    You are a Dungeons & Dragons Dungeon Master.
    
    CRITICAL RULES:
    1. If a roll result is provided, use it to determine the outcome of the previous action
    2. You must request rolls when appropriate for actions that require them
    3. Be consistent with action resolutions based on roll results
    4. For rolls of 20, describe critical success
    5. For rolls of 1, describe critical failure
    """

    if roll_result:
        system_instructions += f"\nA roll was made with result: {roll_result}. Resolve the previous action accordingly."

    # First, check for combat/action that needs a roll
    suggested_roll = determine_roll_type(user_input)
    if suggested_roll:
        return json.dumps({
            "dm_message": "This action requires a roll.",
            "roll_request": suggested_roll,
            "requires_roll": True
        })

    system_instructions += """
    You are a Dungeons & Dragons Dungeon Master. You MUST NEVER resolve actions that require rolls!
    
    CRITICAL RULES:
    1. If a player attempts ANY combat action, STOP and request a roll
    2. If a player tries to hit, attack, or harm something, STOP and request a roll
    3. DO NOT narrate the outcome of attacks or combat actions
    4. For combat, respond ONLY with "This action requires a roll" and wait for the roll
    
    For non-combat actions, proceed with normal narration.
    """

    # Add explicit player identification to system instructions
    system_instructions += f"""
    IMPORTANT - PLAYER IDENTIFICATION:
    - Current speaking player ID: {speaking_player_id}
    - You must ALWAYS reference this exact player ID in your response
    - Never invent actions for other players
    - If you're unsure about player identity, respond with an error
    """

    # Determine if the action needs a roll
    suggested_roll = determine_roll_type(user_input)
    if suggested_roll:
        system_instructions += f"\nSUGGESTED ROLL:\n{json.dumps(suggested_roll, indent=2)}"

    # Add stringent check for roll requirements
    if not determine_roll_type(user_input):
        # Force a generic ability check if no specific roll type is detected
        suggested_roll = {
            "type": "ability_check",
            "ability": "dexterity",
            "dc": 12,
            "advantage": False,
            "disadvantage": False
        }
        system_instructions += f"\nFORCED ROLL REQUEST:\n{json.dumps(suggested_roll, indent=2)}"

    # Get player info for context
    player_info = {}
    if speaking_player_id:
        player = Player.query.get(speaking_player_id)
        if player:
            player_info = {
                "character_name": player.character_name,
                "player_id": str(speaking_player_id)
            }

    full_prompt = (
        f"{system_instructions}\n"
        f"SPEAKING PLAYER:\n{json.dumps(player_info, indent=2)}\n"
        f"CONTEXT:\n{context}\n"
        f"PLAYER ACTION:\n{user_input}\n\n"
        "Respond with properly formatted JSON only:"
    )

    try:
        response = model.generate_content(full_prompt)
        response_text = response.text.strip()
        
        # Remove any markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
            
        # Parse JSON response
        try:
            response_json = json.loads(response_text)
            
            # Check for roll request first
            if "roll_request" in response_json:
                return json.dumps({
                    "dm_message": "Before proceeding with that action, a roll is required.",
                    "roll_request": response_json["roll_request"]
                })
            
            # Force correct player ID and name
            if speaking_player_id and response_json.get("speaking_player"):
                response_json["speaking_player"]["player_id"] = str(speaking_player_id)
                # Override character name if we have player info
                player = Player.query.get(speaking_player_id)
                if player:
                    response_json["speaking_player"]["character_name"] = player.character_name
            
            # Get active players from context
            context_lines = context.split('\n')
            active_players_json = ''
            for i, line in enumerate(context_lines):
                if line.startswith('ACTIVE PLAYERS:'):
                    active_players_json = context_lines[i+1]
                    break
            active_players = json.loads(active_players_json)
            
            # Validate response
            is_valid, error_msg = validate_dm_response(response_json, active_players)
            if not is_valid:
                return f"Error: {error_msg}"
                
            # Ensure dm_message is present
            if "dm_message" not in response_json:
                return "Error: Invalid response format"
                
            # Clean up the message
            dm_message = response_json["dm_message"].strip()
            dm_message = dm_message.replace("DM:", "").replace("DM: DM:", "")
            
            # Update response with cleaned message
            response_json["dm_message"] = dm_message
            
            # Add player info if available
            if player_info:
                response_json["speaking_player"] = player_info
                
            return response_json["dm_message"]
            
        except json.JSONDecodeError:
            print("Failed to parse JSON response:", response_text)
            # If roll is needed based on action, return that instead of error
            suggested_roll = determine_roll_type(user_input)
            if suggested_roll:
                return json.dumps({
                    "dm_message": "A roll is required for this action.",
                    "roll_request": suggested_roll
                })
            return "Error: Invalid JSON response from DM"
            
    except Exception as e:
        print(f"Error during model generation: {e}")
        return "I apologize, but I encountered an error processing your request."

def query_dm_function_stream(user_input, context, speaking_player=None, roll_result=None):
    """Streaming version with roll context"""
    # Remove the forced roll check here
    if roll_result:
        # ...existing roll result handling...
        pass

    system_instructions = """
    You are a Dungeons & Dragons Dungeon Master. Your response will be streamed,
    so respond naturally with narrative text only (no JSON formatting needed).
    
    Rules:
    1. NEVER speak as a player character
    2. ONLY describe NPC actions, environment, and consequences
    3. Use third person for player actions
    4. Write in present tense
    5. No prefixes like 'DM:' in responses
    6. Maintain consistency with the current quest and location
    7. Reference active NPCs naturally in responses
    8. Develop open plot points through player interactions
    9. Track party location and update as players move
    10. Ensure all major actions advance the story
    11. For any combat or skill-based actions, you must stop and request a roll first.
    12. If a roll result is provided, use it to narrate the outcome of the previous action.
    13. DO NOT narrate the roll itself in the outcome of the action.
    13. Be dramatic and descriptive with critical successes (20) and failures (1).
    """

    if roll_result:
        system_instructions += f"\nResolve the action using roll result: {roll_result}"
    

    # Add speaker context if available
    speaker_info_text = ""
    if speaking_player:
        speaker_info_text = f"\nCurrent speaker is {speaking_player['character_name']} (ID: {speaking_player['player_id']}). Only attribute actions to this character.\n"

    full_prompt = (
        f"{system_instructions}\n"
        f"{speaker_info_text}"
        f"CONTEXT:\n{context}\n\n"
        f"PLAYER INPUT:\n{user_input}\n\n"
        "REMEMBER: Respond naturally as the DM, no special formatting needed."
    )

    try:
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text.strip()
    except Exception as e:
        print(f"Error during streaming generation: {e}")
        yield "I apologize, but I encountered an error processing your request."

def query_gpt(prompt, system_message=None):
    """Non-streaming LLM call. Retained for backward compatibility."""
    full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
    response = model.generate_content(full_prompt)
    return response.text

def query_gpt_stream(prompt, system_message=None):
    """Streaming LLM call. Retained for backward compatibility."""
    full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
    response = model.generate_content(full_prompt, stream=True)
    for chunk in response:
        yield chunk.text

def build_dm_context(world_id, campaign_id, session_id=None):
    """Enhanced context builder with better player state tracking"""
    world = World.query.get(world_id)
    if not world:
        world_summary = "World: Unknown\nDescription: No data."
    else:
        world_summary = f"World: {world.name}\nDescription: {world.description}"

    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        campaign_summary = "Campaign: Unknown\nDescription: No data."
    else:
        campaign_summary = f"Campaign: {campaign.title}\nDescription: {campaign.description}"

    # Enhanced player tracking with more detailed state
    active_players = {}
    players = Player.query.filter_by(campaign_id=campaign_id).all()
    
    for player in players:
        # Get last 3 actions for this specific player
        recent_actions = PlayerAction.query.filter_by(
            player_id=player.player_id  # This ties actions to specific players
        ).order_by(desc(PlayerAction.timestamp)).limit(3).all()
        
        # Include player's recent actions in context
        action_history = [action.action_text for action in recent_actions]
        
        active_players[str(player.player_id)] = {
            "character_name": player.character_name,
            "race": player.race,
            "class": player.class_,
            "level": player.level,
            "recent_actions": action_history,  # Last 3 things this player did
            "last_seen": recent_actions[0].timestamp.isoformat() if recent_actions else None
        }

    # Format active players section
    active_players_text = "ACTIVE PLAYERS:\n" + json.dumps(active_players, indent=2)

    # Add character status lens
    character_status = "\nCHARACTER STATUS LENS:\n"
    for player_id, data in active_players.items():
        if data['recent_actions']:  # Only add if there are any actions
            most_recent = data['recent_actions'][0]
            character_status += f"- {data['character_name']}: {most_recent} (Last Action)\n"

    # Initialize recent_events before using it
    recent_events = ""
    if session_id:
        session_obj = Session.query.get(session_id)
        if session_obj and session_obj.session_log:
            recent_events = f"\nRECENT EVENTS:\n{session_obj.session_log}"

    context = (
        f"{world_summary}\n\n"
        f"{campaign_summary}\n\n"
        f"{active_players_text}\n"
        f"{character_status}"
        f"{recent_events}"
    )
    
    # Add campaign state
    campaign = Campaign.query.get(campaign_id)
    if campaign:
        try:
            npcs = json.loads(campaign.active_npcs) if campaign.active_npcs else []
            plot_points = json.loads(campaign.plot_points) if campaign.plot_points else []
        except json.JSONDecodeError:
            npcs = []
            plot_points = []
        
        context += f"\nCurrent Quest: {campaign.current_quest or 'None'}"
        context += f"\nLocation: {campaign.location or 'Unknown'}"
        
        if plot_points:
            context += "\nPlot Points:\n" + "\n".join([f"- {point}" for point in plot_points])
        
        if npcs:
            context += "\nActive NPCs:\n" + "\n" + "\n".join([f"- {npc}" for npc in npcs])

    return context
