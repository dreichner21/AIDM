# segments.py
from flask import Blueprint, request, jsonify
import logging
from aidm_server.database import db
from aidm_server.models import CampaignSegment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

segments_bp = Blueprint("segments", __name__)

@segments_bp.route('', methods=['POST'])
def create_segment():
    """
    Create a new campaign segment for a given campaign.
    """
    data = request.json
    try:
        new_segment = CampaignSegment(
            campaign_id=data['campaign_id'],
            title=data['title'],
            description=data.get('description', ''),
            trigger_condition=data.get('trigger_condition', ''),
            tags=data.get('tags', '')
        )
        db.session.add(new_segment)
        db.session.commit()
        logging.info(f"Campaign Segment created with ID: {new_segment.segment_id}")
        return jsonify({"segment_id": new_segment.segment_id}), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create segment: {str(e)}")
        return jsonify({"error": "Failed to create segment"}), 400

@segments_bp.route('', methods=['GET'])
def list_segments():
    """
    List all segments or optionally filter by campaign_id.
    """
    campaign_id = request.args.get('campaign_id')
    query = CampaignSegment.query
    if campaign_id:
        query = query.filter_by(campaign_id=campaign_id)

    segments = query.all()
    results = []
    for seg in segments:
        results.append({
            "segment_id": seg.segment_id,
            "campaign_id": seg.campaign_id,
            "title": seg.title,
            "description": seg.description,
            "trigger_condition": seg.trigger_condition,
            "tags": seg.tags,
            "is_triggered": seg.is_triggered
        })
    return jsonify(results), 200

@segments_bp.route('/<int:segment_id>', methods=['GET'])
def get_segment(segment_id):
    """
    Retrieve details of a specific segment by ID.
    """
    seg = db.session.get(CampaignSegment, segment_id)
    if not seg:
        return jsonify({"error": "Segment not found"}), 404

    return jsonify({
        "segment_id": seg.segment_id,
        "campaign_id": seg.campaign_id,
        "title": seg.title,
        "description": seg.description,
        "trigger_condition": seg.trigger_condition,
        "tags": seg.tags,
        "is_triggered": seg.is_triggered
    }), 200

@segments_bp.route('/<int:segment_id>', methods=['PUT', 'PATCH'])
def update_segment(segment_id):
    """
    Update an existing campaign segment (e.g., trigger condition, description).
    """
    seg = db.session.get(CampaignSegment, segment_id)
    if not seg:
        return jsonify({"error": "Segment not found"}), 404

    data = request.json
    try:
        seg.title = data.get('title', seg.title)
        seg.description = data.get('description', seg.description)
        seg.trigger_condition = data.get('trigger_condition', seg.trigger_condition)
        seg.tags = data.get('tags', seg.tags)
        if 'is_triggered' in data:
            seg.is_triggered = data['is_triggered']

        db.session.commit()
        return jsonify({"message": "Segment updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update segment: {str(e)}")
        return jsonify({"error": "Failed to update segment"}), 400

@segments_bp.route('/<int:segment_id>', methods=['DELETE'])
def delete_segment(segment_id):
    """
    Delete a campaign segment.
    """
    seg = db.session.get(CampaignSegment, segment_id)
    if not seg:
        return jsonify({"error": "Segment not found"}), 404

    try:
        db.session.delete(seg)
        db.session.commit()
        return jsonify({"message": "Segment deleted"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete segment: {str(e)}")
        return jsonify({"error": "Failed to delete segment"}), 400
