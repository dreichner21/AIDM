# campaigns.py

from flask import Blueprint, request, jsonify
from aidm_server.database import db
from aidm_server.models import Campaign
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

campaigns_bp = Blueprint("campaigns", __name__)

@campaigns_bp.route('', methods=['POST'])
def create_campaign():
    """
    Create a new campaign.

    Returns:
        JSON response with the campaign ID and status code 201 on success,
        or an error message and status code 400 on failure.
    """
    data = request.json
    try:
        new_campaign = Campaign(
            title=data['title'],
            description=data.get('description', ''),
            world_id=data['world_id']
        )
        db.session.add(new_campaign)
        db.session.commit()
        logging.info(f"Campaign created with ID: {new_campaign.campaign_id}")
        return jsonify({"campaign_id": new_campaign.campaign_id}), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create campaign: {str(e)}")
        return jsonify({"error": "Failed to create campaign"}), 400

@campaigns_bp.route('', methods=['GET'])
def list_campaigns():
    """
    List all campaigns.

    Returns:
        JSON response with a list of campaigns.
    """
    try:
        campaigns = Campaign.query.all()
        results = []
        for c in campaigns:
            results.append({
                "campaign_id": c.campaign_id,
                "title": c.title,
                "description": c.description,
                "world_id": c.world_id,
                "created_at": c.created_at.isoformat() if c.created_at else None
            })
        logging.info("Campaigns listed successfully")
        return jsonify(results)
    except Exception as e:
        logging.error(f"Failed to list campaigns: {str(e)}")
        return jsonify({"error": "Failed to list campaigns"}), 400

@campaigns_bp.route('/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """
    Get details of a specific campaign.

    Args:
        campaign_id (int): The ID of the campaign to retrieve.

    Returns:
        JSON response with the campaign details, or an error message if not found.
    """
    try:
        campaign = db.session.get(Campaign, campaign_id)
        if not campaign:
            logging.warning(f"Campaign not found: ID {campaign_id}")
            return jsonify({"error": "Campaign not found"}), 404

        data = {
            "campaign_id": campaign.campaign_id,
            "title": campaign.title,
            "description": campaign.description,
            "world_id": campaign.world_id,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None
        }
        logging.info(f"Campaign details retrieved: ID {campaign_id}")
        return jsonify(data)
    except Exception as e:
        logging.error(f"Failed to get campaign: {str(e)}")
        return jsonify({"error": "Failed to get campaign"}), 400
