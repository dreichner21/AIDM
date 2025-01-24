# worlds.py

from flask import Blueprint, request, jsonify
from aidm_server.database import db
from aidm_server.models import World
from datetime import datetime

worlds_bp = Blueprint("worlds", __name__)

@worlds_bp.route('', methods=['POST'])
def create_world():
    data = request.json
    new_world = World(
        name=data['name'],
        description=data['description']
    )
    db.session.add(new_world)
    db.session.commit()
    return jsonify({"world_id": new_world.world_id}), 201

@worlds_bp.route('/<int:world_id>', methods=['GET'])
def get_world(world_id):
    world = db.session.get(World, world_id)
    if not world:
        return jsonify({"error": "World not found"}), 404

    return jsonify({
        "world_id": world.world_id,
        "name": world.name,
        "description": world.description,
        "created_at": world.created_at.isoformat() if world.created_at else None
    })