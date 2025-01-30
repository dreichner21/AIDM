# aidm_server/llm.py

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
from sqlalchemy import desc

from aidm_server.database import db, graph_db, get_graph_db
from aidm_server.models import (
    World, Campaign, Player, Session, PlayerAction,
    Map, SessionLogEntry, CampaignSegment
)

from aidm_server.context_engine import ContextEngine
from aidm_server.response_controller import DMResponseController

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
    """
    return True, None

def query_dm_function(user_input: str, session_id: int, speaking_player_id=None):
    """
    Non-streaming DM logic (returns the entire response at once).
    1. Builds context from ContextEngine
    2. Sends prompt to LLM
    3. Parses the final text with DMResponseController
    4. Returns a structured dict
    """
    # 1. Build context using ContextEngine
    context_engine = ContextEngine(session_id)
    context_str = context_engine.build_context()

    # NEW: Insert momentum-based style instructions
    gdb = get_graph_db()
    momentum_text = ""
    if gdb:
        momentum_val = gdb.calculate_session_momentum(session_id)
        if momentum_val > 7.5:
            momentum_text = "\nSTYLE: High-intensity dramatic narration."
        elif momentum_val < 3:
            momentum_text = "\nSTYLE: Slow-building atmospheric description."

    system_instructions = """
You are a Dungeons & Dragons Dungeon Master.
- Provide immersive, story-driven narrative.
- If a player's action logically requires a dice roll, instruct them to roll.
- Refer to triggered segments, player history, and the current location as needed.
"""
    full_prompt = f"{system_instructions}{momentum_text}\nCONTEXT:\n{context_str}\n\nPLAYER ACTION:\n{user_input}\n"

    # 2. Generate the LLM response
    response = model.generate_content(full_prompt)
    raw_text = response.text.strip()

    # 3. Parse with DMResponseController
    controller = DMResponseController()
    structured_response = controller.structure_response(raw_text)

    return structured_response

def query_dm_function_stream(user_input: str, session_id: int, speaking_player=None):
    """
    Streaming version of the DM logic.
    1. Build context from ContextEngine
    2. Stream tokens from LLM
    3. Accumulate raw LLM text
    4. Parse the final text with DMResponseController
    5. Return the structured dict
    """
    # 1. Build context
    context_engine = ContextEngine(session_id)
    context_str = context_engine.build_context()

    # NEW: Insert momentum-based style instructions
    gdb = get_graph_db()
    style_line = ""
    if gdb:
        momentum_val = gdb.calculate_session_momentum(session_id)
        if momentum_val > 7.5:
            style_line = "\nSTYLE: High-intensity dramatic narration."
        elif momentum_val < 3:
            style_line = "\nSTYLE: Slow-building atmospheric description."

    system_instructions = f"""
You are a Dungeons & Dragons DM. Provide descriptive, story-focused responses.
If an action warrants a dice roll, explicitly request it from the player.{style_line}
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
        f"CONTEXT:\n{context_str}\n\n"
        f"PLAYER INPUT:\n{user_input}\n"
    )

    raw_text_accumulator = ""

    # 2. Stream from the LLM
    try:
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                raw_text_accumulator += chunk.text
                yield chunk.text  # stream partial text as it arrives
    except Exception as e:
        yield f"Error during streaming: {str(e)}"

    # 3. After the stream is complete, parse the final text
    controller = DMResponseController()
    structured_response = controller.structure_response(raw_text_accumulator)

    # 4. Return the final structured dict
    yield f"<END_OF_STREAM:{json.dumps(structured_response)}>"


def query_gpt(prompt, system_message=None):
    """
    Simple helper for quick queries (e.g. end-of-session summary).
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
