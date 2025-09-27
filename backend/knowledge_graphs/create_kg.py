import json
import logging
from typing import Dict, List, Any
from neo4j import GraphDatabase
from pathlib import Path


class MovieKnowledgeGraphImporter:
    """
    Import movie knowledge graphs from JSON into Neo4j database
    using pre-computed embeddings (e.g., from BAAI/bge-large-en-v1.5).
    """

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.logger = self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        return logging.getLogger(__name__)

    def close(self):
        if self.driver:
            self.driver.close()

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            self.logger.info("Database cleared")

    def create_indexes(self, embedding_dim: int = 1024):
        """
        Create indexes for IDs and vector indexes for embeddings.
        Adjust embedding_dim to match your BGE embedding size.
        """
        indexes = [
            "CREATE INDEX movie_id IF NOT EXISTS FOR (m:Movie) ON (m.id)",
            "CREATE INDEX character_id IF NOT EXISTS FOR (c:Character) ON (c.id)",
            "CREATE INDEX scene_id IF NOT EXISTS FOR (s:Scene) ON (s.id)",
            "CREATE INDEX location_id IF NOT EXISTS FOR (l:Location) ON (l.id)",
            "CREATE INDEX object_id IF NOT EXISTS FOR (o:Object) ON (o.id)"
        ]

        with self.driver.session() as session:
            for query in indexes:
                try:
                    session.run(query)
                except Exception as e:
                    self.logger.warning(f"Index creation failed: {e}")

            # Vector indexes
            vector_indexes = [
                ("scene_embeddings", "Scene"),
                ("character_embeddings", "Character"),
                ("location_embeddings", "Location"),
                ("object_embeddings", "Object"),
                ("movie_embeddings", "Movie"),
            ]

            for index_name, node_label in vector_indexes:
                try:
                    query = f"""
                    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
                    FOR (n:{node_label})
                    ON (n.embedding)
                    OPTIONS {{
                        indexConfig: {{
                            `vector.dimensions`: {embedding_dim},
                            `vector.similarity_function`: 'cosine'
                        }}
                    }}
                    """
                    session.run(query)
                    self.logger.info(f"Vector index '{index_name}' created for {node_label}")
                except Exception as e:
                    self.logger.warning(f"Vector index creation failed: {e}")

    def create_movie_node(self, session, movie_data: Dict[str, Any]):
        query = """
        MERGE (m:Movie {id: $id})
        SET m.title = $title,
            m.year = $year,
            m.plot_summary = $plot_summary,
            m.themes = $themes,
            m.embedding = $embedding
        """
        session.run(query, **movie_data)

    def create_character_nodes(self, session, characters: List[Dict[str, Any]]):
        query = """
        UNWIND $characters as char
        MERGE (c:Character {id: char.id})
        SET c.name = char.name,
            c.role = char.role,
            c.archetype = char.archetype,
            c.description = char.description,
            c.embedding = char.embedding
        """
        session.run(query, characters=characters)

    def create_scene_nodes(self, session, scenes: List[Dict[str, Any]]):
        query = """
        UNWIND $scenes as scene
        MERGE (s:Scene {id: scene.id})
        SET s.start_timestamp = scene.start_timestamp,
            s.end_timestamp = scene.end_timestamp,
            s.summary = scene.summary,
            s.embedding = scene.embedding
        """
        session.run(query, scenes=scenes)

    def create_location_nodes(self, session, locations: List[Dict[str, Any]]):
        query = """
        UNWIND $locations as location
        MERGE (l:Location {id: location.id})
        SET l.name = location.name,
            l.type = location.type,
            l.description = location.description,
            l.embedding = location.embedding
        """
        session.run(query, locations=locations)

    def create_object_nodes(self, session, objects: List[Dict[str, Any]]):
        query = """
        UNWIND $objects as obj
        MERGE (o:Object {id: obj.id})
        SET o.name = obj.name,
            o.type = obj.type,
            o.significance = obj.significance,
            o.embedding = obj.embedding
        """
        session.run(query, objects=objects)

    def create_relationships(self, session, relationships: List[Dict[str, Any]]):
        for rel in relationships:
            rel_type = rel.get("type", "RELATES_TO")
            source = rel.get("source_id", rel.get("source"))
            target = rel.get("target_id", rel.get("target"))

            query = f"""
            MATCH (a {{id: $source}})
            MATCH (b {{id: $target}})
            MERGE (a)-[r:{rel_type}]->(b)
            """
            session.run(query, source=source, target=target)
    
    def link_scenes_to_movie(self, session, movie_id: str, scenes: List[Dict[str, Any]]):
        """
        Ensure every scene in `scenes` is connected to `movie_id` via CONTAINS.
        """
        for scene in scenes:
            query = """
            MATCH (m:Movie {id: $movie_id})
            MATCH (s:Scene {id: $scene_id})
            MERGE (m)-[:CONTAINS]->(s)
            """
            session.run(query, movie_id=movie_id, scene_id=scene["id"])


    def load_json_file(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def import_movie_graph(self, json_file_path: str, clear_db: bool = False):
        if clear_db:
            self.clear_database()

        # Assuming BGE-large: 1024 dimensions
        self.create_indexes(embedding_dim=1024)

        data = self.load_json_file(json_file_path)

        with self.driver.session() as session:
            if data.get("movie"):
                self.create_movie_node(session, data["movie"])
            if data.get("characters"):
                self.create_character_nodes(session, data["characters"])
            if data.get("scenes"):
                self.create_scene_nodes(session, data["scenes"])
            if data.get("locations"):
                self.create_location_nodes(session, data["locations"])
            if data.get("objects"):
                self.create_object_nodes(session, data["objects"])
            if data.get("relationships"):
                self.create_relationships(session, data["relationships"])

        self.logger.info(f"Imported graph: {json_file_path}")

    def import_multiple_movies(self, json_files: List[str], clear_db: bool = False):
        if clear_db:
            self.clear_database()
        self.create_indexes(embedding_dim=1024)

        for file in json_files:
            try:
                self.import_movie_graph(file, clear_db=False)
            except Exception as e:
                self.logger.error(f"Failed to import {file}: {e}")

    def get_graph_stats(self):
        with self.driver.session() as session:
            node_counts = session.run(
                "MATCH (n) RETURN labels(n)[0] as label, count(n) as count"
            )
            rel_counts = session.run(
                "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count"
            )

            return {
                "nodes": {r["label"]: r["count"] for r in node_counts},
                "relationships": {r["type"]: r["count"] for r in rel_counts},
            }


def main():
    NEO4J_URI = "neo4j+s://934bb46e.databases.neo4j.io"
    NEO4J_USER = "934bb46e"
    NEO4J_PASSWORD = "zbI5ka8n4RdbPsmPr2rMJrKPwTtIZ7AMKpGqtbXMM44"

    importer = MovieKnowledgeGraphImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        json_dir = Path("embeded_graphs")
        files = list(json_dir.glob("*.json"))

        importer.import_multiple_movies([str(f) for f in files], clear_db=True)

        stats = importer.get_graph_stats()
        print("\n=== Graph Stats ===")
        print("Nodes:", stats["nodes"])
        print("Relationships:", stats["relationships"])

    finally:
        importer.close()


if __name__ == "__main__":
    main()
