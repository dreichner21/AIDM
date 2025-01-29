import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

# Ensure you've imported load_dotenv if you're using .env files
from dotenv import load_dotenv
load_dotenv()

from aidm_server.database import db, init_db, init_graph_db
from aidm_server.blueprints.campaigns import campaigns_bp
from aidm_server.blueprints.worlds import worlds_bp
from aidm_server.blueprints.players import players_bp
from aidm_server.blueprints.sessions import sessions_bp
from aidm_server.blueprints.maps import maps_bp
from aidm_server.blueprints.segments import segments_bp  # NEW
from aidm_server.blueprints.socketio_events import register_socketio_events
from aidm_server.blueprints.admin import configure_admin

def create_app():
    app = Flask(__name__)
    CORS(app)

    # You may store your secret key in an environment variable or .env
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "my_dev_secret")

    # Neo4j config from environment or .env
    app.config['NEO4J_URI'] = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    app.config['NEO4J_USER'] = os.getenv('NEO4J_USER', 'neo4j')
    app.config['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD', 'password')

    # Initialize SQLite DB
    init_db(app)

    # Initialize Neo4j Graph DB
    print("About to call init_graph_db now...")
    init_graph_db(app)
    print("Finished calling init_graph_db!")

    # Register blueprints with /api prefix
    app.register_blueprint(campaigns_bp, url_prefix='/api/campaigns')
    app.register_blueprint(worlds_bp, url_prefix='/api/worlds')
    app.register_blueprint(players_bp, url_prefix='/api/players')
    app.register_blueprint(sessions_bp, url_prefix='/api/sessions')
    app.register_blueprint(maps_bp, url_prefix='/api/maps')
    app.register_blueprint(segments_bp, url_prefix='/api/segments')

    # Configure Flask-Admin
    configure_admin(app, db)

    return app

app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*")

# Register Socket.IO events
register_socketio_events(socketio)

if __name__ == '__main__':
    # Create tables if they don't already exist
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database tables created successfully.")
        except Exception as e:
            logging.error(f"Error creating database tables: {str(e)}")
            raise

    # Run in debug mode, but disable the reloader to avoid duplicated logs
    socketio.run(app, debug=True, port=5000, use_reloader=False)
