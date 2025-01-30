# aidm_server/graph_db.py

import logging
from neo4j import GraphDatabase, Result

class GraphDB:
    """
    Encapsulates all Neo4j connection and query logic.
    
    Example usage:
        graph_db = GraphDB(uri, user, password)
        graph_db.create_npc_node(npc_id=1, name="Gandalf", role="Wizard")
    """

    def __init__(self, uri, user, password):
        """
        Initialize the GraphDB driver with the provided connection details.
        
        Args:
            uri (str): Bolt URI for your Neo4j instance, e.g. 'bolt://localhost:7687'.
            user (str): Username for Neo4j authentication.
            password (str): Password for Neo4j authentication.
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logging.info("Neo4j driver initialized.")

    def close(self):
        """
        Close the underlying driver connection.
        """
        if self.driver:
            self.driver.close()
            logging.info("Neo4j driver connection closed.")

    def run_query(self, query: str, parameters: dict = None) -> list:
        """
        Generic helper to run a Cypher query and return the results as a list.
        
        Args:
            query (str): Cypher query string
            parameters (dict): Parameter dictionary for the Cypher query

        Returns:
            list: A list of records from the query result.
        """
        with self.driver.session() as session:
            try:
                result: Result = session.run(query, parameters or {})
                return list(result)
            except Exception as e:
                logging.error(f"Error running query:\n{query}\nParameters: {parameters}\nException: {str(e)}")
                raise

    # -------------------------------------------------------------------------
    # NPC Node Operations (existing code)
    # -------------------------------------------------------------------------

    def create_npc_node(self, npc_id: int, name: str, role: str) -> None:
        """
        Merge (create if not exists) an NPC node in the graph with properties.
        """
        query = """
            MERGE (n:NPC {npc_id: $npc_id})
            SET n.name = $name,
                n.role = $role
            RETURN n
        """
        params = {
            "npc_id": npc_id,
            "name": name,
            "role": role
        }
        self.run_query(query, params)
        logging.info(f"NPC node merged/created with npc_id={npc_id}, name='{name}', role='{role}'")

    def get_npc_node(self, npc_id: int) -> dict:
        """
        Retrieve a single NPC node's properties by its npc_id.
        """
        query = """
            MATCH (n:NPC {npc_id: $npc_id})
            RETURN properties(n) as props
        """
        results = self.run_query(query, {"npc_id": npc_id})
        if results:
            return results[0]["props"]  # The first row, 'props' column
        return {}

    def update_npc_node(self, npc_id: int, name: str = None, role: str = None) -> None:
        """
        Update an existing NPC node. If a field is None, we skip updating it.
        """
        set_clauses = []
        params = {"npc_id": npc_id}
        
        if name is not None:
            set_clauses.append("n.name = $name")
            params["name"] = name

        if role is not None:
            set_clauses.append("n.role = $role")
            params["role"] = role

        if not set_clauses:
            logging.info("No fields to update, skipping.")
            return

        set_statement = ", ".join(set_clauses)
        query = f"""
            MATCH (n:NPC {{npc_id: $npc_id}})
            SET {set_statement}
            RETURN n
        """
        self.run_query(query, params)
        logging.info(f"NPC node updated with npc_id={npc_id}, name='{name}', role='{role}'")

    def delete_npc_node(self, npc_id: int) -> None:
        """
        Delete an NPC node (and any relationships) by npc_id.
        """
        query = """
            MATCH (n:NPC {npc_id: $npc_id})
            DETACH DELETE n
        """
        self.run_query(query, {"npc_id": npc_id})
        logging.info(f"NPC node with npc_id={npc_id} deleted (including relationships).")

    def get_npc_relationships(self, npc_id: int) -> list:
        """
        Return all direct relationships for a given NPC node.
        """
        query = """
            MATCH (n:NPC {npc_id: $npc_id})-[r]-(m)
            RETURN type(r) as rel_type, properties(m) as other_node
        """
        results = self.run_query(query, {"npc_id": npc_id})
        rels = []
        for record in results:
            rel_type = record["rel_type"]
            other_node = record["other_node"]
            rels.append({
                "relationship": rel_type,
                "node": other_node
            })
        return rels

    # -------------------------------------------------------------------------
    # Relationship Methods (existing code)
    # -------------------------------------------------------------------------

    def create_relationship(
        self,
        start_label: str,
        start_key: int,
        end_label: str,
        end_key: int,
        rel_type: str
    ) -> None:
        """
        Merge a relationship (rel_type) between two existing nodes identified by:
          - (start_label { npc_id = start_key })
          - (end_label { npc_id = end_key })
        """
        query = f"""
            MERGE (a:{start_label} {{npc_id: $start_key}})
            MERGE (b:{end_label} {{npc_id: $end_key}})
            MERGE (a)-[r:{rel_type}]->(b)
            RETURN r
        """
        params = {
            "start_key": start_key,
            "end_key": end_key
        }
        self.run_query(query, params)
        logging.info(
            f"Relationship '{rel_type}' merged between "
            f"{start_label}(npc_id={start_key}) and {end_label}(npc_id={end_key})"
        )

    def delete_relationship(
        self,
        start_label: str,
        start_key: int,
        end_label: str,
        end_key: int,
        rel_type: str
    ) -> None:
        """
        Delete a specific relationship of rel_type between two known nodes.
        """
        query = f"""
            MATCH (a:{start_label} {{npc_id: $start_key}})-[r:{rel_type}]->(b:{end_label} {{npc_id: $end_key}})
            DELETE r
        """
        params = {
            "start_key": start_key,
            "end_key": end_key
        }
        self.run_query(query, params)
        logging.info(
            f"Relationship '{rel_type}' deleted between "
            f"{start_label}(npc_id={start_key}) and {end_label}(npc_id={end_key})."
        )

    # -------------------------------------------------------------------------
    # Example: Generic Helpers (existing code)
    # -------------------------------------------------------------------------

    def get_all_nodes_of_label(self, label: str) -> list:
        """
        Return all nodes of a given label, with their properties.
        """
        query = f"""
            MATCH (n:{label})
            RETURN properties(n) AS props
        """
        results = self.run_query(query)
        return [record["props"] for record in results]

    def search_nodes_by_property(
        self, 
        label: str, 
        property_name: str, 
        property_value: str
    ) -> list:
        """
        Search for nodes of a given label by a string property match.
        """
        query = f"""
            MATCH (n:{label})
            WHERE toLower(n.{property_name}) CONTAINS toLower($value)
            RETURN properties(n) as props
        """
        params = {"value": property_value}
        results = self.run_query(query, params)
        return [r["props"] for r in results]

    # -------------------------------------------------------------------------
    # NEW: Narrative & Momentum Methods
    # -------------------------------------------------------------------------

    def create_plotpoint(self, plotpoint_id: int, volatility: float = 1.0, **kwargs):
        """
        Merge a PlotPoint node with given ID (unique in your system),
        a volatility factor, and any additional properties from kwargs.
        """
        set_clauses = [f"pp.volatility = $volatility"]
        for k in kwargs:
            set_clauses.append(f"pp.{k} = ${k}")
        set_statement = ", ".join(set_clauses)
        
        query = f"""
            MERGE (pp:PlotPoint {{plotpoint_id: $plotpoint_id}})
            SET {set_statement}
            RETURN pp
        """
        params = {"plotpoint_id": plotpoint_id, "volatility": volatility}
        for k, v in kwargs.items():
            params[k] = v
        
        self.run_query(query, params)
        logging.info(f"PlotPoint created/updated with ID={plotpoint_id}, volatility={volatility}")

    def link_action_to_plotpoint(self, action_id: int, plotpoint_id: int, weight: float):
        """
        Create or merge an IMPACTS relationship between an Action node and a PlotPoint.
        """
        query = """
            MATCH (a:Action {action_id: $action_id}), (pp:PlotPoint {plotpoint_id: $plotpoint_id})
            MERGE (a)-[r:IMPACTS]->(pp)
            SET r.weight = $weight
            RETURN r
        """
        params = {
            "action_id": action_id,
            "plotpoint_id": plotpoint_id,
            "weight": weight
        }
        self.run_query(query, params)
        logging.info(f"Action {action_id} linked to PlotPoint {plotpoint_id} with weight={weight}")

    def create_action_node(self, action_id: int, session_id: int, text: str, severity: float = 1.0):
        """
        Merge an Action node identified by action_id with relevant properties.
        """
        query = """
            MERGE (a:Action {action_id: $action_id})
            SET a.session_id = $session_id,
                a.text = $text,
                a.timestamp = timestamp(),
                a.severity = $severity
            RETURN a
        """
        params = {
            "action_id": action_id,
            "session_id": session_id,
            "text": text,
            "severity": severity
        }
        self.run_query(query, params)
        logging.info(f"Action node created/updated, ID={action_id}, session={session_id}")

    def attach_player_to_action(self, player_id: int, action_id: int):
        """
        Optional: link an existing Player node to an Action node via :PERFORMED or similar.
        """
        query = """
            MATCH (p:Player {player_id: $player_id}), (a:Action {action_id: $action_id})
            MERGE (p)-[r:PERFORMED]->(a)
            RETURN r
        """
        params = {
            "player_id": player_id,
            "action_id": action_id
        }
        self.run_query(query, params)
        logging.info(f"Player {player_id} linked with Action {action_id}")

    def calculate_session_momentum(self, session_id: int) -> float:
        """
        Calculates total momentum by summing (weight * volatility) on (Action)-[:IMPACTS]->(PlotPoint).
        """
        query = """
            MATCH (a:Action)-[r:IMPACTS]->(pp:PlotPoint)
            WHERE a.session_id = $session_id
            RETURN sum(r.weight * pp.volatility) AS total_momentum
        """
        results = self.run_query(query, {"session_id": session_id})
        if results and results[0]["total_momentum"] is not None:
            val = results[0]["total_momentum"]
            return float(val)
        return 0.0

    def cascade_triggers(self, session_id: int, threshold: float):
        """
        If any PlotPoint's 'momentum' crosses threshold, automatically link to a 'MajorEvent' node.
        This is just an example of auto-trigger logic.
        """
        query = """
            MATCH (a:Action {session_id: $session_id})-[r:IMPACTS]->(pp:PlotPoint)
            WITH pp, sum(r.weight * pp.volatility) AS momentum
            WHERE momentum > $threshold
            MERGE (pp)-[tr:ACTIVATES]->(me:MajorEvent {name: 'AutoTriggeredEvent'})
            RETURN pp, me
        """
        self.run_query(query, {"session_id": session_id, "threshold": threshold})
        logging.info(f"Cascade triggers executed for session {session_id} with threshold={threshold}")

    def decay_relationships(self, decay_rate: float = 0.1):
        """
        Example that reduces the weight of IMPACTS relationships globally,
        or you could parameterize by session or time-based logic.
        """
        query = """
            MATCH ()-[r:IMPACTS]->()
            SET r.weight = r.weight - $decay
            WHERE r.weight < 0
            DELETE r
        """
        params = {"decay": decay_rate}
        self.run_query(query, params)
        logging.info(f"Decayed IMPACTS relationships by {decay_rate}; removed any that fell below 0.")
