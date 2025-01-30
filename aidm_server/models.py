from aidm_server.database import db
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class World(db.Model):
    __tablename__ = 'worlds'
    world_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    campaign_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    world_id = db.Column(db.Integer, db.ForeignKey('worlds.world_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    current_quest = db.Column(db.String, nullable=True)
    plot_points = db.Column(db.Text)
    active_npcs = db.Column(db.Text)
    location = db.Column(db.Text)

    world = db.relationship('World', backref='campaigns')

class Map(db.Model):
    __tablename__ = 'maps'
    map_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    world_id = db.Column(db.Integer, db.ForeignKey('worlds.world_id'), nullable=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    map_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    world = db.relationship('World', backref='maps')
    campaign = db.relationship('Campaign', backref='maps')

class Player(db.Model):
    __tablename__ = 'players'
    player_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    character_name = db.Column(db.String, nullable=False)
    race = db.Column(db.String)
    character_class = db.Column(db.String)  # Renamed from class_
    level = db.Column(db.Integer, default=1)
    stats = db.Column(db.Text)
    inventory = db.Column(db.Text)
    character_sheet = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    campaign = db.relationship('Campaign', backref='players')

class Session(db.Model):
    __tablename__ = 'sessions'
    session_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False)
    state_snapshot = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    campaign = db.relationship('Campaign', backref='sessions')
    log_entries = db.relationship('SessionLogEntry', backref='session', cascade="all, delete-orphan")

class Npc(db.Model):
    __tablename__ = 'npcs'
    npc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    world_id = db.Column(db.Integer, db.ForeignKey('worlds.world_id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    role = db.Column(db.String)
    backstory = db.Column(db.Text)

    world = db.relationship('World', backref='npcs')

class PlayerAction(db.Model):
    __tablename__ = 'player_actions'
    action_id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), nullable=False)
    action_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    player = db.relationship('Player', backref='actions')
    session = db.relationship('Session', backref='player_actions')

class StoryEvent(db.Model):
    __tablename__ = 'story_events'
    event_id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'))
    description = db.Column(db.Text)
    importance = db.Column(db.Integer)
    resolved = db.Column(db.Boolean, default=False)

class SessionLogEntry(db.Model):
    __tablename__ = 'session_log_entries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    entry_type = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    structured_output = db.Column(db.Text, nullable=True)

def get_full_session_log(session_id):
    entries = SessionLogEntry.query.filter_by(session_id=session_id).order_by(SessionLogEntry.timestamp).all()
    return "\n".join(entry.message for entry in entries)

# -- NEW MODEL FOR CAMPAIGN SEGMENTS --
class CampaignSegment(db.Model):
    """
    Represents a discrete story segment or milestone within a campaign.
    """
    __tablename__ = 'campaign_segments'

    segment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    trigger_condition = db.Column(db.Text, nullable=True)  # e.g. JSON or mini-DSL
    tags = db.Column(db.Text, nullable=True)               # store keywords / context data
    is_triggered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    campaign = db.relationship('Campaign', backref='segments')
