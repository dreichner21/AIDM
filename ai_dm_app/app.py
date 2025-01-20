from flask import Flask, request, jsonify
from flask_cors import CORS
from models import (
    create_world, get_world_by_id,
    create_campaign, get_campaign_by_id,
    create_player, get_players_in_campaign,
    get_sessions_by_campaign
)
from session_logic import start_session, record_interaction, end_session, get_session_recap
from llm import query_gpt, build_dm_context
from db import init_db
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database
init_db()

# Get API key from environment variable or generate a new one
API_KEY = os.getenv('DND_API_KEY')
if not API_KEY:
    import secrets
    API_KEY = secrets.token_urlsafe(32)
    print(f"\nNo API key found in environment. Generated new API key: {API_KEY}")
    print("Add this to your .env file as DND_API_KEY=<key>")

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            return f(*args, **kwargs)
        return jsonify({"error": "Invalid or missing API key"}), 401
    return decorated_function

# Apply the decorator to all routes
@app.route('/worlds', methods=['POST'])
@require_api_key
def create_new_world():
    data = request.json
    world_id = create_world(data['name'], data['description'])
    return jsonify({"world_id": world_id}), 201

@app.route('/worlds/<int:world_id>', methods=['GET'])
@require_api_key
def get_world(world_id):
    world = get_world_by_id(world_id)
    if not world:
        return jsonify({"error": "World not found"}), 404
    return jsonify(world)

@app.route('/campaigns', methods=['POST'])
@require_api_key
def create_new_campaign():
    data = request.json
    campaign_id = create_campaign(
        data['title'],
        data['world_id'],
        data.get('description', '')
    )
    return jsonify({"campaign_id": campaign_id}), 201

@app.route('/campaigns/<int:campaign_id>', methods=['GET'])
@require_api_key
def get_campaign(campaign_id):
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    return jsonify(campaign)

@app.route('/campaigns/<int:campaign_id>/players', methods=['POST'])
@require_api_key
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
@require_api_key
def get_players(campaign_id):
    players = get_players_in_campaign(campaign_id)
    return jsonify(players)

@app.route('/sessions/start', methods=['POST'])
@require_api_key
def start_new_session():
    data = request.json
    campaign_id = data['campaign_id']
    session_id = start_session(campaign_id)
    return jsonify({"session_id": session_id}), 201

@app.route('/sessions/<int:session_id>/interact', methods=['POST'])
@require_api_key
def handle_interaction(session_id):
    data = request.json
    user_input = data['user_input']
    campaign_id = data['campaign_id']
    world_id = data['world_id']

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
@require_api_key
def end_game_session(session_id):
    recap = end_session(session_id)
    return jsonify({"recap": recap})

@app.route('/sessions/<int:session_id>/recap', methods=['GET'])
@require_api_key
def get_session_summary(session_id):
    recap = get_session_recap(session_id)
    if not recap:
        return jsonify({"error": "Recap not available"}), 404
    return jsonify({"recap": recap})

@app.route('/campaigns/<int:campaign_id>/sessions', methods=['GET'])
@require_api_key
def list_campaign_sessions(campaign_id):
    sessions = get_sessions_by_campaign(campaign_id)
    return jsonify(sessions)

if __name__ == '__main__':
    # Allow external connections
    app.run(host='0.0.0.0', port=5000, debug=True) 