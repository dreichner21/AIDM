from flask import Flask, request, jsonify
from models import (
    create_world, get_world_by_id,
    create_campaign, get_campaign_by_id,
    create_player, get_players_in_campaign,
    get_sessions_by_campaign
)
from session_logic import start_session, record_interaction, end_session, get_session_recap
from llm import query_gpt, build_dm_context
from db import init_db

app = Flask(__name__)

# Initialize database
init_db()

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
    # No need to do data['campaign_id']—we already have campaign_id from the URL
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
    
    # OPTIONAL: Grab an optional "player_id" or "player_name" from the payload
    player_id = data.get('player_id')  # might be None if not supplied
    
    # Build context for the AI
    context = build_dm_context(world_id, campaign_id, session_id)
    system_message = (
        "You are an experienced Dungeons & Dragons Dungeon Master running a tabletop RPG session..."
        + context
    )
    
    # Get AI response
    ai_response = query_gpt(user_input, system_message)
    
    # Record the interaction (now passing in player_id)
    record_interaction(session_id, user_input, ai_response, player_id=player_id)
    
    # Format the response
    formatted_response = ai_response.replace('\n', '<br>')
    return jsonify({"dm_response": formatted_response})

    # Build context and get AI response
    context = build_dm_context(world_id, campaign_id, session_id)
    system_message = (
        "You are an experienced Dungeons & Dragons Dungeon Master running a tabletop RPG session. Your responsibilities:\n"
        "1. Narrate the world, NPCs, and events vividly and consistently\n"
        "2. Manage game mechanics and rules fairly\n"
        "3. Respond to player actions with appropriate consequences\n"
        "4. Keep track of the party's progress and maintain narrative continuity\n"
        "5. Create engaging encounters and challenges\n\n"
        "Use this context to inform your responses:\n" + context
    )
    ai_response = query_gpt(user_input, system_message)

    # Record the interaction
    record_interaction(session_id, user_input, ai_response)

    # Format the response - replace raw newlines with HTML line breaks
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

if __name__ == '__main__':
    app.run(debug=True) 