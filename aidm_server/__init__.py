from flask import Flask
from dotenv import load_dotenv
from aidm_server.database import init_db, init_graph_db
import os

# ...existing imports...

def create_app(config=None):
    # Load environment variables from .env file
    load_dotenv()
    
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.update(config)
    
    # Initialize databases
    init_db(app)
    app.graph_db = init_graph_db(app)
    
    # ...rest of app initialization...
    
    return app
