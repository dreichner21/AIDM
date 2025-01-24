from aidm_server.database import db  # Changed from ai_dm.database
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class World(db.Model):
    """
    Represents a world in the game.

    Attributes:
        world_id (int): The unique identifier for the world.
        name (str): The name of the world.
        description (str): A description of the world.
        created_at (datetime): The timestamp when the world was created.
    """
    __tablename__ = 'worlds'
    world_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Campaign(db.Model):
    """
    Represents a campaign in the game.

    Attributes:
        campaign_id (int): The unique identifier for the campaign.
        title (str): The title of the campaign.
        description (str): A description of the campaign.
        world_id (int): The ID of the world the campaign belongs to.
        created_at (datetime): The timestamp when the campaign was created.
        current_quest (str): The current quest in the campaign.
        plot_points (str): JSON array of key story elements.
        active_npcs (str): JSON array of current NPCs.
        location (str): Current party location.
    """
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
    """
    Represents a player in the game.

    Attributes:
        player_id (int): The unique identifier for the player.
        campaign_id (int): The ID of the campaign the player belongs to.
        name (str): The name of the player.
        character_name (str): The name of the player's character.
        race (str): The race of the player's character.
        class_ (str): The class of the player's character.
        level (int): The level of the player's character.
        stats (str): JSON string of the player's character stats.
        inventory (str): JSON string of the player's character inventory.
        character_sheet (str): JSON string of the player's character sheet.
        created_at (datetime): The timestamp when the player was created.
    """
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
    """
    Represents a session in the game.

    Attributes:
        session_id (int): The unique identifier for the session.
        campaign_id (int): The ID of the campaign the session belongs to.
        session_log (str): The log of the session.
        state_snapshot (str): The state snapshot of the session.
        created_at (datetime): The timestamp when the session was created.
    """
    __tablename__ = 'sessions'
    session_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False)
    session_log = db.Column(db.Text)
    state_snapshot = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    campaign = db.relationship('Campaign', backref='sessions')

class Npc(db.Model):
    """
    Represents a non-player character (NPC) in the game.

    Attributes:
        npc_id (int): The unique identifier for the NPC.
        world_id (int): The ID of the world the NPC belongs to.
        name (str): The name of the NPC.
        role (str): The role of the NPC.
        backstory (str): The backstory of the NPC.
    """
    __tablename__ = 'npcs'
    npc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    world_id = db.Column(db.Integer, db.ForeignKey('worlds.world_id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    role = db.Column(db.String)
    backstory = db.Column(db.Text)
    
    world = db.relationship('World', backref='npcs')

class PlayerAction(db.Model):
    """
    Tracks individual player actions during a session.

    Attributes:
        action_id (int): The unique identifier for the action.
        player_id (int): The ID of the player who performed the action.
        session_id (int): The ID of the session the action belongs to.
        action_text (str): The text of the action.
        timestamp (datetime): The timestamp when the action was performed.
    """
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
    """
    Represents a story event in the game.

    Attributes:
        event_id (int): The unique identifier for the event.
        campaign_id (int): The ID of the campaign the event belongs to.
        description (str): The description of the event.
        importance (int): The importance of the event on a scale of 1-10.
        resolved (bool): Whether the event has been resolved.
    """
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
    try:
        db.create_all()
        logging.info("Database tables created successfully.")
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")
        raise
    print("Done!")
