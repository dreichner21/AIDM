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
    # Example: NPC Node Operations
    # -------------------------------------------------------------------------

    def create_npc_node(self, npc_id: int, name: str, role: str) -> None:
        """
        Merge (create if not exists) an NPC node in the graph with properties.
        
        Args:
            npc_id (int): Unique ID (from your SQL DB) for the NPC.
            name (str): Display name of the NPC.
            role (str): Role or short description (e.g. "Wizard").
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
        
        Args:
            npc_id (int): The ID of the NPC to look up.

        Returns:
            dict: The node's properties as a dictionary, or {} if not found.
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
        
        Args:
            npc_id (int): The ID of the NPC to update.
            name (str): New name (optional).
            role (str): New role (optional).
        """
        # We only SET the fields that are actually provided
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

        Args:
            npc_id (int): The ID of the NPC to delete.
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
        This includes relationships in both directions.
        
        Args:
            npc_id (int): The ID of the NPC whose relationships we want.

        Returns:
            list: A list of dictionaries, each containing 'relationship' and 'node' keys.
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
    # Relationship Methods
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
        
        If the nodes or relationship do not exist, they will be created or merged.

        Args:
            start_label (str): The label of the start node (e.g., 'NPC').
            start_key (int): The ID property for the start node (usually npc_id).
            end_label (str): The label of the end node (e.g., 'NPC').
            end_key (int): The ID property for the end node (usually npc_id).
            rel_type (str): The type of the relationship to MERGE (e.g., 'ALLY_OF').
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
        Does NOT delete the nodes themselves.
        
        Args:
            start_label (str): The label of the start node (e.g., 'NPC').
            start_key (int): The ID property for the start node.
            end_label (str): The label of the end node (e.g., 'NPC').
            end_key (int): The ID property for the end node.
            rel_type (str): The exact relationship type to remove (e.g., 'ALLY_OF').
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
    # Example: Generic Helpers
    # -------------------------------------------------------------------------

    def get_all_nodes_of_label(self, label: str) -> list:
        """
        Return all nodes of a given label, with their properties.

        Args:
            label (str): The Neo4j label to match (e.g. 'NPC').

        Returns:
            list of dict: Each dict contains the node's properties.
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
        This example uses a case-insensitive partial match (contains).
        
        Args:
            label (str): The Neo4j label to match (e.g. 'NPC').
            property_name (str): The property name to filter on (e.g. 'name').
            property_value (str): The substring to search in that property.

        Returns:
            list: A list of matching node properties as dictionaries.
        """
        # For partial matches, we can use `(?i).*<value>.*` for case-insensitive
        # You might also consider a fulltext index or a more advanced query in production.
        query = f"""
            MATCH (n:{label})
            WHERE toLower(n.{property_name}) CONTAINS toLower($value)
            RETURN properties(n) as props
        """
        params = {"value": property_value}
        results = self.run_query(query, params)
        return [r["props"] for r in results]
