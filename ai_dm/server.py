# ai_dm/server.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wtforms import validators  # Add this with your other imports
from wtforms.validators import DataRequired, Optional
from wtforms import SelectField
from flask_admin.form import Select2Field

"""
server.py

Flask + SocketIO server for the AI Dungeon Master application,
fully refactored to use function calling with Gemini 2.0 for DM responses.
"""

import json
from datetime import datetime
import logging
import traceback

# Import database first to avoid circular imports
from ai_dm.database import db, migrate, init_db

# Rest of imports
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_cors import CORS

from ai_dm.models_orm import World, Campaign, Player, Session, Npc, PlayerAction
from ai_dm.llm import query_dm_function, query_dm_function_stream, build_dm_context, determine_roll_type

# Create Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Initialize database with new configuration
init_db(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Try to import views, but don't fail if not found
try:
    from ai_dm.views import *
except ImportError:
    print("Views module not found - continuing without views")

# Create tables if they don't exist
with app.app_context():
    db.create_all()

############################################################################
# RESTful Endpoints
############################################################################

@app.route('/worlds', methods=['POST'])
def create_new_world():
    data = request.json
    new_world = World(
        name=data['name'],
        description=data['description']
    )
    db.session.add(new_world)
    db.session.commit()
    return jsonify({"world_id": new_world.world_id}), 201

@app.route('/worlds/<int:world_id>', methods=['GET'])
def get_world(world_id):
    world = db.session.get(World, world_id)
    if not world:
        return jsonify({"error": "World not found"}), 404

    data = {
        "world_id": world.world_id,
        "name": world.name,
        "description": world.description,
        "created_at": world.created_at.isoformat() if world.created_at else None
    }
    return jsonify(data)

@app.route('/campaigns', methods=['POST'])
def create_new_campaign():
    data = request.json
    new_campaign = Campaign(
        title=data['title'],
        description=data.get('description', ''),
        world_id=data['world_id']
    )
    db.session.add(new_campaign)
    db.session.commit()
    return jsonify({"campaign_id": new_campaign.campaign_id}), 201

@app.route('/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    campaign = db.session.get(Campaign, campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    data = {
        "campaign_id": campaign.campaign_id,
        "title": campaign.title,
        "description": campaign.description,
        "world_id": campaign.world_id,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None
    }
    return jsonify(data)

@app.route('/campaigns', methods=['GET'])
def list_campaigns():
    campaigns = Campaign.query.all()
    results = []
    for c in campaigns:
        results.append({
            "campaign_id": c.campaign_id,
            "title": c.title,
            "description": c.description,
            "world_id": c.world_id,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    return jsonify(results)

@app.route('/campaigns/<int:campaign_id>/players', methods=['POST'])
def add_player(campaign_id):
    data = request.json
    
    # Validate campaign exists
    campaign = db.session.get(Campaign, campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    try:
        new_player = Player(
            campaign_id=campaign_id,  # This is now guaranteed to exist
            name=data['name'],
            character_name=data['character_name'],
            race=data.get('race', ''),  # Provide defaults for optional fields
            class_=data.get('char_class', ''),
            level=data.get('level', 1),
            stats=data.get('stats', ''),
            inventory=data.get('inventory', ''),
            character_sheet=data.get('character_sheet', '')
        )
        db.session.add(new_player)
        db.session.commit()
        return jsonify({
            "player_id": new_player.player_id,
            "message": "Player successfully created"
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error("Failed to create player: %s", traceback.format_exc())
        return jsonify({
            "error": "Failed to create player"
        }), 400

@app.route('/campaigns/<int:campaign_id>/players', methods=['GET'])
def get_players(campaign_id):
    players = Player.query.filter_by(campaign_id=campaign_id).all()
    results = []
    for p in players:
        results.append({
            "player_id": p.player_id,
            "campaign_id": p.campaign_id,
            "name": p.name,
            "character_name": p.character_name,
            "race": p.race,
            "class_": p.class_,
            "level": p.level,
            "stats": p.stats,
            "inventory": p.inventory,
            "character_sheet": p.character_sheet,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })
    return jsonify(results)

@app.route('/sessions/start', methods=['POST'])
def start_new_session():
    data = request.json
    campaign_id = data['campaign_id']
    new_session = Session(campaign_id=campaign_id)
    db.session.add(new_session)
    db.session.commit()
    return jsonify({"session_id": new_session.session_id}), 201

@app.route('/sessions/<int:session_id>/interact', methods=['POST'])
def handle_interaction(session_id):
    """
    REST endpoint that uses function calling for DM responses.
    """
    data = request.json
    # Check for required fields
    required_fields = ['user_input', 'campaign_id', 'world_id', 'player_id']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required data, including player_id"}), 400
        
    user_input = data['user_input']
    campaign_id = data['campaign_id']
    world_id = data['world_id']
    player_id = data['player_id']  # Now guaranteed to be present
    roll_result = data.get('roll_result')  # New: Get roll result if provided

    # Get player info - no longer optional
    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({"error": "Invalid player_id"}), 404
    player_label = player.character_name

    context = build_dm_context(world_id, campaign_id, session_id)

    session_obj = db.session.get(Session, session_id)
    if not session_obj:
        return jsonify({"error": "Session not found"}), 404

    # Handle roll results if provided
    if roll_result:
        state = json.loads(session_obj.state_snapshot or '{}')
        pending_roll = state.get('pending_roll', {})
        original_action = pending_roll.get('original_action')
        
        if original_action:
            # Include original action and roll result in context
            context = build_dm_context(world_id, campaign_id, session_id)
            context += f"\nPrevious attempt: {original_action}\nRoll result: {roll_result}"
            
            # Clear pending roll
            state['pending_roll'] = {}
            session_obj.state_snapshot = json.dumps(state)
            db.session.commit()
            
            # Get DM's response with roll context
            dm_response = query_dm_function(original_action, context, speaking_player_id=player_id, roll_result=roll_result)
            return jsonify({"dm_response": dm_response})

    # Remove the manual roll check here and let the LLM handle it
    dm_response = query_dm_function(user_input, context, speaking_player_id=player_id)
    
    # Check if response contains a roll request
    try:
        response_data = json.loads(dm_response)
        if "roll_request" in response_data:
            return jsonify({
                "dm_response": response_data["dm_message"],
                "roll_request": response_data["roll_request"],
                "requires_roll": True
            })
    except json.JSONDecodeError:
        pass  # Continue with normal response handling if not JSON

    # Validate response doesn't contain common errors
    if dm_response.startswith("DM:") or "DM: DM:" in dm_response:
        dm_response = dm_response.replace("DM:", "").replace("DM: DM:", "").strip()

    # Update session log
    new_interaction = f"\n{player_label}: {user_input}\nDM: {dm_response}\n"
    session_obj.session_log = (session_obj.session_log or "") + new_interaction
    db.session.commit()

    return jsonify({
        "dm_response": dm_response,
        "session_log": session_obj.session_log  # Add session log to response
    })

@app.route('/sessions/<int:session_id>/end', methods=['POST'])
def end_game_session(session_id):
    session_obj = db.session.get(Session, session_id)
    if not session_obj:
        return jsonify({"error": "Session not found"}), 404

    full_log = session_obj.session_log if session_obj.session_log else ""
    recap_prompt = (
        "Please provide a concise summary of this D&D session, highlighting key events, "
        "important decisions, and any significant character developments:\n\n" + full_log
    )
    # Using existing query_gpt for recap as it's a summarization task
    recap = query_gpt(
        prompt=recap_prompt,
        system_message="You are a D&D session summarizer. Provide a clear, engaging recap."
    )

    state_snapshot = {
        "recap": recap,
        "ended_at": datetime.utcnow().isoformat()
    }
    session_obj.state_snapshot = json.dumps(state_snapshot)
    db.session.commit()

    return jsonify({"recap": recap})

@app.route('/sessions/<int:session_id>/recap', methods=['GET'])
def get_session_summary(session_id):
    session_obj = db.session.get(Session, session_id)
    if not session_obj:
        return jsonify({"error": "Session not found"}), 404

    if not session_obj.state_snapshot:
        return jsonify({"error": "Recap not available"}), 404

    snapshot = json.loads(session_obj.state_snapshot)
    return jsonify({"recap": snapshot.get("recap")})

@app.route('/campaigns/<int:campaign_id>/sessions', methods=['GET'])
def list_campaign_sessions(campaign_id):
    sessions = Session.query.filter_by(campaign_id=campaign_id).all()
    results = []
    for s in sessions:
        results.append({
            "session_id": s.session_id,
            "campaign_id": s.campaign_id,
            "created_at": s.created_at.isoformat() if s.created_at else None
        })
    return jsonify(results)

@app.route("/process_action", methods=["POST"])
def process_action():
    try:
        data = request.get_json()
        action_text = data.get("action")
        campaign_id = data.get("campaign_id")
        world_id = data.get("world_id")
        player_id = data.get("player_id")
        session_id = data.get("session_id")

        # Build context
        context = build_dm_context(world_id, campaign_id, session_id)
        
        # Get DM's response
        dm_response = query_dm_function(action_text, context, player_id)
        
        # Always check for rolls first
        suggested_roll = determine_roll_type(action_text)
        if suggested_roll:
            return jsonify({
                "success": True,
                "message": "Before continuing, please make a roll:",
                "roll_request": suggested_roll
            })
        
        # Process normal response
        try:
            response_json = json.loads(dm_response)
            if "roll_request" in response_json:
                return jsonify({
                    "success": True,
                    "message": response_json.get("dm_message", ""),
                    "roll_request": response_json["roll_request"]
                })
            
            # No roll needed, return normal response
            return jsonify({
                "success": True,
                "message": response_json.get("dm_message", "")
            })
            
        except json.JSONDecodeError:
            # If response isn't JSON, just return it as a message
            return jsonify({
                "success": True,
                "message": dm_response
            })

    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        return jsonify({
            "success": False,
            "message": "An internal error has occurred."
        }), 500

def handle_roll_request(response_json):
    """Process any roll requests from the DM's response"""
    if isinstance(response_json, str):
        try:
            response_json = json.loads(response_json)
        except json.JSONDecodeError:
            return None
    
    if "roll_request" in response_json:
        roll_info = response_json["roll_request"]
        return {
            "needs_roll": True,
            "roll_type": roll_info.get("type"),
            "ability": roll_info.get("ability"),
            "skill": roll_info.get("skill"),
            "dc": roll_info.get("dc", 10),
            "advantage": roll_info.get("advantage", False),
            "disadvantage": roll_info.get("disadvantage", False)
        }
    return None

@app.route('/campaigns/<int:campaign_id>/story', methods=['POST'])
def update_campaign_story(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    data = request.json
    
    if 'quest' in data:
        campaign.current_quest = data['quest']
    if 'location' in data:
        campaign.location = data['location']
    if 'plot_points' in data:
        campaign.plot_points = json.dumps(data['plot_points'])
    if 'active_npcs' in data:
        campaign.active_npcs = json.dumps(data['active_npcs'])
        
    db.session.commit()
    return jsonify({"success": True})

@app.route('/campaigns/<int:campaign_id>/events', methods=['POST'])
def add_story_event(campaign_id):
    data = request.json
    event = StoryEvent(
        campaign_id=campaign_id,
        description=data['description'],
        importance=data.get('importance', 5)
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({"event_id": event.event_id})

############################################################################
# SocketIO Events
############################################################################

@socketio.on('join_session')
def handle_join_session(data):
    session_id = data.get('session_id')
    if not session_id:
        emit('error', {'message': 'Session ID is required to join.'})
        return
    join_room(str(session_id))
    emit('new_message', {
        'message': f"A new player joined session {session_id}!"
    }, room=str(session_id))

@socketio.on('send_message')
def handle_send_message(data):
    """Enhanced real-time message handling with roll detection"""
    # Validate required fields
    required_fields = ['session_id', 'campaign_id', 'world_id', 'message', 'player_id']
    if not all(data.get(field) for field in required_fields):
        emit('error', {
            'message': 'Missing required data',
            'required_fields': required_fields
        })
        return

    session_id = data['session_id']
    player_id = data['player_id']
    roll_result = data.get('roll_result')
    
    # Get player info early - before any roll checks
    player = db.session.get(Player, player_id)
    if not player:
        emit('error', {'message': 'Invalid player ID'})
        return
        
    player_label = player.character_name  # Define player_label here, before roll checks
    
    if player.campaign_id != data['campaign_id']:
        emit('error', {'message': 'Player not part of this campaign'})
        return

    # Track player action with session_id
    new_action = PlayerAction(
        player_id=player_id,
        session_id=session_id,
        action_text=data['message'],
        timestamp=datetime.utcnow()
    )
    db.session.add(new_action)
    db.session.commit()

    session_obj = db.session.get(Session, session_id)
    if not session_obj:
        emit('error', {'message': 'Session not found'})
        return

    # Broadcast message to all clients in the session EXCEPT sender
    emit('new_message', {
        'message': data['message'],
        'speaker': player_label
    }, room=str(session_id), include_self=False)  # exclude sender

    if roll_result:
        state = json.loads(session_obj.state_snapshot or '{}')
        pending_roll = state.get('pending_roll', {})
        original_action = pending_roll.get('original_action')
        
        if original_action:
            context = build_dm_context(world_id, campaign_id, session_id)
            context += f"\nPrevious attempt: {original_action}\nRoll result: {roll_result}"
            
            # Clear pending roll
            state['pending_roll'] = {}
            session_obj.state_snapshot = json.dumps(state)
            db.session.commit()
            
            # Stream response with roll context
            emit('dm_response_start', {'session_id': session_id}, room=str(session_id))
            for chunk in query_dm_function_stream(original_action, context, speaking_player=speaking_player, roll_result=roll_result):
                if chunk:
                    emit('dm_chunk', {
                        'chunk': chunk,
                        'session_id': session_id
                    }, room=str(session_id))
                    socketio.sleep(0)
            emit('dm_response_end', {'session_id': session_id}, room=str(session_id))
            return

    # Remove the manual roll check here and let the LLM handle it
    
    # Rest of the existing function...
    user_input = data['message']
    campaign_id = data['campaign_id']
    world_id = data['world_id']

    # Get player info - no longer optional
    player = db.session.get(Player, player_id)
    if not player:
        emit('error', {'message': 'Invalid player_id'}, room=str(session_id))
        return

    player_label = player.character_name
    speaking_player = {
        "character_name": player.character_name,
        "player_id": str(player_id)
    }

    # Build context
    context = build_dm_context(world_id, campaign_id, session_id)

    # Signal start of DM response
    emit('dm_response_start', {'session_id': session_id}, room=str(session_id))

    # Stream DM response with speaker info
    full_response = []
    try:
        response_text = ""
        # First check if the action requires a roll
        if determine_roll_type(user_input):
            roll_message = "This action requires a roll before proceeding."
            # Log roll request
            new_interaction = f"\n{player_label}: {user_input}\nDM: {roll_message}\n"
            session_obj.session_log = (session_obj.session_log or "") + new_interaction
            db.session.commit()
            
            emit('roll_request', {
                'roll_info': suggested_roll,
                'message': roll_message,
                'requires_roll': True
            }, room=str(session_id))
            return

        # Stream DM response
        for chunk in query_dm_function_stream(user_input, context, speaking_player=speaking_player):
            if chunk:
                chunk = chunk.replace("DM:", "").replace("DM: DM:", "").strip()
                response_text += chunk
                emit('dm_chunk', {
                    'chunk': chunk,
                    'session_id': session_id
                }, room=str(session_id))
                socketio.sleep(0)

        # Update session log after complete response
        if response_text:
            new_interaction = f"\n{player_label}: {user_input}\nDM: {response_text}\n"
            session_obj.session_log = (session_obj.session_log or "") + new_interaction
            db.session.commit()

            # Emit updated session log
            emit('session_log_update', {
                'session_log': session_obj.session_log,
                'session_id': session_id
            }, room=str(session_id))

    except Exception as e:
        print(f"Error in stream response: {e}")
        emit('error', {
            'message': f'Error generating response: {str(e)}'
        }, room=str(session_id))
    finally:
        emit('dm_response_end', {'session_id': session_id}, room=str(session_id))

############################################################################
# Flask-Admin Setup
############################################################################

class PlayerModelView(ModelView):
    form_columns = ('campaign_id', 'name', 'character_name', 'race', 'class_', 'level', 'stats', 'inventory', 'character_sheet')
    column_list = ('campaign_id', 'name', 'character_name', 'race', 'class_', 'level')
    
    def create_form(self):
        form = super(PlayerModelView, self).create_form()
        
        form.race = Select2Field('Race', choices=[
            ('', 'Select Race'),
            ('Human', 'Human'),
            ('Elf', 'Elf'),
            ('Dwarf', 'Dwarf'),
            ('Halfling', 'Halfling'),
            ('Dragonborn', 'Dragonborn'),
            ('Tiefling', 'Tiefling'),
            ('Half-Elf', 'Half-Elf'),
            ('Half-Orc', 'Half-Orc'),
            ('Gnome', 'Gnome')
        ], validators=[DataRequired()])
        
        form.class_ = Select2Field('Class', choices=[
            ('', 'Select Class'),
            ('Fighter', 'Fighter'),
            ('Wizard', 'Wizard'),
            ('Cleric', 'Cleric'),
            ('Rogue', 'Rogue'),
            ('Ranger', 'Ranger'),
            ('Paladin', 'Paladin'),
            ('Barbarian', 'Barbarian'),
            ('Bard', 'Bard'),
            ('Druid', 'Druid'),
            ('Monk', 'Monk'),
            ('Sorcerer', 'Sorcerer'),
            ('Warlock', 'Warlock')
        ], validators=[DataRequired()])
        
        return form
    
    form_args = {
        'campaign_id': {
            'label': 'Campaign',
            'validators': [DataRequired()]
        },
        'name': {
            'label': 'Player Name',
            'validators': [DataRequired()]
        },
        'character_name': {
            'label': 'Character Name',
            'validators': [DataRequired()]
        },
        'level': {
            'default': 1,
            'validators': [Optional()]
        }
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            if not model.stats:
                model.stats = '{}'
            if not model.inventory:
                model.inventory = '[]'
            if not model.character_sheet:
                model.character_sheet = '{}'
            if not model.level:
                model.level = 1

class NpcModelView(ModelView):
    form_columns = ('world_id', 'name', 'role', 'backstory')
    column_list = ('world_id', 'name', 'role')
    
    def create_form(self):
        form = super(NpcModelView, self).create_form()
        form.role = Select2Field('Role', choices=[
            ('', 'Select Role'),
            ('Merchant', 'Merchant'),
            ('Guard', 'Guard'),
            ('Noble', 'Noble'),
            ('Innkeeper', 'Innkeeper'),
            ('Wizard', 'Wizard'),
            ('Priest', 'Priest'),
            ('Blacksmith', 'Blacksmith'),
            ('Farmer', 'Farmer'),
            ('Soldier', 'Soldier'),
            ('Other', 'Other')
        ], validators=[Optional()])
        return form
    
    form_args = {
        'world_id': {
            'label': 'World',
            'validators': [DataRequired()]
        },
        'name': {
            'label': 'NPC Name',
            'validators': [DataRequired()]
        },
        'backstory': {
            'label': 'Backstory',
            'validators': [Optional()]
        }
    }

    def on_model_change(self, form, model, is_created):
        if is_created and not model.backstory:
            model.backstory = ''

class CampaignModelView(ModelView):
    form_columns = ('title', 'description', 'world_id', 'current_quest', 'location', 'plot_points', 'active_npcs')
    column_list = ('title', 'world_id', 'current_quest', 'location')
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            if not model.plot_points:
                model.plot_points = '[]'
            if not model.active_npcs:
                model.active_npcs = '[]'
            if not model.current_quest:
                model.current_quest = ''
            if not model.location:
                model.location = ''

# Update admin views - replace the Campaign view with our new one
admin = Admin(app, name="AI-DM Admin", template_mode="bootstrap3")
admin.add_view(ModelView(World, db.session))
admin.add_view(CampaignModelView(Campaign, db.session))  # Changed this line
admin.add_view(PlayerModelView(Player, db.session))
admin.add_view(ModelView(Session, db.session))
admin.add_view(NpcModelView(Npc, db.session))  # Changed this line
admin.add_view(ModelView(PlayerAction, db.session))

############################################################################
# Main Entry Point
############################################################################

if __name__ == '__main__':
    socketio.run(app, debug=True)
