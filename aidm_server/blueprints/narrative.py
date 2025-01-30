# aidm_server/blueprints/narrative.py

from flask import Blueprint, request, jsonify
import logging
from aidm_server.database import get_graph_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

narrative_bp = Blueprint("narrative", __name__)

@narrative_bp.route('/plotpoints', methods=['POST'])
def create_plotpoint():
    """
    Create or update a PlotPoint in Neo4j with a given ID and volatility.
    Additional properties can be passed in the JSON.
    """
    data = request.json or {}
    plotpoint_id = data.get('plotpoint_id')
    volatility = data.get('volatility', 1.0)
    if not plotpoint_id:
        return jsonify({"error": "plotpoint_id is required"}), 400

    graph_db = get_graph_db()
    if not graph_db:
        return jsonify({"error": "Graph DB not available"}), 500

    # We'll assume the user can pass extra fields
    extra_fields = {k: v for k, v in data.items() if k not in ['plotpoint_id','volatility']}
    graph_db.create_plotpoint(plotpoint_id, volatility, **extra_fields)
    return jsonify({"message": "PlotPoint created/updated"}), 200

@narrative_bp.route('/plotpoints/<int:plotpoint_id>/link_action', methods=['POST'])
def link_action(plotpoint_id):
    """
    Link an Action node to a PlotPoint via an IMPACTS relationship with a given weight.
    """
    data = request.json or {}
    action_id = data.get('action_id')
    weight = data.get('weight', 1.0)
    if not action_id:
        return jsonify({"error": "action_id is required"}), 400

    graph_db = get_graph_db()
    if not graph_db:
        return jsonify({"error": "Graph DB not available"}), 500

    graph_db.link_action_to_plotpoint(action_id, plotpoint_id, weight)
    return jsonify({"message": "Action linked to PlotPoint"}), 200

@narrative_bp.route('/momentum/<int:session_id>', methods=['GET'])
def get_momentum(session_id):
    """
    Returns the aggregated momentum for a given session.
    """
    graph_db = get_graph_db()
    if not graph_db:
        return jsonify({"error": "Graph DB not available"}), 500

    momentum_val = graph_db.calculate_session_momentum(session_id)
    return jsonify({"session_id": session_id, "momentum": momentum_val}), 200
