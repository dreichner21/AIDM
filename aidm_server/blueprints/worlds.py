# worlds.py

from flask import Blueprint, request, jsonify
from aidm_server.database import db
from aidm_server.models import World
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

worlds_bp = Blueprint("worlds", __name__)

@worlds_bp.route('', methods=['POST'])
def create_world():
    """
    Create a new world.

    Returns:
        JSON response with the world ID and status code 201 on success,
        or an error message and status code 400 on failure.
    """
    data = request.json
    try:
        new_world = World(
            name=data['name'],
            description=data['description']
        )
        db.session.add(new_world)
        db.session.commit()
        logging.info(f"World created with ID: {new_world.world_id}")
        return jsonify({"world_id": new_world.world_id}), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create world: {str(e)}")
        return jsonify({"error": "Failed to create world"}), 400

@worlds_bp.route('/<int:world_id>', methods=['GET'])
def get_world(world_id):
    """
    Get details of a specific world.

    Args:
        world_id (int): The ID of the world to retrieve.

    Returns:
        JSON response with the world details, or an error message if not found.
    """
    try:
        world = db.session.get(World, world_id)
        if not world:
            logging.warning(f"World not found: ID {world_id}")
            return jsonify({"error": "World not found"}), 404

        data = {
            "world_id": world.world_id,
            "name": world.name,
            "description": world.description,
            "created_at": world.created_at.isoformat() if world.created_at else None
        }
        logging.info(f"World details retrieved: ID {world_id}")
        return jsonify(data)
    except Exception as e:
        logging.error(f"Failed to get world: {str(e)}")
        return jsonify({"error": "Failed to get world"}), 400
