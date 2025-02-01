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
    query_dm_function_stream
)
from aidm_server.database import get_graph_db  # <-- We'll use this to get our Neo4j instance

# Track active players across sessions: { session_id: { player_id: {...player_data...} } }
active_players = {}
# Map each socket connection to a specific session/player
socketio_connections = {}

def get_player_data(player_id):
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
        socketio_connections[request.sid] = {'session_id': session_id, 'player_id': player_id}

        if session_id not in active_players:
            active_players[session_id] = {}

        # If the player is already in the dict, skip re-broadcast
        if player_id in active_players[session_id]:
            print(f"[DEBUG] Player {player_id} re-joined session {session_id}, skipping broadcast.")
            return

        # Load from DB
        player_data = get_player_data(player_id)
        if player_data:
            active_players[session_id][player_id] = player_data
            emit('player_joined', player_data, room=str(session_id))
            all_players = list(active_players[session_id].values())
            emit('active_players', all_players, room=str(session_id))

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

        if session_id in active_players and player_id in active_players[session_id]:
            del active_players[session_id][player_id]
            emit('player_left', {'id': player_id}, room=str(session_id))
            updated_players = list(active_players[session_id].values())
            emit('active_players', updated_players, room=str(session_id))

        if request.sid in socketio_connections:
            del socketio_connections[request.sid]

    @socketio.on('disconnect')
    def handle_disconnect():
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
        user_input = data['message']

        # Validate player
        player = db.session.get(Player, player_id)
        player_name = player.name
        character_name = player.character_name

        if not player:
            emit('error', {'message': 'Invalid player ID'})
            return
        if player.campaign_id != campaign_id:
            emit('error', {'message': 'Player not part of this campaign'})
            return

        # Save player action to SQL DB
        new_action = PlayerAction(
            player_id=player_id,
            session_id=session_id,
            action_text=user_input,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_action)
        db.session.commit()

        # --- NEW: Also log this action in Neo4j for momentum tracking ---
        graph_db = get_graph_db()
        if graph_db:
            # Create or merge an Action node in Neo4j
            graph_db.create_action_node(
                action_id=new_action.action_id,
                session_id=session_id,
                text=user_input,
                severity=1.0  # you might vary severity based on content
            )
            # Optionally link player -> action
            # If you also have a Player node in Neo4j with property player_id = X:
            graph_db.run_query("""
                MERGE (p:Player {player_id: $pid})
                SET p.name = $player_name,
                    p.character_name = $character_name
                RETURN p
            """, 
            {
                "pid": player_id,
                "player_name": player.name,
                "character_name": player.character_name
            }
        )
            graph_db.attach_player_to_action(player_id, new_action.action_id)

        player_label = player.character_name

        # Broadcast player's message to others
        emit('new_message', {
            'message': data['message'],
            'speaker': player_label
        }, room=str(session_id), include_self=False)

        # Store in session log
        player_msg_entry = SessionLogEntry(
            session_id=session_id,
            message=f"{player_label}: {user_input}",
            entry_type="player"
        )
        db.session.add(player_msg_entry)
        db.session.commit()

        # Check for newly triggered segments (placeholder logic)
        untriggered_segments = CampaignSegment.query.filter_by(
            campaign_id=campaign_id,
            is_triggered=False
        ).all()

        def check_segment_trigger(segment, cid):
            # Custom logic or pattern matching
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

        # --- NEW: Check momentum and possibly run cascade triggers ---
        if graph_db:
            current_momentum = graph_db.calculate_session_momentum(session_id)
            # Example threshold-based cascade
            if current_momentum > 5.0:
                graph_db.cascade_triggers(session_id, threshold=5.0)
        
        # =========================================================
        #  Generate the DM response (streaming):
        # =========================================================
        speaking_player = {
            "character_name": player_label,
            "player_id": str(player_id)
        }

        emit('dm_response_start', {'session_id': session_id}, room=str(session_id))

        dm_response_text = ""

        # We call our streaming generator
        for chunk in query_dm_function_stream(user_input, session_id, speaking_player=speaking_player):
            if chunk.startswith("<END_OF_STREAM:"):
                # This chunk includes the JSON of the structured response.
                try:
                    json_str = chunk.replace("<END_OF_STREAM:", "").replace(">", "")
                    structured_data = json.loads(json_str)
                    emit('dm_structured_response', {
                        'structured': structured_data
                    }, room=str(session_id))

                    # Optionally log the structured response to SessionLogEntry
                    final_dm_entry = SessionLogEntry(
                        session_id=session_id,
                        message=f"DM: {structured_data.get('primary', '')}",
                        entry_type="dm",
                        structured_output=json.dumps(structured_data)
                    )
                    db.session.add(final_dm_entry)
                    db.session.commit()

                except Exception as e:
                    emit('error', {
                        'message': f"Error parsing structured response: {str(e)}"
                    }, room=str(session_id))
            else:
                # normal chunk of text
                dm_response_text += chunk
                emit('dm_chunk', {
                    'chunk': chunk,
                    'session_id': session_id
                }, room=str(session_id))
                socketio.sleep(0)  # Yield control back to event loop

        emit('dm_response_end', {'session_id': session_id}, room=str(session_id))

        # We also mark log update so the client can refresh session logs
        emit('session_log_update', {'session_id': session_id}, room=str(session_id))
