# aidm_server/database.py

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import create_engine, MetaData
from sqlalchemy.pool import NullPool
import logging

# Import our new GraphDB class
from aidm_server.graph_db import GraphDB

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate()

# Global reference to our graph DB driver
graph_db = None  # Will be set by init_graph_db
_initialized = False

def init_db(app):
    """
    Initialize the SQLite (or other SQL) database.
    """
    global _initialized
    try:
        # Create instance directory if it doesn't exist
        instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        
        database_path = os.path.join(instance_path, 'dnd_ai_dm.db')
        database_uri = f'sqlite:///{database_path}'
        
        app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'poolclass': NullPool,
            'connect_args': {
                'check_same_thread': False,
                'timeout': 30
            }
        }
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        migrate.init_app(app, db, render_as_batch=True)
        
        # Create database file if it doesn't exist
        if not os.path.exists(database_path):
            with app.app_context():
                db.create_all()
        logging.info("Database (SQLite) initialized successfully.")
        
    except Exception as e:
        logging.error(f"Error initializing SQL database: {str(e)}")
        raise


def init_graph_db(app):
    """
    Initialize the Neo4j Graph database connection using environment config.
    """
    global graph_db, _initialized
    
    if graph_db is not None:
        return graph_db

    # Prioritize environment variables
    uri = os.getenv('NEO4J_URI', app.config.get('NEO4J_URI'))
    user = os.getenv('NEO4J_USER', app.config.get('NEO4J_USER'))
    password = os.getenv('NEO4J_PASSWORD', app.config.get('NEO4J_PASSWORD'))

    if not all([uri, user, password]):
        app.logger.warning("Neo4j credentials not found in environment or config")
        return None

    try:
        graph_db = GraphDB(uri, user, password)
        app.logger.info(f"Neo4j connected successfully to {uri}")
        
        return graph_db
    except Exception as e:
        app.logger.error(f"Error initializing Neo4j: {str(e)}")
        return None

def get_graph_db():
    """
    Get the initialized graph database instance.
    
    Returns:
        GraphDB: The initialized graph database instance or None if not initialized
    """
    return graph_db

def get_engine():
    """
    Get the SQLAlchemy engine.
    """
    return db.engine

def get_session():
    """
    Get a new SQLAlchemy session.
    """
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db.engine)
    return Session()
