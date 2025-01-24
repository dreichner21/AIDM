from datetime import datetime
from ai_dm.database import db

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
    plot_points = db.Column(db.Text)  # JSON array of key story elements
    active_npcs = db.Column(db.Text)  # JSON array of current NPCs
    location = db.Column(db.Text)     # Current party location
    
    world = db.relationship('World', backref='campaigns')

class Player(db.Model):
    __tablename__ = 'players'
    player_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    character_name = db.Column(db.String, nullable=False)
    race = db.Column(db.String)
    class_ = db.Column(db.String)
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
    session_log = db.Column(db.Text)
    state_snapshot = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    campaign = db.relationship('Campaign', backref='sessions')

class Npc(db.Model):
    __tablename__ = 'npcs'
    npc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    world_id = db.Column(db.Integer, db.ForeignKey('worlds.world_id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    role = db.Column(db.String)
    backstory = db.Column(db.Text)
    
    world = db.relationship('World', backref='npcs')

class PlayerAction(db.Model):
    """Tracks individual player actions during a session"""
    __tablename__ = 'player_actions'
    
    action_id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), nullable=False)  # Make non-nullable
    action_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', backref='actions')
    session = db.relationship('Session', backref='player_actions')

class StoryEvent(db.Model):
    __tablename__ = 'story_events'
    event_id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'))
    description = db.Column(db.Text)
    importance = db.Column(db.Integer)  # 1-10 scale
    resolved = db.Column(db.Boolean, default=False)

if __name__ == '__main__':
    with db.engine.connect() as conn:
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print("Existing tables:", [row[0] for row in result])

    print("Creating tables if they don't exist...")
    db.create_all()
    print("Done!")
