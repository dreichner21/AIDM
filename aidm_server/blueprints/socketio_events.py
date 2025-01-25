# socketio_events.py

import json
from datetime import datetime
from flask_socketio import join_room, emit
from aidm_server.database import db
from aidm_server.models import Player, Session, PlayerAction, SessionLogEntry
from aidm_server.llm import (
    query_dm_function,
    query_dm_function_stream,
    build_dm_context,
    determine_roll_type
)

def register_socketio_events(socketio):
    """
    Attach all Socket.IO event handlers to the given socketio instance.
    """

    @socketio.on('join_session')
    def handle_join_session(data):
        """
        Handle a client joining a session.
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
        Handle a client sending a message, stream DM responses, and store one final log entry.
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

        # Emit the player's message to others in the room
        emit('new_message', {
            'message': data['message'],
            'speaker': player_label
        }, room=str(session_id), include_self=False)  # Don't echo back to sender

        # Store the player's message in SessionLogEntry
        player_msg_entry = SessionLogEntry(
            session_id=session_id,
            message=f"{player_label}: {data['message']}",
            entry_type="player"
        )
        db.session.add(player_msg_entry)
        db.session.commit()

        # Check if we are resolving a roll
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

                try:
                    for chunk in query_dm_function_stream(original_action, context, speaking_player=player_label, roll_result=roll_result):
                        if chunk:
                            emit('dm_chunk', {
                                'chunk': chunk,
                                'session_id': session_id
                            }, room=str(session_id))
                            
                            # Store each chunk
                            dm_entry_chunk = SessionLogEntry(
                                session_id=session_id,
                                message=f"DM (chunk): {chunk}",
                                entry_type="dm"
                            )
                            db.session.add(dm_entry_chunk)
                            db.session.commit()
                except Exception as e:
                    emit('error', {
                        'message': f'Error generating response: {str(e)}'
                    }, room=str(session_id))
                finally:
                    emit('dm_response_end', {'session_id': session_id}, room=str(session_id))
                return

        user_input = data['message']
        speaking_player = {
            "character_name": player_label,
            "player_id": str(player_id)
        }
        context = build_dm_context(world_id, campaign_id, session_id)

        emit('dm_response_start', {'session_id': session_id}, room=str(session_id))

        dm_response_text = ""  # Accumulate chunks here

        try:
            for chunk in query_dm_function_stream(user_input, context, speaking_player=speaking_player):
                if chunk:
                    emit('dm_chunk', {
                        'chunk': chunk,
                        'session_id': session_id
                    }, room=str(session_id))
                    
                    socketio.sleep(0)  # Ensure chunks are sent immediately
                    dm_response_text += chunk

        except Exception as e:
            emit('error', {
                'message': f'Error generating response: {str(e)}'
            }, room=str(session_id))
        finally:
            emit('dm_response_end', {'session_id': session_id}, room=str(session_id))

        # Store one final combined entry
        if dm_response_text.strip():
            final_dm_entry = SessionLogEntry(
                session_id=session_id,
                message=f"DM: {dm_response_text.strip()}",
                entry_type="dm"
            )
            db.session.add(final_dm_entry)
            db.session.commit()

        emit('session_log_update', {
            'session_id': session_id
        }, room=str(session_id))
