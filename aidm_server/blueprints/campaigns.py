# campaigns.py

from flask import Blueprint, request, jsonify
from aidm_server.database import db
from aidm_server.models import Campaign
from datetime import datetime
import json

campaigns_bp = Blueprint("campaigns", __name__)

@campaigns_bp.route('', methods=['POST'])
def create_campaign():
    data = request.json
    new_campaign = Campaign(
        title=data['title'],
        description=data.get('description', ''),
        world_id=data['world_id']
    )
    db.session.add(new_campaign)
    db.session.commit()
    return jsonify({"campaign_id": new_campaign.campaign_id}), 201

@campaigns_bp.route('', methods=['GET'])
def list_campaigns():
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
    return jsonify(results)

@campaigns_bp.route('/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    campaign = db.session.get(Campaign, campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    data = {
        "campaign_id": campaign.campaign_id,
        "title": campaign.title,
        "description": campaign.description,
        "world_id": campaign.world_id,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None
    }
    return jsonify(data)