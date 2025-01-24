# players.py

from flask import Blueprint, request, jsonify
import logging
from aidm_server.database import db
from aidm_server.models import Player, Campaign

players_bp = Blueprint("players", __name__)

@players_bp.route('/campaigns/<int:campaign_id>/players', methods=['GET', 'POST'])  # no trailing slash
def handle_players(campaign_id):
    if request.method == 'POST':
        return add_player(campaign_id)
    else:
        return get_players(campaign_id)

def add_player(campaign_id):
    data = request.json

    campaign = db.session.get(Campaign, campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    try:
        new_player = Player(
            campaign_id=campaign_id,
            name=data['name'],
            character_name=data['character_name'],
            race=data.get('race', ''),
            class_=data.get('char_class', ''),
            level=data.get('level', 1)
        )
        db.session.add(new_player)
        db.session.commit()
        return jsonify({
            "player_id": new_player.player_id,
            "message": "Player successfully created"
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error("Failed to create player: %s", str(e))
        return jsonify({"error": "Failed to create player"}), 400

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
            "level": p.level
        })
    return jsonify(results)