# socketio_events.py

import json
from datetime import datetime
from flask import request
from flask_socketio import join_room, leave_room, emit
from aidm_server.database import db
from aidm_server.models import (
    Player, Session, PlayerAction, SessionLogEntry,
    CampaignSegment
)
from aidm_server.llm import (
    query_dm_function,
    query_dm_function_stream,
    build_dm_context
)

# Track active players across sessions: { session_id: { player_id: {...player_data...} } }
active_players = {}
# Track which session/player each socket connection belongs to: { request.sid: {'session_id': x, 'player_id': y} }
socketio_connections = {}

def get_player_data(player_id):
    """
    Retrieve player data from the database and return a dict
    containing whichever fields you want in the UI.
    """
    player = db.session.get(Player, player_id)
    if not player:
        return None
    return {
        'id': player.player_id,
        'character_name': player.character_name,
        'name': player.name,
    }

def register_socketio_events(socketio):
    @socketio.on('join_session')
    def handle_join_session(data):
        session_id = data.get('session_id')
        player_id = data.get('player_id')

        if not session_id:
            emit('error', {'message': 'Session ID is required to join.'})
            return

        join_room(str(session_id))

        # Record this connection (for disconnect tracking)
        socketio_connections[request.sid] = {
            'session_id': session_id,
            'player_id': player_id
        }

        # Initialize structure if needed
        if session_id not in active_players:
            active_players[session_id] = {}

        # -- Avoid re-broadcast if player is already active --
        if player_id in active_players[session_id]:
            print(f"[DEBUG] Player {player_id} re-joined session {session_id}, skipping broadcast.")
            return

        # Fetch from DB and add to active players
        player_data = get_player_data(player_id)
        if player_data:
            active_players[session_id][player_id] = player_data

            # Broadcast that this player joined
            emit('player_joined', player_data, room=str(session_id))

            # Emit the updated list
            all_players = list(active_players[session_id].values())
            emit('active_players', all_players, room=str(session_id))

        # Optionally, also broadcast a general chat message
        emit('new_message', {
            'message': f"A new player joined session {session_id}!"
        }, room=str(session_id))

    @socketio.on('leave_session')
    def handle_leave_session(data):
        session_id = data.get('session_id')
        player_id = data.get('player_id')

        if not session_id or not player_id:
            emit('error', {'message': 'session_id and player_id are required'})
            return

        leave_room(str(session_id))

        # Remove from active players
        if session_id in active_players and player_id in active_players[session_id]:
            del active_players[session_id][player_id]
            emit('player_left', {'id': player_id}, room=str(session_id))

            updated_players = list(active_players[session_id].values())
            emit('active_players', updated_players, room=str(session_id))

        # Clean up the socket->session mapping
        if request.sid in socketio_connections:
            del socketio_connections[request.sid]

    @socketio.on('disconnect')
    def handle_disconnect():
        """
        Called automatically when a client disconnects (closes browser, etc.).
        Remove them from active_players if necessary.
        """
        connection_info = socketio_connections.pop(request.sid, None)
        if connection_info:
            session_id = connection_info['session_id']
            player_id = connection_info['player_id']

            if session_id in active_players and player_id in active_players[session_id]:
                del active_players[session_id][player_id]
                emit('player_left', {'id': player_id}, room=str(session_id))

                updated_players = list(active_players[session_id].values())
                emit('active_players', updated_players, room=str(session_id))

    @socketio.on('send_message')
    def handle_send_message(data):
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

        # Validate player
        player = db.session.get(Player, player_id)
        if not player:
            emit('error', {'message': 'Invalid player ID'})
            return
        if player.campaign_id != campaign_id:
            emit('error', {'message': 'Player not part of this campaign'})
            return

        player_label = player.character_name

        # Save player action
        new_action = PlayerAction(
            player_id=player_id,
            session_id=session_id,
            action_text=data['message'],
            timestamp=datetime.utcnow()
        )
        db.session.add(new_action)
        db.session.commit()

        # Validate session
        session_obj = db.session.get(Session, session_id)
        if not session_obj:
            emit('error', {'message': 'Session not found'})
            return

        # Broadcast player's message
        emit('new_message', {
            'message': data['message'],
            'speaker': player_label
        }, room=str(session_id), include_self=False)

        # Store in session log
        player_msg_entry = SessionLogEntry(
            session_id=session_id,
            message=f"{player_label}: {data['message']}",
            entry_type="player"
        )
        db.session.add(player_msg_entry)
        db.session.commit()

        # Check for newly triggered segments
        untriggered_segments = CampaignSegment.query.filter_by(
            campaign_id=campaign_id,
            is_triggered=False
        ).all()

        def check_segment_trigger(segment, campaign_id):
            # Implement your custom trigger logic
            return False

        for seg in untriggered_segments:
            if check_segment_trigger(seg, campaign_id):
                seg.is_triggered = True
                db.session.commit()
                emit('segment_triggered', {
                    'segment_id': seg.segment_id,
                    'title': seg.title
                }, room=str(session_id))

                log_entry = SessionLogEntry(
                    session_id=session_id,
                    message=f"**Segment Triggered**: {seg.title}",
                    entry_type="dm"
                )
                db.session.add(log_entry)
                db.session.commit()

        # Generate DM response
        user_input = data['message']
        speaking_player = {
            "character_name": player_label,
            "player_id": str(player_id)
        }
        context = build_dm_context(world_id, campaign_id, session_id)

        print("\n=== DM CONTEXT ===")
        print(context)
        print("=== END CONTEXT ===\n")

        emit('dm_response_start', {'session_id': session_id}, room=str(session_id))

        dm_response_text = ""

        try:
            for chunk in query_dm_function_stream(user_input, context, speaking_player=speaking_player):
                if chunk:
                    emit('dm_chunk', {
                        'chunk': chunk,
                        'session_id': session_id
                    }, room=str(session_id))
                    socketio.sleep(0)
                    dm_response_text += chunk

        except Exception as e:
            emit('error', {
                'message': f'Error generating response: {str(e)}'
            }, room=str(session_id))
        finally:
            emit('dm_response_end', {'session_id': session_id}, room=str(session_id))

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
