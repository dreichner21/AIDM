# aidm_server/context_engine.py

import logging
from aidm_server.database import db, graph_db, get_graph_db
from aidm_server.models import (
    World,
    Campaign,
    Player,
    Session,
    SessionLogEntry
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RecentEventsBuffer:
    """
    Stores a limited number of recent events.
    """
    def __init__(self, capacity: int = 15):
        self.capacity = capacity
        self.buffer = []

    def add(self, event: str):
        self.buffer.append(event)
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)

    def get_events(self):
        return list(self.buffer)

class VectorDBBackedMemory:
    """
    Placeholder for a long-term memory system.
    """
    def store(self, data: str):
        pass

    def query(self, query_str: str) -> list[str]:
        return []

class DualMemoryStore:
    def __init__(self, working: RecentEventsBuffer, persistent: VectorDBBackedMemory):
        self.working = working
        self.persistent = persistent

class ContextEngine:
    """
    Builds a multi-section context string for the LLM, pulling from DB and memory.
    """
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.memory = DualMemoryStore(
            working=RecentEventsBuffer(capacity=15),
            persistent=VectorDBBackedMemory()
        )

    def build_context(self) -> str:
        return f"""
World State: {self._get_world_summary()}
Momentum: {self._get_session_momentum()}
Campaign Progress: {self._get_campaign_timeline()}
Active Characters: {self._get_character_dossiers()}
Recent Developments: {self._get_significant_events()}
Outstanding Threads: {self._get_open_plot_hooks()}
Current Scene: {self._get_scene_description()}
Style Guide: {self._get_narrative_style_prefs()}
"""

    def _get_world_summary(self) -> str:
        session_obj = db.session.get(Session, self.session_id)
        if not session_obj:
            return "Unknown (no session found)"

        campaign = db.session.get(Campaign, session_obj.campaign_id)
        if not campaign:
            return "Unknown (no campaign found)"

        world = db.session.get(World, campaign.world_id)
        if not world:
            return "No world data found."
        return f"{world.name} - {world.description}"

    # NEW
    def _get_session_momentum(self) -> str:
        gdb = get_graph_db()
        if not gdb:
            return "Graph DB not connected."
        val = gdb.calculate_session_momentum(self.session_id)
        return f"{val:.2f}"

    def _get_campaign_timeline(self) -> str:
        return "Timeline not implemented."

    def _get_character_dossiers(self) -> str:
        session_obj = db.session.get(Session, self.session_id)
        if not session_obj:
            return "No session."
        campaign_id = session_obj.campaign_id

        players = Player.query.filter_by(campaign_id=campaign_id).all()
        lines = []
        for p in players:
            lines.append(
                f"Player {p.player_id} - {p.character_name}, Race: {p.race}, Class: {p.character_class}, Level: {p.level}"
            )
        return "\n".join(lines)

    def _get_significant_events(self) -> str:
        logs = SessionLogEntry.query\
            .filter_by(session_id=self.session_id)\
            .order_by(SessionLogEntry.timestamp.desc())\
            .limit(5)\
            .all()

        lines = []
        for entry in reversed(logs):
            lines.append(f"[{entry.entry_type.upper()}] {entry.message}")
        return "\n".join(lines)

    def _get_open_plot_hooks(self) -> str:
        return "Open hooks not implemented."

    def _get_scene_description(self) -> str:
        return "Scene details not implemented."

    def _get_narrative_style_prefs(self) -> str:
        return "Keep responses in a classical fantasy tone with moderate detail."
