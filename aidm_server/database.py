import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import create_engine, MetaData
from sqlalchemy.pool import NullPool
import logging

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

def init_db(app):
    """
    Initialize the database with specific engine configuration.

    Args:
        app (Flask): The Flask application instance.

    Raises:
        Exception: If there is an error during database initialization.
    """
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
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {str(e)}")
        raise

def get_engine():
    """
    Get the SQLAlchemy engine.

    Returns:
        Engine: The SQLAlchemy engine instance.
    """
    return db.engine

def get_session():
    """
    Get a new SQLAlchemy session.

    Returns:
        Session: A new SQLAlchemy session.
    """
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db.engine)
    return Session()
