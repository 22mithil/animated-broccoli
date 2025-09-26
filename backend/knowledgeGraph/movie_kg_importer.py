import json
import logging
from typing import Dict, List, Any
from neo4j import GraphDatabase
from pathlib import Path

class MovieKnowledgeGraphImporter:
    """
    Import movie knowledge graphs from JSON into Neo4j database
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j database URI (e.g., 'bolt://localhost:7687')
            user: Database username
            password: Database password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        """Clear all nodes and relationships from the database"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            self.logger.info("Database cleared")
    
    def create_indexes(self):
        """Create indexes for better performance"""
        indexes = [
            "CREATE INDEX movie_id IF NOT EXISTS FOR (m:Movie) ON (m.id)",
            "CREATE INDEX character_id IF NOT EXISTS FOR (c:Character) ON (c.id)",
            "CREATE INDEX scene_id IF NOT EXISTS FOR (s:Scene) ON (s.id)",
            "CREATE INDEX event_id IF NOT EXISTS FOR (e:Event) ON (e.id)",
            "CREATE INDEX location_id IF NOT EXISTS FOR (l:Location) ON (l.id)",
            "CREATE INDEX object_id IF NOT EXISTS FOR (o:Object) ON (o.id)",
            "CREATE INDEX theme_id IF NOT EXISTS FOR (t:Theme) ON (t.id)"
        ]
        
        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    self.logger.info(f"Index created: {index_query.split()[-1]}")
                except Exception as e:
                    self.logger.warning(f"Index creation failed or already exists: {e}")
    
    def create_movie_node(self, session, movie_data: Dict[str, Any]):
        """Create movie node"""
        query = """
        MERGE (m:Movie {id: $id})
        SET m.title = $title,
            m.year = $year,
            m.plot_summary = $plot_summary,
            m.themes = $themes,
            m.mood = $mood
        RETURN m.id as id
        """
        
        result = session.run(query, **movie_data)
        record = result.single()
        if record:
            self.logger.info(f"Created/Updated Movie: {movie_data.get('title', movie_data.get('id'))}")
            return record['id']
        return None
    
    def create_character_nodes(self, session, characters: List[Dict[str, Any]]):
        """Create character nodes in batch"""
        query = """
        UNWIND $characters as char
        MERGE (c:Character {id: char.id})
        SET c.name = char.name,
            c.role = char.role,
            c.archetype = char.archetype,
            c.description = char.description
        RETURN count(c) as created_count
        """
        
        result = session.run(query, characters=characters)
        record = result.single()
        count = record['created_count'] if record else 0
        self.logger.info(f"Created/Updated {count} Character nodes")
        return count
    
    def create_scene_nodes(self, session, scenes: List[Dict[str, Any]]):
        """Create scene nodes in batch"""
        query = """
        UNWIND $scenes as scene
        MERGE (s:Scene {id: scene.id})
        SET s.sequence_number = scene.sequence_number,
            s.summary = scene.summary,
            s.emotional_tone = scene.emotional_tone,
            s.key_quotes = scene.key_quotes
        RETURN count(s) as created_count
        """
        
        result = session.run(query, scenes=scenes)
        record = result.single()
        count = record['created_count'] if record else 0
        self.logger.info(f"Created/Updated {count} Scene nodes")
        return count
    
    def create_event_nodes(self, session, events: List[Dict[str, Any]]):
        """Create event nodes in batch"""
        query = """
        UNWIND $events as event
        MERGE (e:Event {id: event.id})
        SET e.name = event.name,
            e.type = event.type,
            e.description = event.description,
            e.significance = event.significance
        RETURN count(e) as created_count
        """
        
        result = session.run(query, events=events)
        record = result.single()
        count = record['created_count'] if record else 0
        self.logger.info(f"Created/Updated {count} Event nodes")
        return count
    
    def create_location_nodes(self, session, locations: List[Dict[str, Any]]):
        """Create location nodes in batch"""
        query = """
        UNWIND $locations as location
        MERGE (l:Location {id: location.id})
        SET l.name = location.name,
            l.type = location.type,
            l.description = location.description
        RETURN count(l) as created_count
        """
        
        result = session.run(query, locations=locations)
        record = result.single()
        count = record['created_count'] if record else 0
        self.logger.info(f"Created/Updated {count} Location nodes")
        return count
    
    def create_object_nodes(self, session, objects: List[Dict[str, Any]]):
        """Create object nodes in batch"""
        query = """
        UNWIND $objects as obj
        MERGE (o:Object {id: obj.id})
        SET o.name = obj.name,
            o.type = obj.type,
            o.significance = obj.significance
        RETURN count(o) as created_count
        """
        
        result = session.run(query, objects=objects)
        record = result.single()
        count = record['created_count'] if record else 0
        self.logger.info(f"Created/Updated {count} Object nodes")
        return count
    
    def create_theme_nodes(self, session, themes: List[Dict[str, Any]]):
        """Create theme nodes in batch"""
        query = """
        UNWIND $themes as theme
        MERGE (t:Theme {id: theme.id})
        SET t.name = theme.name,
            t.category = theme.category
        RETURN count(t) as created_count
        """
        
        result = session.run(query, themes=themes)
        record = result.single()
        count = record['created_count'] if record else 0
        self.logger.info(f"Created/Updated {count} Theme nodes")
        return count
    
    def create_relationships(self, session, relationships: List[Dict[str, Any]]):
        total_created = 0

        for rel in relationships:
            rel_type = rel.get('type', 'RELATES_TO')
            source = rel.get('source_id', rel.get('source'))
            target = rel.get('target_id', rel.get('target'))
            properties = rel.get('properties', {})

            # Skip empty dicts
            if not isinstance(properties, dict):
                properties = {}
            
            # Build SET clause dynamically
            set_clause = ", ".join([f"r.{k} = $prop_{k}" for k in properties.keys()]) if properties else ""

            query = f"""
            MATCH (source {{id: $source}})
            MATCH (target {{id: $target}})
            MERGE (source)-[r:{rel_type}]->(target)
            """
            if set_clause:
                query += f"\nSET {set_clause}"
            query += "\nRETURN count(r) as created_count"

            # Flatten properties for parameters
            params = {"source": source, "target": target}
            params.update({f"prop_{k}": v for k, v in properties.items()})

            try:
                result = session.run(query, **params)
                record = result.single()
                total_created += record['created_count'] if record else 0
            except Exception as e:
                self.logger.error(f"Error creating relationship {source}->{target}: {e}")

        self.logger.info(f"Total relationships created: {total_created}")
        return total_created

    
    def load_json_file(self, file_path: str) -> Dict[str, Any]:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.logger.info(f"Loaded JSON file: {file_path}")
                return data
        except Exception as e:
            self.logger.error(f"Error loading JSON file {file_path}: {e}")
            raise
    
    def import_movie_graph(self, json_file_path: str, clear_db: bool = False):
        """
        Import a single movie knowledge graph from JSON file
        
        Args:
            json_file_path: Path to the JSON file
            clear_db: Whether to clear the database before import
        """
        if clear_db:
            self.clear_database()
            
        # Create indexes
        self.create_indexes()
        
        # Load JSON data
        data = self.load_json_file(json_file_path)
        
        with self.driver.session() as session:
            # Create nodes
            if 'movie' in data and data['movie']:
                self.create_movie_node(session, data['movie'])
            
            if 'characters' in data and data['characters']:
                self.create_character_nodes(session, data['characters'])
            
            if 'scenes' in data and data['scenes']:
                self.create_scene_nodes(session, data['scenes'])
            
            if 'events' in data and data['events']:
                self.create_event_nodes(session, data['events'])
            
            if 'locations' in data and data['locations']:
                self.create_location_nodes(session, data['locations'])
            
            if 'objects' in data and data['objects']:
                self.create_object_nodes(session, data['objects'])
            
            if 'themes' in data and data['themes']:
                self.create_theme_nodes(session, data['themes'])
            
            # Create relationships
            if 'relationships' in data and data['relationships']:
                total_rels = self.create_relationships(session, data['relationships'])
                self.logger.info(f"Total relationships created: {total_rels}")
        
        self.logger.info(f"Successfully imported movie knowledge graph from {json_file_path}")
    
    def import_multiple_movies(self, json_files: List[str], clear_db: bool = False):
        """
        Import multiple movie knowledge graphs from JSON files
        
        Args:
            json_files: List of JSON file paths
            clear_db: Whether to clear the database before import
        """
        if clear_db:
            self.clear_database()
        
        self.create_indexes()
        
        for json_file in json_files:
            try:
                self.import_movie_graph(json_file, clear_db=False)
                self.logger.info(f"Successfully imported {json_file}")
            except Exception as e:
                self.logger.error(f"Error importing {json_file}: {e}")
                continue
        
        self.logger.info(f"Completed importing {len(json_files)} movie knowledge graphs")
    
    def validate_json_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON data structure and return validation report"""
        report = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        # Expected sections
        expected_sections = ['movie', 'characters', 'scenes', 'events', 'locations', 'objects', 'themes', 'relationships']
        
        # Check for required sections
        for section in expected_sections:
            if section not in data:
                report['warnings'].append(f"Missing section: {section}")
        
        # Collect all entity IDs
        all_ids = set()
        
        # Validate movie
        if 'movie' in data and data['movie']:
            movie = data['movie']
            if 'id' not in movie:
                report['errors'].append("Movie missing 'id' field")
            else:
                all_ids.add(movie['id'])
            report['stats']['movie'] = 1
        
        # Validate entity sections
        entity_sections = ['characters', 'scenes', 'events', 'locations', 'objects', 'themes']
        for section in entity_sections:
            if section in data and data[section]:
                entities = data[section]
                if not isinstance(entities, list):
                    report['errors'].append(f"{section} should be a list")
                    continue
                
                section_ids = set()
                for i, entity in enumerate(entities):
                    if 'id' not in entity:
                        report['errors'].append(f"{section}[{i}] missing 'id' field")
                    else:
                        entity_id = entity['id']
                        if entity_id in section_ids:
                            report['errors'].append(f"Duplicate ID in {section}: {entity_id}")
                        section_ids.add(entity_id)
                        all_ids.add(entity_id)
                
                report['stats'][section] = len(entities)
        
        # Validate relationships
        if 'relationships' in data and data['relationships']:
            relationships = data['relationships']
            if not isinstance(relationships, list):
                report['errors'].append("Relationships should be a list")
            else:
                valid_rel_count = 0
                for i, rel in enumerate(relationships):
                    source_id = rel.get('source_id', rel.get('source'))
                    target_id = rel.get('target_id', rel.get('target'))
                    
                    if not source_id:
                        report['errors'].append(f"relationships[{i}] missing source_id/source field")
                        continue
                    if not target_id:
                        report['errors'].append(f"relationships[{i}] missing target_id/target field")
                        continue
                    
                    if source_id not in all_ids:
                        report['warnings'].append(f"relationships[{i}] source_id '{source_id}' not found in entities")
                    if target_id not in all_ids:
                        report['warnings'].append(f"relationships[{i}] target_id '{target_id}' not found in entities")
                    
                    if 'type' not in rel:
                        report['warnings'].append(f"relationships[{i}] missing 'type' field, will use 'RELATES_TO'")
                    
                    valid_rel_count += 1
                
                report['stats']['relationships'] = valid_rel_count
        
        # Set overall validity
        report['valid'] = len(report['errors']) == 0
        
        return report
    
    def print_validation_report(self, report: Dict[str, Any]):
        """Print a formatted validation report"""
        print("\n=== JSON Data Validation Report ===")
        print(f"Overall Status: {'✅ VALID' if report['valid'] else '❌ INVALID'}")
        
        if report['stats']:
            print("\nEntity Counts:")
            for entity_type, count in report['stats'].items():
                print(f"  {entity_type}: {count}")
        
        if report['errors']:
            print(f"\n❌ Errors ({len(report['errors'])}):")
            for error in report['errors']:
                print(f"  • {error}")
        
        if report['warnings']:
            print(f"\n⚠️  Warnings ({len(report['warnings'])}):")
            for warning in report['warnings']:
                print(f"  • {warning}")
        
        if report['valid'] and not report['warnings']:
            print("\n🎉 Data is ready for import!")

    def get_graph_stats(self):
        """Get statistics about the imported graph"""
        with self.driver.session() as session:
            stats_query = """
            RETURN 
                size(()-[:Movie]->()) as movies,
                size(()-[:Character]->()) as characters,
                size(()-[:Scene]->()) as scenes,
                size(()-[:Event]->()) as events,
                size(()-[:Location]->()) as locations,
                size(()-[:Object]->()) as objects,
                size(()-[:Theme]->()) as themes,
                size(()-[]->()) as total_relationships
            """
            
            node_counts_query = """
            MATCH (n) 
            RETURN labels(n)[0] as label, count(n) as count 
            ORDER BY count DESC
            """
            
            rel_counts_query = """
            MATCH ()-[r]->() 
            RETURN type(r) as relationship_type, count(r) as count 
            ORDER BY count DESC
            """
            
            try:
                # Get node counts
                result = session.run(node_counts_query)
                node_stats = {record['label']: record['count'] for record in result}
                
                # Get relationship counts
                result = session.run(rel_counts_query)
                rel_stats = {record['relationship_type']: record['count'] for record in result}
                
                return {
                    'nodes': node_stats,
                    'relationships': rel_stats
                }
            except Exception as e:
                self.logger.error(f"Error getting graph statistics: {e}")
                return {}


def main():
    """Import all movie knowledge graphs from the graphs/ folder"""
    
    # Neo4j connection details
    NEO4J_URI = "neo4j+s://934bb46e.databases.neo4j.io"
    NEO4J_USER = "934bb46e"
    NEO4J_PASSWORD = "zbI5ka8n4RdbPsmPr2rMJrKPwTtIZ7AMKpGqtbXMM44"
    
    importer = MovieKnowledgeGraphImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Get all JSON files from the graphs folder
        json_directory = Path("corrected_graphs")
        if not json_directory.exists():
            print(f"❌ Directory not found: {json_directory.resolve()}")
            return
        
        json_files = list(json_directory.glob("*.json"))
        if not json_files:
            print(f"❌ No JSON files found in {json_directory.resolve()}")
            return
        
        print(f"\n📂 Found {len(json_files)} JSON files in {json_directory.resolve()} ...")
        
        # Import all movies (clear DB once at the start)
        importer.import_multiple_movies([str(f) for f in json_files], clear_db=True)
        
        # Print statistics after import
        stats = importer.get_graph_stats()
        print("\n=== Knowledge Graph Statistics ===")
        print("Node counts:")
        for label, count in stats.get('nodes', {}).items():
            print(f"  {label}: {count}")
        
        print("\nRelationship counts:")
        for rel_type, count in stats.get('relationships', {}).items():
            print(f"  {rel_type}: {count}")
    
    except Exception as e:
        print(f"Error during import: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        importer.close()



# Quick validation function for convenience
# def validate_json_file(json_file_path: str):
#     """Quickly validate a JSON file without connecting to Neo4j"""
#     try:
#         with open(json_file_path, 'r', encoding='utf-8') as file:
#             data = json.load(file)
        
#         # Create a temporary importer instance just for validation
#         temp_importer = MovieKnowledgeGraphImporter("bolt://localhost:7687", "temp", "temp")
#         report = temp_importer.validate_json_data(data)
#         temp_importer.print_validation_report(report)
#         temp_importer.close()
        
#         return report['valid']
#     except Exception as e:
#         print(f"Error validating JSON file: {e}")
#         return False


if __name__ == "__main__":
    main()