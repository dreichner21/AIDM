# __init__.py
# This file makes the "blueprints" directory into a Python package.
from .campaigns import campaigns_bp
from .worlds import worlds_bp  
from .players import players_bp
from .sessions import sessions_bp

__all__ = [
    'campaigns_bp',
    'worlds_bp',
    'players_bp', 
    'sessions_bp'
]