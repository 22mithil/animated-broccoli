import logging
from neo4j import GraphDatabase
# from sentence_transformers import SentenceTransformer


class KnowledgeGraphTester:
    def __init__(self, uri: str, user: str, password: str, embedding_model="BAAI/bge-large-en-v1.5"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        # self.model = SentenceTransformer(embedding_model)
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    def close(self):
        if self.driver:
            self.driver.close()

    # -------------------
    # 1. BASIC QUERIES
    # -------------------
    def get_stats(self):
        with self.driver.session() as session:
            nodes = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
            rels = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")

            print("\n=== Node Counts ===")
            for r in nodes:
                print(f"{r['label']}: {r['count']}")

            print("\n=== Relationship Counts ===")
            for r in rels:
                print(f"{r['type']}: {r['count']}")

    def list_movies(self):
        with self.driver.session() as session:
            movies = session.run("MATCH (m:Movie) RETURN m.id as id, m.title as title, m.year as year")
            print("\n=== Movies in DB ===")
            for m in movies:
                print(f"{m['id']} | {m['title']} ({m['year']})")

    def list_nodes_for_movie(self, movie_id: str):
        with self.driver.session() as session:
            query = """
            MATCH (m:Movie {id: $movie_id})
            OPTIONAL MATCH (m)-[*1..2]-(c:Character)
            OPTIONAL MATCH (m)-[*1..2]-(s:Scene)
            OPTIONAL MATCH (m)-[*1..2]-(l:Location)
            OPTIONAL MATCH (m)-[*1..2]-(o:Object)
            RETURN collect(DISTINCT c.name) as characters,
                   collect(DISTINCT s.id) as scenes,
                   collect(DISTINCT l.name) as locations,
                   collect(DISTINCT o.name) as objects
            """
            res = session.run(query, movie_id=movie_id).single()
            print(f"\n=== Nodes linked to Movie {movie_id} ===")
            print("Characters:", res["characters"])
            print("Scenes:", res["scenes"])
            print("Locations:", res["locations"])
            print("Objects:", res["objects"])

    # -------------------
    # 2. CONNECTIVITY TEST
    # -------------------
    def check_full_connectivity(self, movie_id: str):
        with self.driver.session() as session:
            query = """
            MATCH (m:Movie {id: $movie_id})
            CALL apoc.path.subgraphAll(m, {relationshipFilter:'>', minLevel:0}) YIELD nodes
            WITH collect(nodes) AS reachable
            MATCH (n)
            WHERE NOT n IN reachable[0]
            RETURN collect(labels(n)[0] + ':' + coalesce(n.id, n.title, n.name, elementId(n))) AS disconnected
            """
            res = session.run(query, movie_id=movie_id).single()
            disconnected = res["disconnected"]
            if disconnected and len(disconnected) > 0:
                print(f"\n⚠️ Some nodes are NOT connected to Movie {movie_id}:")
                for d in disconnected:
                    print(" -", d)
            else:
                print(f"\n✅ All nodes are connected (directly or indirectly) to Movie {movie_id}")

    # -------------------
    # 3. SEMANTIC SEARCH
    # -------------------
    # def encode_query(self, text: str):
    #     """
    #     Encode natural language text into embedding using BGE model.
    #     """
    #     emb = self.model.encode(text, normalize_embeddings=True).tolist()
    #     return emb

    # def semantic_search(self, text_query: str, label="Scene", top_k=5):
    #     """
    #     Run semantic similarity search on nodes with embeddings.
    #     Query is text -> embedding -> Neo4j search.
    #     """
    #     index_map = {
    #         "Scene": "scene_embeddings",
    #         "Character": "character_embeddings",
    #         "Location": "location_embeddings",
    #         "Object": "object_embeddings",
    #         "Movie": "movie_embeddings"
    #     }
    #     index_name = index_map.get(label, "scene_embeddings")

    #     query_embedding = self.encode_query(text_query)

    #     if label == "Movie":
    #         cypher = f"""
    #         CALL db.index.vector.queryNodes('{index_name}', $top_k, $embedding)
    #         YIELD node, score
    #         RETURN node.id as id, node.title as title, node.year as year,
    #                node.themes as themes, node.plot_summary as summary,
    #                score
    #         """
    #     else:
    #         cypher = f"""
    #         CALL db.index.vector.queryNodes('{index_name}', $top_k, $embedding)
    #         YIELD node, score
    #         RETURN node.id as id, labels(node)[0] as label, score,
    #                coalesce(node.name, node.title, node.summary, "") as text
    #         """

    #     with self.driver.session() as session:
    #         results = session.run(cypher, top_k=top_k, embedding=query_embedding)

    #         print(f"\n=== Semantic Search: '{text_query}' (Top {top_k} {label}s) ===")
    #         for r in results:
    #             if label == "Movie":
    #                 print(f"[Movie] {r['id']} | {r['title']} ({r['year']}) | score={r['score']:.4f}")
    #                 print("Themes:", r["themes"])
    #                 print("Summary:", r["summary"][:200] + "..." if r["summary"] else "")
    #                 print("-" * 80)
    #             else:
    #                 print(f"[{r['label']}] {r['id']} | score={r['score']:.4f} | {r['text']}")


def main():
    NEO4J_URI = "neo4j+s://934bb46e.databases.neo4j.io"
    NEO4J_USER = "934bb46e"
    NEO4J_PASSWORD = "zbI5ka8n4RdbPsmPr2rMJrKPwTtIZ7AMKpGqtbXMM44"

    tester = KnowledgeGraphTester(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Basic Stats
        tester.get_stats()
        # tester.list_movies()

        # Example: pick Harry Potter movie
        movie_id = "movie_harry_potter_1"
        # tester.list_nodes_for_movie(movie_id)
        tester.check_full_connectivity(movie_id)

        # # Semantic search examples
        # tester.semantic_search("romantic scene in the rain", label="Scene", top_k=5)
        # tester.semantic_search("main protagonist", label="Character", top_k=5)
        # tester.semantic_search("battlefield location", label="Location", top_k=5)
        # tester.semantic_search("magic school adventure", label="Movie", top_k=3)

    finally:
        tester.close()


if __name__ == "__main__":
    main()
