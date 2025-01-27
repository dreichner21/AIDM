# socketio_events.py

import json
from datetime import datetime
from flask_socketio import join_room, emit
from aidm_server.database import db
from aidm_server.models import (
    Player, Session, PlayerAction, SessionLogEntry,
    CampaignSegment
)
# Removed import of 'determine_roll_type' since it's no longer used
from aidm_server.llm import (
    query_dm_function,
    query_dm_function_stream,
    build_dm_context
)

def register_socketio_events(socketio):
    """
    Attach all Socket.IO event handlers to the given socketio instance.
    """

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
        """
        Handle a client sending a message, then stream DM responses.
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

        player = db.session.get(Player, player_id)
        if not player:
            emit('error', {'message': 'Invalid player ID'})
            return
        if player.campaign_id != campaign_id:
            emit('error', {'message': 'Player not part of this campaign'})
            return

        player_label = player.character_name

        # Record player action
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

        # Broadcast player's message
        emit('new_message', {
            'message': data['message'],
            'speaker': player_label
        }, room=str(session_id), include_self=False)

        # Store in the session log
        player_msg_entry = SessionLogEntry(
            session_id=session_id,
            message=f"{player_label}: {data['message']}",
            entry_type="player"
        )
        db.session.add(player_msg_entry)
        db.session.commit()

        # ---- CHECK FOR NEWLY TRIGGERED SEGMENTS ----
        untriggered_segments = CampaignSegment.query.filter_by(
            campaign_id=campaign_id,
            is_triggered=False
        ).all()

        def check_segment_trigger(segment, campaign_id):
            # Stub: Evaluate segment.trigger_condition for real logic
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

        # ---- Generate DM Response ----
        user_input = data['message']
        speaking_player = {
            "character_name": player_label,
            "player_id": str(player_id)
        }
        context = build_dm_context(world_id, campaign_id, session_id)

        emit('dm_response_start', {'session_id': session_id}, room=str(session_id))

        dm_response_text = ""

        try:
            # Stream DM response
            for chunk in query_dm_function_stream(user_input, context, speaking_player=speaking_player):
                if chunk:
                    emit('dm_chunk', {
                        'chunk': chunk,
                        'session_id': session_id
                    }, room=str(session_id))
                    socketio.sleep(0)  # ensure real-time chunk emission
                    dm_response_text += chunk

        except Exception as e:
            emit('error', {
                'message': f'Error generating response: {str(e)}'
            }, room=str(session_id))
        finally:
            emit('dm_response_end', {'session_id': session_id}, room=str(session_id))

        # Store combined DM response in log
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
