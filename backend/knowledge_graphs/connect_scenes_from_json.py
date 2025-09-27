# connect_scenes_from_json.py

import json
from pathlib import Path
from neo4j import GraphDatabase
import logging

# ----------------------------
# Configuration
# ----------------------------
NEO4J_URI = "neo4j+s://934bb46e.databases.neo4j.io"
NEO4J_USER = "934bb46e"
NEO4J_PASSWORD = "zbI5ka8n4RdbPsmPr2rMJrKPwTtIZ7AMKpGqtbXMM44"
JSON_DIR = Path("embeded_graphs")  # Folder containing JSON files

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ----------------------------
# Neo4j Connection
# ----------------------------
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def connect_scenes_from_json():
    json_files = list(JSON_DIR.glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in {JSON_DIR}")
        return

    with driver.session() as session:
        for json_file in json_files:
            data = load_json(json_file)
            movie = data.get("movie")
            scenes = data.get("scenes", [])

            if not movie:
                logger.warning(f"No movie node found in {json_file}, skipping.")
                continue

            movie_id = movie["id"]
            logger.info(f"Processing movie {movie.get('title', movie_id)} ({movie_id})")

            # Get list of scene IDs from JSON
            scene_ids = [scene["id"] for scene in scenes]

            # Find which scenes are not connected to this movie yet
            query = """
            UNWIND $scene_ids AS sid
            MATCH (s:Scene {id: sid})
            WHERE NOT ( (s)-[]-(:Movie {id: $movie_id}) )
            RETURN s.id AS orphan_scene_id
            """
            result = session.run(query, movie_id=movie_id, scene_ids=scene_ids)
            orphan_scenes = [record["orphan_scene_id"] for record in result]

            if not orphan_scenes:
                logger.info(f"All scenes already connected for movie {movie.get('title', movie_id)}")
                continue

            logger.info(f"Connecting {len(orphan_scenes)} orphan scenes to movie {movie.get('title', movie_id)}")

            # Connect orphan scenes using CONTAINS
            session.run("""
                UNWIND $orphan_scenes AS sid
                MATCH (m:Movie {id: $movie_id})
                MATCH (s:Scene {id: sid})
                MERGE (m)-[:CONTAINS]->(s)
            """, movie_id=movie_id, orphan_scenes=orphan_scenes)

            logger.info(f"Finished connecting scenes for movie {movie.get('title', movie_id)}")


if __name__ == "__main__":
    try:
        connect_scenes_from_json()
        logger.info("Scene connectivity fix from JSON completed!")
    finally:
        driver.close()
