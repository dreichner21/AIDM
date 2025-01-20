from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from models import (
    create_world, get_world_by_id,
    create_campaign, get_campaign_by_id,
    create_player, get_players_in_campaign,
    get_sessions_by_campaign, get_player_by_id
)
from session_logic import start_session, record_interaction, end_session, get_session_recap
from llm import query_gpt, build_dm_context
from db import init_db, get_connection

app = Flask(__name__)

# --- SOCKETIO SETUP ---
socketio = SocketIO(app, cors_allowed_origins="*")
# --- END SOCKETIO SETUP ---

# Initialize database
init_db()

#
# -- REST ENDPOINTS --
#

@app.route('/worlds', methods=['POST'])
def create_new_world():
    data = request.json
    world_id = create_world(data['name'], data['description'])
    return jsonify({"world_id": world_id}), 201

@app.route('/worlds/<int:world_id>', methods=['GET'])
def get_world(world_id):
    world = get_world_by_id(world_id)
    if not world:
        return jsonify({"error": "World not found"}), 404
    return jsonify(world)

@app.route('/campaigns', methods=['POST'])
def create_new_campaign():
    data = request.json
    campaign_id = create_campaign(
        data['title'],
        data['world_id'],
        data.get('description', '')
    )
    return jsonify({"campaign_id": campaign_id}), 201

@app.route('/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    return jsonify(campaign)

@app.route('/campaigns/<int:campaign_id>/players', methods=['POST'])
def add_player(campaign_id):
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
    players = get_players_in_campaign(campaign_id)
    return jsonify(players)

@app.route('/sessions/start', methods=['POST'])
def start_new_session():
    data = request.json
    campaign_id = data['campaign_id']
    session_id = start_session(campaign_id)
    return jsonify({"session_id": session_id}), 201

@app.route('/sessions/<int:session_id>/interact', methods=['POST'])
def handle_interaction(session_id):
    data = request.json
    user_input = data['user_input']
    campaign_id = data['campaign_id']
    world_id = data['world_id']
    player_id = data.get('player_id')

    # Determine the player's label
    player_label = "Player"
    if player_id:
        p = get_player_by_id(player_id)
        if p and p['character_name']:
            player_label = p['character_name']
        else:
            player_label = f"Player {player_id}"

    context = build_dm_context(world_id, campaign_id, session_id)
    system_message = (
        "You are an experienced Dungeons & Dragons Dungeon Master...\n"
        f"Currently, {player_label} is speaking.\n\n"
        + context
    )

    ai_response = query_gpt(user_input, system_message)
    record_interaction(session_id, user_input, ai_response, player_id=player_id)

    # Broadcast the correct label
    combined_msg = f"{player_label}: {user_input}\nDM: {ai_response}"
    socketio.emit('new_message', {'message': combined_msg}, room=str(session_id))

    formatted_response = ai_response.replace('\n', '<br>')
    return jsonify({"dm_response": formatted_response})


@app.route('/sessions/<int:session_id>/end', methods=['POST'])
def end_game_session(session_id):
    recap = end_session(session_id)
    return jsonify({"recap": recap})

@app.route('/sessions/<int:session_id>/recap', methods=['GET'])
def get_session_summary(session_id):
    recap = get_session_recap(session_id)
    if not recap:
        return jsonify({"error": "Recap not available"}), 404
    return jsonify({"recap": recap})

@app.route('/campaigns/<int:campaign_id>/sessions', methods=['GET'])
def list_campaign_sessions(campaign_id):
    sessions = get_sessions_by_campaign(campaign_id)
    return jsonify(sessions)


#
# -- SOCKETIO EVENTS --
#

@socketio.on('join_session')
def handle_join_session(data):
    """
    Lets the user join a "room" named after session_id
    so they can receive broadcasted messages for that session.
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
    session_id = data.get('session_id')
    user_input = data.get('message', '')
    campaign_id = data.get('campaign_id')
    world_id = data.get('world_id')
    player_id = data.get('player_id')  # e.g., 10, 11, etc.

    if not session_id or not campaign_id or not world_id:
        return  # We need these to proceed

    # Determine the player's label
    player_data = get_player_by_id(player_id) if player_id else None
    player_label = "Unknown Player"
    if player_data and player_data['character_name']:
        player_label = player_data['character_name']

    # Build the DM context with a hint about who is speaking
    context = build_dm_context(world_id, campaign_id, session_id)
    system_message = (
        "You are an experienced Dungeons & Dragons Dungeon Master. "
        "There are multiple distinct players with separate characters. "
        f"Right now, {player_label} is speaking.\n\n"
        f"Use these details to keep track of different characters:\n\n{context}\n\n"
        "Remember, do not confuse one character with another."
    )

    # Call the AI to get the DM response
    ai_response = query_gpt(user_input, system_message)

    # Record in DB with the correct player label
    record_interaction(session_id, user_input, ai_response, player_id=player_id)

    # Broadcast to all sockets in the session with the label
    combined_msg = f"{player_label}: {user_input}\nDM: {ai_response}"
    emit('new_message', {'message': combined_msg}, room=str(session_id))


#
# -- START APP WITH SOCKETIO --
#

if __name__ == '__main__':
    socketio.run(app, debug=True)
