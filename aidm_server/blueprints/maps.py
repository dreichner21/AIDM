from flask import Blueprint, request, jsonify
from aidm_server.database import db
from aidm_server.models import Map, World, Campaign
from datetime import datetime
import json
import logging

maps_bp = Blueprint("maps", __name__)

@maps_bp.route('', methods=['POST'])
def create_map():
    """
    Create a new map.
    """
    data = request.json
    try:
        new_map = Map(
            world_id=data.get('world_id'),
            campaign_id=data.get('campaign_id'),
            title=data['title'],
            description=data.get('description', ''),
            map_data=json.dumps(data.get('map_data', {}))
        )
        db.session.add(new_map)
        db.session.commit()
        return jsonify({"map_id": new_map.map_id}), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create map: {str(e)}")
        return jsonify({"error": "Failed to create map"}), 400

@maps_bp.route('', methods=['GET'])
def list_maps():
    """
    List all maps or optionally filter by world/campaign.
    """
    world_id = request.args.get('world_id')
    campaign_id = request.args.get('campaign_id')
    
    query = Map.query
    if world_id:
        query = query.filter_by(world_id=world_id)
    if campaign_id:
        query = query.filter_by(campaign_id=campaign_id)

    maps = query.all()
    results = []
    for m in maps:
        results.append({
            "map_id": m.map_id,
            "world_id": m.world_id,
            "campaign_id": m.campaign_id,
            "title": m.title,
            "description": m.description,
            "map_data": json.loads(m.map_data) if m.map_data else {},
            "created_at": m.created_at.isoformat() if m.created_at else None
        })
    return jsonify(results)

@maps_bp.route('/<int:map_id>', methods=['GET'])
def get_map(map_id):
    """
    Get details of a specific map.
    """
    try:
        m = db.session.get(Map, map_id)
        if not m:
            return jsonify({"error": "Map not found"}), 404
        return jsonify({
            "map_id": m.map_id,
            "world_id": m.world_id,
            "campaign_id": m.campaign_id,
            "title": m.title,
            "description": m.description,
            "map_data": json.loads(m.map_data) if m.map_data else {},
            "created_at": m.created_at.isoformat() if m.created_at else None
        })
    except Exception as e:
        logging.error(f"Failed to get map: {str(e)}")
        return jsonify({"error": "Failed to get map"}), 400

@maps_bp.route('/<int:map_id>', methods=['PUT', 'PATCH'])
def update_map(map_id):
    """
    Update map details or features.
    """
    data = request.json
    m = db.session.get(Map, map_id)
    if not m:
        return jsonify({"error": "Map not found"}), 404
    try:
        m.title = data.get('title', m.title)
        m.description = data.get('description', m.description)
        if 'map_data' in data:
            m.map_data = json.dumps(data['map_data'])
        db.session.commit()
        return jsonify({"message": "Map updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update map: {str(e)}")
        return jsonify({"error": "Failed to update map"}), 400