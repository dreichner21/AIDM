from aidm_server.database import get_graph_db

class NPCGraphInterface:
    def __init__(self, npc_id):
        self.npc_id = npc_id
        self.graph_db = get_graph_db()

    def get_factions(self):
        return self.graph_db.get_npc_relationships(self.npc_id)

    def get_relationships(self):
        return self.graph_db.get_npc_relationships(self.npc_id)
