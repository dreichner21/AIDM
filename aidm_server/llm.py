# aidm_server/llm.py

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
from sqlalchemy import desc

from aidm_server.models import (
    World, Campaign, Player, Session, PlayerAction,
    Map, SessionLogEntry, CampaignSegment
)
from aidm_server.database import db, graph_db  # <--- Import the global graph_db here

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_GENAI_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_GENAI_API_KEY environment variable is not set")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-exp-1206")


def validate_dm_response(response_json, active_players):
    """
    (Optional) Validate structured JSON from the DM if needed.
    Currently not enforced, but you could check references to players, etc.
    """
    return True, None


def gather_segment_context(campaign_id):
    """
    Potentially gather data about segments/triggers.
    Currently a placeholder.
    """
    return {}


def build_dm_context(world_id, campaign_id, session_id=None):
    """
    Build a context string for the DM logic:
      - World info
      - Campaign info
      - Player data
      - Recent session events
      - Triggered segments
      - Additional graph relationships
    """
    # 1. World data
    world = World.query.get(world_id)
    if not world:
        world_summary = "World: Unknown\nDescription: No data."
    else:
        world_summary = f"World: {world.name}\nDescription: {world.description}"

    # 2. Campaign data
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        campaign_summary = "Campaign: Unknown\nDescription: No data."
    else:
        campaign_summary = f"Campaign: {campaign.title}\nDescription: {campaign.description}"

    # 3. Players
    active_players = {}
    players = Player.query.filter_by(campaign_id=campaign_id).all()
    for player in players:
        recent_actions = PlayerAction.query.filter_by(player_id=player.player_id)\
            .order_by(PlayerAction.timestamp.desc()).limit(3).all()
        action_history = [action.action_text for action in recent_actions]
        active_players[str(player.player_id)] = {
            "character_name": player.character_name,
            "race": player.race,
            "class": player.class_,
            "level": player.level,
            "recent_actions": action_history
        }
    active_players_text = "ACTIVE PLAYERS:\n" + json.dumps(active_players, indent=2)

    # 4. Recent session log
    recent_events = ""
    if session_id:
        entries = SessionLogEntry.query.filter_by(session_id=session_id)\
            .order_by(SessionLogEntry.timestamp.desc())\
            .limit(10).all()
        if entries:
            entries.reverse()
            recent_events = "\nRECENT EVENTS:\n" + "\n".join(e.message for e in entries)

    # 5. Triggered segments
    triggered_segments = CampaignSegment.query.filter_by(
        campaign_id=campaign_id,
        is_triggered=True
    ).all()
    segment_text = ""
    for seg in triggered_segments:
        segment_text += f"\n[SEGMENT] {seg.title}\n{seg.description}\n"

    # 6. Gather data from the graph (NPC relationships, etc.)
    #    For demonstration, let's assume we want to check relationships for all NPCs in this world.
    npc_relationship_text = ""
    npcs_in_world = []
    # We'll look up NPCs from the relational DB if we have them. 
    # (You could also store the entire NPC set purely in Neo4j.)
    from aidm_server.models import Npc
    if world:
        npcs_in_world = Npc.query.filter_by(world_id=world_id).all()

    for npc in npcs_in_world:
        rels = graph_db.get_npc_relationships(npc_id=npc.npc_id)
        # Format as text for the prompt
        npc_relationship_text += f"\nNPC {npc.name} (ID: {npc.npc_id}) relationships:\n"
        for r in rels:
            rel_type = r["relationship"]
            other_node = r["node"]
            npc_relationship_text += f"  - {rel_type} -> {other_node.get('name', 'Unknown')} (ID: {other_node.get('npc_id', '?')})\n"

    # 7. Combine everything into a single context string
    context = (
        f"{world_summary}\n\n"
        f"{campaign_summary}\n\n"
        f"{active_players_text}\n"
        f"{recent_events}\n"
    )
    if campaign:
        context += f"\nCurrent Quest: {campaign.current_quest or 'None'}"
        context += f"\nLocation: {campaign.location or 'Unknown'}"
        # Optionally include campaign.plot_points or active_npcs

    context += f"\n{segment_text}"
    context += f"\n--- GRAPH RELATIONSHIPS ---\n{npc_relationship_text}"

    return context


def query_dm_function(user_input, context, speaking_player_id=None):
    """
    Non-streaming DM logic: pass a prompt to the Generative AI model
    and return the text (or JSON).
    """
    system_instructions = """
You are a Dungeons & Dragons Dungeon Master.
- Provide immersive, story-driven narrative.
- If a player's action logically requires a dice roll, instruct them to roll.
- Refer to triggered segments, player history, and the current location as needed.
"""
    full_prompt = f"{system_instructions}\nCONTEXT:\n{context}\n\nPLAYER ACTION:\n{user_input}\n"
    response = model.generate_content(full_prompt)
    response_text = response.text.strip()

    # Attempt to parse JSON if it starts with { or [
    if response_text.startswith("{") or response_text.startswith("["):
        try:
            response_json = json.loads(response_text)
            return response_json
        except json.JSONDecodeError:
            pass

    return response_text


def query_dm_function_stream(user_input, context, speaking_player=None):
    """
    Streaming version of query_dm_function.
    Sends the LLM response in chunks to the socket client.
    """
    system_instructions = """
You are a Dungeons & Dragons DM. Provide descriptive, story-focused responses.
If an action warrants a dice roll, explicitly request it from the player.
"""
    speaker_text = ""
    if speaking_player:
        speaker_text = (
            f"\nCurrent speaker: {speaking_player['character_name']} "
            f"(ID: {speaking_player['player_id']})."
        )

    full_prompt = (
        f"{system_instructions}\n"
        f"{speaker_text}\n"
        f"CONTEXT:\n{context}\n\n"
        f"PLAYER INPUT:\n{user_input}\n"
    )

    try:
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text.strip()
    except Exception as e:
        yield f"Error during streaming: {str(e)}"


def query_gpt(prompt, system_message=None):
    """
    Simple wrapper for quick queries (used e.g. in /end session).
    """
    full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
    response = model.generate_content(full_prompt)
    return response.text


def query_gpt_stream(prompt, system_message=None):
    """
    Streaming version for quick GPT queries.
    """
    full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
    response = model.generate_content(full_prompt, stream=True)
    for chunk in response:
        yield chunk.text
