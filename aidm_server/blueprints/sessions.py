# sessions.py

from flask import Blueprint, request, jsonify
from aidm_server.database import db
from aidm_server.models import Session
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sessions_bp = Blueprint("sessions", __name__)

@sessions_bp.route('/start', methods=['POST'])
def start_new_session():
    """
    Start a new session for a given campaign.

    Returns:
        JSON response with the new session ID and status code 201 on success,
        or an error message and status code 400 on failure.
    """
    data = request.json
    campaign_id = data['campaign_id']
    try:
        new_session = Session(campaign_id=campaign_id)
        db.session.add(new_session)
        db.session.commit()
        logging.info(f"Session started with ID: {new_session.session_id}")
        return jsonify({"session_id": new_session.session_id}), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to start session: {str(e)}")
        return jsonify({"error": "Failed to start session"}), 400

@sessions_bp.route('/<int:session_id>/end', methods=['POST'])
def end_game_session(session_id):
    """
    End a game session and provide a recap.

    Args:
        session_id (int): The ID of the session to end.

    Returns:
        JSON response with the session recap, or an error message if not found.
    """
    session_obj = db.session.get(Session, session_id)
    if not session_obj:
        logging.warning(f"Session not found: ID {session_id}")
        return jsonify({"error": "Session not found"}), 404

    full_log = session_obj.session_log or ""
    from aidm_server.llm import query_gpt

    recap_prompt = (
        "Please provide a concise summary of this D&D session, highlighting key events, "
        "important decisions, and any significant character developments:\n\n" + full_log
    )
    try:
        recap = query_gpt(prompt=recap_prompt, system_message="You are a D&D session summarizer.")
        session_obj.state_snapshot = jsonify({
            "recap": recap,
            "ended_at": datetime.utcnow().isoformat()
        }).data.decode("utf-8")
        db.session.commit()
        logging.info(f"Session ended with ID: {session_id}")
        return jsonify({"recap": recap})
    except Exception as e:
        logging.error(f"Failed to end session: {str(e)}")
        return jsonify({"error": "Failed to end session"}), 400

@sessions_bp.route('/campaigns/<int:campaign_id>/sessions', methods=['GET'])
def list_campaign_sessions(campaign_id):
    """
    List all sessions for a specific campaign.

    Args:
        campaign_id (int): The ID of the campaign.

    Returns:
        JSON response with a list of sessions.
    """
    try:
        sessions = Session.query.filter_by(campaign_id=campaign_id).all()
        results = []
        for s in sessions:
            results.append({
                "session_id": s.session_id,
                "campaign_id": s.campaign_id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "state_snapshot": s.state_snapshot
            })
        logging.info(f"Sessions listed for campaign ID: {campaign_id}")
        return jsonify(results)
    except Exception as e:
        logging.error(f"Failed to list sessions: {str(e)}")
        return jsonify({"error": "Failed to list sessions"}), 400
