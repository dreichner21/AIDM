# socketio_events.py

import json
from datetime import datetime
from flask_socketio import join_room, emit
from aidm_server.database import db
from aidm_server.models import Player, Session, PlayerAction
from aidm_server.llm import query_dm_function, query_dm_function_stream, build_dm_context, determine_roll_type

def register_socketio_events(socketio):
    """
    Attach all Socket.IO event handlers to the given socketio instance.
    """

    @socketio.on('join_session')
    def handle_join_session(data):
        """
        Handle a client joining a session.

        Args:
            data (dict): The data containing the session ID.

        Emits:
            error: If the session ID is missing.
            new_message: When a new player joins the session.
        """
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
        """
        Handle a client sending a message.

        Args:
            data (dict): The data containing session, campaign, world, player IDs, and the message.

        Emits:
            error: If required data is missing or invalid.
            new_message: When a new message is sent by a player.
            dm_response_start: When the DM response starts.
            dm_chunk: When a chunk of the DM response is received.
            dm_response_end: When the DM response ends.
            roll_request: When a roll is required for an action.
            session_log_update: When the session log is updated.
        """
        required_fields = ['session_id', 'campaign_id', 'world_id', 'message', 'player_id']
        if not all(data.get(field) for field in required_fields):
            emit('error', {
                'message': 'Missing required data',
                'required_fields': required_fields
            })
            return

        session_id = data['session_id']
        campaign_id = data['campaign_id']
        world_id = data['world_id']
        player_id = data['player_id']
        roll_result = data.get('roll_result')

        player = db.session.get(Player, player_id)
        if not player:
            emit('error', {'message': 'Invalid player ID'})
            return

        player_label = player.character_name
        if player.campaign_id != campaign_id:
            emit('error', {'message': 'Player not part of this campaign'})
            return

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

        emit('new_message', {
            'message': data['message'],
            'speaker': player_label
        }, room=str(session_id), include_self=False)

        if roll_result:
            state = json.loads(session_obj.state_snapshot or '{}')
            pending_roll = state.get('pending_roll', {})
            original_action = pending_roll.get('original_action')
            
            if original_action:
                context = build_dm_context(world_id, campaign_id, session_id)
                context += f"\nPrevious attempt: {original_action}\nRoll result: {roll_result}"
                
                state['pending_roll'] = {}
                session_obj.state_snapshot = json.dumps(state)
                db.session.commit()
                
                emit('dm_response_start', {'session_id': session_id}, room=str(session_id))
                for chunk in query_dm_function_stream(original_action, context, speaking_player=player_label, roll_result=roll_result):
                    if chunk:
                        emit('dm_chunk', {
                            'chunk': chunk,
                            'session_id': session_id
                        }, room=str(session_id))
                emit('dm_response_end', {'session_id': session_id}, room=str(session_id))
                return

        user_input = data['message']
        speaking_player = {
            "character_name": player_label,
            "player_id": str(player_id)
        }
        context = build_dm_context(world_id, campaign_id, session_id)

        emit('dm_response_start', {'session_id': session_id}, room=str(session_id))

        response_text = ""
        # Basic roll detection
        suggested_roll = determine_roll_type(user_input)
        if suggested_roll:
            roll_message = "This action requires a roll before proceeding."
            new_interaction = f"\n{player_label}: {user_input}\nDM: {roll_message}\n"
            session_obj.session_log = (session_obj.session_log or "") + new_interaction
            db.session.commit()
            
            emit('roll_request', {
                'roll_info': suggested_roll,
                'message': roll_message,
                'requires_roll': True
            }, room=str(session_id))
            return

        try:
            for chunk in query_dm_function_stream(user_input, context, speaking_player=speaking_player):
                if chunk:
                    chunk = chunk.replace("DM:", "").replace("DM: DM:", "").strip()
                    response_text += chunk
                    emit('dm_chunk', {
                        'chunk': chunk,
                        'session_id': session_id
                    }, room=str(session_id))
        except Exception as e:
            emit('error', {
                'message': f'Error generating response: {str(e)}'
            }, room=str(session_id))
        finally:
            emit('dm_response_end', {'session_id': session_id}, room=str(session_id))

        if response_text:
            new_interaction = f"\n{player_label}: {user_input}\nDM: {response_text}\n"
            session_obj.session_log = (session_obj.session_log or "") + new_interaction
            db.session.commit()

            emit('session_log_update', {
                'session_log': session_obj.session_log,
                'session_id': session_id
            }, room=str(session_id))
