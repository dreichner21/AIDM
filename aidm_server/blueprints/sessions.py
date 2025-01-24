# sessions.py

from flask import Blueprint, request, jsonify
from aidm_server.database import db
from aidm_server.models import Session
from datetime import datetime

sessions_bp = Blueprint("sessions", __name__)

@sessions_bp.route('/start', methods=['POST'])  # no change needed - relative path
def start_new_session():
    data = request.json
    campaign_id = data['campaign_id']
    new_session = Session(campaign_id=campaign_id)
    db.session.add(new_session)
    db.session.commit()
    return jsonify({"session_id": new_session.session_id}), 201

@sessions_bp.route('/<int:session_id>/end', methods=['POST'])  # no change needed - relative path
def end_game_session(session_id):
    session_obj = db.session.get(Session, session_id)
    if not session_obj:
        return jsonify({"error": "Session not found"}), 404

    full_log = session_obj.session_log or ""
    from aidm_server.llm import query_gpt  # Changed from ai_dm.llm

    recap_prompt = (
        "Please provide a concise summary of this D&D session, highlighting key events, "
        "important decisions, and any significant character developments:\n\n" + full_log
    )
    recap = query_gpt(prompt=recap_prompt, system_message="You are a D&D session summarizer.")

    session_obj.state_snapshot = jsonify({
        "recap": recap,
        "ended_at": datetime.utcnow().isoformat()
    }).data.decode("utf-8")
    db.session.commit()

    return jsonify({"recap": recap})

@sessions_bp.route('/campaigns/<int:campaign_id>/sessions', methods=['GET'])
def list_campaign_sessions(campaign_id):
    sessions = Session.query.filter_by(campaign_id=campaign_id).all()
    results = []
    for s in sessions:
        results.append({
            "session_id": s.session_id,
            "campaign_id": s.campaign_id,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "state_snapshot": s.state_snapshot
        })
    return jsonify(results)