"""
server.py

Flask + SocketIO server for the AI Dungeon Master application.
Exposes REST endpoints and WebSocket events for creating and
managing worlds, campaigns, players, and interactive sessions.
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room

# Import application logic from local modules
from ai_dm.models import (
    create_world, get_world_by_id,
    create_campaign, get_campaign_by_id,
    create_player, get_players_in_campaign,
    get_sessions_by_campaign, get_player_by_id
)
from ai_dm.session_logic import (
    start_session, record_interaction, end_session, get_session_recap
)
from ai_dm.llm import query_gpt, build_dm_context
from ai_dm.db import init_db

# Create Flask application and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize the database/tables
init_db()

#
# -- RESTful Endpoints --
#

@app.route('/worlds', methods=['POST'])
def create_new_world():
    """
    Create a new world by providing 'name' and 'description' in JSON.
    Returns the new world's ID.
    """
    data = request.json
    world_id = create_world(data['name'], data['description'])
    return jsonify({"world_id": world_id}), 201

@app.route('/worlds/<int:world_id>', methods=['GET'])
def get_world(world_id):
    """
    Retrieve details of a specific world by its ID.
    """
    world = get_world_by_id(world_id)
    if not world:
        return jsonify({"error": "World not found"}), 404
    return jsonify(world)

@app.route('/campaigns', methods=['POST'])
def create_new_campaign():
    """
    Create a new campaign by providing 'title', 'world_id', and an optional 'description'.
    Returns the new campaign's ID.
    """
    data = request.json
    campaign_id = create_campaign(
        data['title'],
        data['world_id'],
        data.get('description', '')
    )
    return jsonify({"campaign_id": campaign_id}), 201

@app.route('/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """
    Retrieve details of a specific campaign by its ID.
    """
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    return jsonify(campaign)

@app.route('/campaigns/<int:campaign_id>/players', methods=['POST'])
def add_player(campaign_id):
    """
    Add a new player to a campaign. Requires 'name', 'character_name',
    and optionally 'race', 'char_class', 'level'.
    Returns the new player's ID.
    """
    data = request.json
    player_id = create_player(
        campaign_id,
        data['name'],
        data['character_name'],
        data.get('race'),
        data.get('char_class'),
        data.get('level', 1)
    )
    return jsonify({"player_id": player_id}), 201

@app.route('/campaigns/<int:campaign_id>/players', methods=['GET'])
def get_players(campaign_id):
    """
    List all players in a campaign.
    """
    players = get_players_in_campaign(campaign_id)
    return jsonify(players)

@app.route('/sessions/start', methods=['POST'])
def start_new_session():
    """
    Start a new session for a given campaign.
    Expects 'campaign_id' in JSON. Returns the new session's ID.
    """
    data = request.json
    campaign_id = data['campaign_id']
    session_id = start_session(campaign_id)
    return jsonify({"session_id": session_id}), 201

@app.route('/sessions/<int:session_id>/interact', methods=['POST'])
def handle_interaction(session_id):
    """
    Handle an interaction from a player during a session.
    Expects JSON with 'user_input', 'campaign_id', 'world_id',
    and optionally 'player_id'. Queries the AI for a DM response,
    logs it, and broadcasts via SocketIO.
    """
    data = request.json
    user_input = data['user_input']
    campaign_id = data['campaign_id']
    world_id = data['world_id']
    player_id = data.get('player_id')

    # Determine the player's label (e.g., character name)
    player_label = "Player"
    if player_id:
        player = get_player_by_id(player_id)
        if player and player['character_name']:
            player_label = player['character_name']
        else:
            player_label = f"Player {player_id}"

    # Build DM context (world/campaign/player info)
    context = build_dm_context(world_id, campaign_id, session_id)

    # Provide a system message to the AI for more context
    system_message = (
        "You are an experienced Dungeons & Dragons Dungeon Master...\n"
        f"Currently, {player_label} is speaking.\n\n"
        + context
    )

    # Get the DM's response from the AI
    ai_response = query_gpt(user_input, system_message)

    # Record this interaction in the DB
    record_interaction(session_id, user_input, ai_response, player_id=player_id)

    # Broadcast the message to all WebSocket clients in this session's room
    combined_msg = f"{player_label}: {user_input}\nDM: {ai_response}"
    socketio.emit('new_message', {'message': combined_msg}, room=str(session_id))

    # Return a formatted response for the REST caller
    formatted_response = ai_response.replace('\n', '<br>')
    return jsonify({"dm_response": formatted_response})

@app.route('/sessions/<int:session_id>/end', methods=['POST'])
def end_game_session(session_id):
    """
    End a running session and get a text recap.
    """
    recap = end_session(session_id)
    return jsonify({"recap": recap})

@app.route('/sessions/<int:session_id>/recap', methods=['GET'])
def get_session_summary(session_id):
    """
    Retrieve the recap for a completed session, if available.
    """
    recap = get_session_recap(session_id)
    if not recap:
        return jsonify({"error": "Recap not available"}), 404
    return jsonify({"recap": recap})

@app.route('/campaigns/<int:campaign_id>/sessions', methods=['GET'])
def list_campaign_sessions(campaign_id):
    """
    List all sessions associated with a specific campaign.
    """
    sessions = get_sessions_by_campaign(campaign_id)
    return jsonify(sessions)

#
# -- SocketIO Events --
#

@socketio.on('join_session')
def handle_join_session(data):
    """
    Event for a client to join a specific session "room" and
    start receiving broadcasted messages for that session.
    """
    session_id = data.get('session_id')
    if not session_id:
        return
    join_room(str(session_id))
    emit('new_message', {
        'message': f"A new player joined session {session_id}!"
    }, room=str(session_id))

@socketio.on('send_message')
def handle_send_message(data):
    """
    Event for a client to send a message to the DM in real-time
    through SocketIO. Expects a dict with 'session_id', 'campaign_id',
    'world_id', 'player_id', and the actual 'message'.
    """
    session_id = data.get('session_id')
    user_input = data.get('message', '')
    campaign_id = data.get('campaign_id')
    world_id = data.get('world_id')
    player_id = data.get('player_id')

    if not session_id or not campaign_id or not world_id:
        return  # Cannot proceed without these essential pieces

    # Get player data to identify them by character name or fallback label
    player_data = get_player_by_id(player_id) if player_id else None
    player_label = "Unknown Player"
    if player_data and player_data['character_name']:
        player_label = player_data['character_name']

    # Build the DM context
    context = build_dm_context(world_id, campaign_id, session_id)
    system_message = (
        "You are an experienced Dungeons & Dragons Dungeon Master.\n"
        "There are multiple players with distinct characters.\n"
        f"Currently, {player_label} is speaking.\n\n"
        "Use these details to keep track of different characters:\n\n"
        f"{context}\n\n"
        "Do not confuse one character with another."
    )

    # Generate AI response
    ai_response = query_gpt(user_input, system_message)

    # Record the interaction in DB
    record_interaction(session_id, user_input, ai_response, player_id=player_id)

    # Broadcast to all clients in the session room
    combined_msg = f"{player_label}: {user_input}\nDM: {ai_response}"
    emit('new_message', {'message': combined_msg}, room=str(session_id))

#
# -- Start server with SocketIO --
#

if __name__ == '__main__':
    # Run the app with SocketIO
    # Turn off debug=True in production
    socketio.run(app, debug=True)
