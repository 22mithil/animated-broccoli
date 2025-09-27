from neo4j import GraphDatabase
import logging

class KnowledgeGraphConnectivityTester:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # Check if GDS is available
        self.has_gds = self._check_gds_availability()
        
    def close(self):
        self.driver.close()
    
    def _check_gds_availability(self):
        """Check if Graph Data Science library is available"""
        try:
            with self.driver.session() as session:
                result = session.run("CALL gds.version() YIELD gdsVersion RETURN gdsVersion")
                version = result.single()
                if version:
                    self.logger.info(f"GDS available, version: {version['gdsVersion']}")
                    return True
        except Exception as e:
            self.logger.info("GDS not available, using standard Cypher queries")
            return False
        return False

    def get_movies(self):
        with self.driver.session() as session:
            result = session.run("MATCH (m:Movie) RETURN m.id as id, m.title as title ORDER BY m.title")
            return [record for record in result]

    def _get_reachable_nodes_gds(self, session, movie_id):
        """Use GDS for finding reachable nodes"""
        try:
            # First, create or get a graph projection
            create_graph_query = """
            CALL gds.graph.project.cypher(
                'connectivity-graph',
                'MATCH (n) WHERE n:Movie OR n:Character OR n:Scene OR n:Location OR n:Object RETURN id(n) AS id, labels(n) AS labels',
                'MATCH (a)-[r]-(b) RETURN id(a) AS source, id(b) AS target'
            )
            YIELD graphName, nodeCount, relationshipCount
            RETURN graphName, nodeCount, relationshipCount
            """
            
            # Check if graph already exists
            try:
                session.run("CALL gds.graph.drop('connectivity-graph')")
            except:
                pass  # Graph doesn't exist, that's fine
            
            session.run(create_graph_query)
            
            # Find reachable nodes using DFS
            reachable_query = """
            MATCH (m:Movie {id: $movie_id})
            CALL gds.dfs.stream('connectivity-graph', {sourceNode: id(m)})
            YIELD nodeId
            MATCH (n) WHERE id(n) = nodeId
            RETURN collect(DISTINCT n.id) as reachableNodeIds
            """
            
            result = session.run(reachable_query, movie_id=movie_id)
            reachable_nodes = result.single()["reachableNodeIds"]
            
            # Clean up
            session.run("CALL gds.graph.drop('connectivity-graph')")
            
            return reachable_nodes
            
        except Exception as e:
            self.logger.warning(f"GDS query failed: {e}, falling back to standard Cypher")
            return self._get_reachable_nodes_cypher(session, movie_id)

    def _get_reachable_nodes_cypher(self, session, movie_id):
        """Use standard Cypher for finding reachable nodes"""
        reachable_query = """
        MATCH (m:Movie {id: $movie_id})
        MATCH (m)-[*0..20]-(reachable)
        RETURN collect(DISTINCT reachable.id) as reachableNodeIds
        """
        result = session.run(reachable_query, movie_id=movie_id)
        return result.single()["reachableNodeIds"]

    def _get_wcc_components_gds(self, session):
        """Use GDS for weakly connected components"""
        try:
            # Create graph projection
            try:
                session.run("CALL gds.graph.drop('wcc-graph')")
            except:
                pass
            
            create_graph_query = """
            CALL gds.graph.project.cypher(
                'wcc-graph',
                'MATCH (n) WHERE n:Movie OR n:Character OR n:Scene OR n:Location OR n:Object RETURN id(n) AS id',
                'MATCH (a)-[r]-(b) RETURN id(a) AS source, id(b) AS target'
            )
            """
            session.run(create_graph_query)
            
            # Run WCC
            wcc_query = """
            CALL gds.wcc.stream('wcc-graph')
            YIELD nodeId, componentId
            MATCH (n) WHERE id(n) = nodeId
            RETURN componentId, collect(n.id) as nodes, count(*) as size
            ORDER BY size DESC
            """
            
            result = session.run(wcc_query)
            components = [{"componentId": r["componentId"], "size": r["size"], "nodes": r["nodes"]} for r in result]
            
            # Clean up
            session.run("CALL gds.graph.drop('wcc-graph')")
            
            return components
            
        except Exception as e:
            self.logger.warning(f"GDS WCC failed: {e}, falling back to standard Cypher")
            return self._get_wcc_components_cypher(session)

    def _get_wcc_components_cypher(self, session):
        """Use standard Cypher to find connected components"""
        # Get all nodes
        all_nodes_query = "MATCH (n) RETURN n.id as node_id"
        all_nodes = [r["node_id"] for r in session.run(all_nodes_query)]
        
        visited = set()
        components = []
        component_id = 0
        
        for node_id in all_nodes:
            if node_id not in visited:
                # Find component starting from this node
                component_query = """
                MATCH (start {id: $node_id})
                MATCH (start)-[*0..]-(connected)
                RETURN collect(DISTINCT connected.id) as component_nodes
                """
                try:
                    result = session.run(component_query, node_id=node_id)
                    component_nodes = result.single()["component_nodes"]
                    
                    # Mark all nodes in this component as visited
                    for n in component_nodes:
                        visited.add(n)
                    
                    components.append({
                        "componentId": component_id,
                        "size": len(component_nodes),
                        "nodes": component_nodes
                    })
                    component_id += 1
                    
                except Exception as e:
                    # If there's an error, treat as isolated node
                    if node_id not in visited:
                        visited.add(node_id)
                        components.append({
                            "componentId": component_id,
                            "size": 1,
                            "nodes": [node_id]
                        })
                        component_id += 1
        
        # Sort by size descending
        components.sort(key=lambda x: x["size"], reverse=True)
        return components

    def test_connectivity_for_movie(self, movie_id):
        with self.driver.session() as session:
            # Find reachable nodes from the movie
            if self.has_gds:
                reachable_nodes = self._get_reachable_nodes_gds(session, movie_id)
            else:
                reachable_nodes = self._get_reachable_nodes_cypher(session, movie_id)

            # Find all nodes not reachable from this movie
            disconnected_query = """
            MATCH (n)
            WHERE NOT n.id IN $reachable_nodes
            RETURN n.id as id, labels(n) as labels
            ORDER BY labels(n)[0], n.id
            """
            disconnected = session.run(disconnected_query, reachable_nodes=reachable_nodes)
            disconnected_nodes = [{"id": r["id"], "labels": r["labels"]} for r in disconnected]

            # Weakly Connected Components
            if self.has_gds:
                wcc_components = self._get_wcc_components_gds(session)
            else:
                wcc_components = self._get_wcc_components_cypher(session)

            # Overall graph connectivity metrics
            stats_query = """
            MATCH (n)
            WITH count(n) as totalNodes
            MATCH ()-[r]-()
            WITH totalNodes, count(DISTINCT r) as totalEdges
            RETURN totalNodes, totalEdges,
                   CASE WHEN totalEdges >= totalNodes - 1 THEN 'Potentially Connected'
                        ELSE 'Definitely Disconnected' END as status
            """
            stats = session.run(stats_query).single()

            return {
                "movie_id": movie_id,
                "reachable_count": len(reachable_nodes),
                "reachable_nodes": reachable_nodes,
                "disconnected_nodes": disconnected_nodes,
                "wcc_components": wcc_components,
                "graph_stats": dict(stats) if stats else {}
            }

    def analyze_graph_structure(self):
        """Analyze overall graph structure"""
        with self.driver.session() as session:
            # Node type distribution
            node_types_query = """
            MATCH (n)
            RETURN labels(n)[0] as node_type, count(n) as count
            ORDER BY count DESC
            """
            node_types = [{"type": r["node_type"], "count": r["count"]} 
                         for r in session.run(node_types_query)]
            
            # Relationship type distribution
            rel_types_query = """
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            """
            rel_types = [{"type": r["rel_type"], "count": r["count"]} 
                        for r in session.run(rel_types_query)]
            
            # Find isolated nodes (no connections)
            isolated_query = """
            MATCH (n)
            WHERE NOT (n)-[]-()
            RETURN n.id as node_id, labels(n)[0] as node_type
            ORDER BY node_type, node_id
            """
            isolated_nodes = [{"id": r["node_id"], "type": r["node_type"]} 
                            for r in session.run(isolated_query)]
            
            return {
                "node_types": node_types,
                "relationship_types": rel_types,
                "isolated_nodes": isolated_nodes
            }


def main():
    NEO4J_URI = "neo4j+s://934bb46e.databases.neo4j.io"
    NEO4J_USER = "934bb46e"
    NEO4J_PASSWORD = "zbI5ka8n4RdbPsmPr2rMJrKPwTtIZ7AMKpGqtbXMM44"

    tester = KnowledgeGraphConnectivityTester(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        print("=== KNOWLEDGE GRAPH CONNECTIVITY ANALYSIS ===\n")
        
        # Overall graph structure
        print("1. GRAPH STRUCTURE ANALYSIS")
        print("-" * 40)
        structure = tester.analyze_graph_structure()
        
        print("Node Types:")
        for node_type in structure["node_types"]:
            print(f"  {node_type['type']}: {node_type['count']}")
        
        print("\nRelationship Types:")
        for rel_type in structure["relationship_types"]:
            print(f"  {rel_type['type']}: {rel_type['count']}")
        
        if structure["isolated_nodes"]:
            print(f"\nIsolated Nodes (no connections): {len(structure['isolated_nodes'])}")
            for node in structure["isolated_nodes"][:5]:
                print(f"  {node['type']}: {node['id']}")
            if len(structure["isolated_nodes"]) > 5:
                print(f"  ... and {len(structure['isolated_nodes']) - 5} more")
        else:
            print("\nIsolated Nodes: None")
        
        print("\n" + "="*50 + "\n")
        
        # Movie-specific connectivity
        movies = tester.get_movies()
        print(f"2. MOVIE CONNECTIVITY ANALYSIS")
        print("-" * 40)
        print(f"Found {len(movies)} movies in database:\n")
        
        for movie in movies:
            print(f"--- Testing Movie: {movie['title']} ({movie['id']}) ---")
            results = tester.test_connectivity_for_movie(movie["id"])

            print(f"Reachable nodes count: {results['reachable_count']}")
            
            if results["disconnected_nodes"]:
                print(f"⚠️ Disconnected nodes: {len(results['disconnected_nodes'])}")
                # Group by node type for better readability
                by_type = {}
                for node in results["disconnected_nodes"]:
                    node_type = node['labels'][0] if node['labels'] else 'Unknown'
                    by_type.setdefault(node_type, []).append(node['id'])
                
                for node_type, ids in by_type.items():
                    print(f"   {node_type}: {len(ids)} nodes")
                    for node_id in ids[:3]:  # Show first 3 of each type
                        print(f"     - {node_id}")
                    if len(ids) > 3:
                        print(f"     ... and {len(ids) - 3} more")
            else:
                print("✅ All nodes are connected to this movie")

            print(f"Graph Stats: Total nodes: {results['graph_stats'].get('totalNodes', 'N/A')}, "
                  f"Total edges: {results['graph_stats'].get('totalEdges', 'N/A')}, "
                  f"Status: {results['graph_stats'].get('status', 'N/A')}")
            
            print(f"Connected Components: {len(results['wcc_components'])}")
            if len(results['wcc_components']) > 1:
                print("  Component sizes:", [comp['size'] for comp in results['wcc_components'][:5]])
            
            print()

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.close()


if __name__ == "__main__":
    main()