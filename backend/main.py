from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import logging
from neo4j import GraphDatabase
import numpy as np
import httpx
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
import json
import uvicorn
from dotenv import load_dotenv
from config.database import Database
from models.chat import Message, ChatSession
from datetime import datetime
from bson import ObjectId

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)    

app = FastAPI(title="MediaGraphAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    original_query: str
    enhanced_query: str
    detected_label: str
    results: List[Dict[str, Any]]
    response: str

class EmbeddingRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: List[float]

# Configuration
class Config:
    # Environment variables
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MONGODB_URL = os.getenv("MONGODB_URL")
    EMBEDDING_SERVICE_URL = "http://localhost:8005/embed"
    
    # Model configuration
    TOP_K_RESULTS = 5
print(Config.GEMINI_API_KEY)
print(Config.NEO4J_URI)
print(Config.NEO4J_USER)
print(Config.NEO4J_PASSWORD)
# Initialize services
class ServiceManager:
    def __init__(self):
        self.neo4j_driver = None
        self.gemini_configured = False
        self.http_client = None
    
    async def initialize_services(self):
        try:
            # Initialize Neo4j
            self.neo4j_driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
            )
            logger.info("Neo4j connection initialized")
            
            # Initialize MongoDB
            await Database.connect_db(Config.MONGODB_URL)
            logger.info("MongoDB connection initialized")
            
            # Initialize HTTP client for embedding service
            self.http_client = httpx.AsyncClient(timeout=30.0)
            logger.info("HTTP client initialized for embedding service")
            
            # Configure Gemini
            if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "your-gemini-api-key":
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self.gemini_configured = True
                logger.info("Gemini API configured")
            else:
                logger.warning("Gemini API key not configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    async def close(self):
        if self.http_client:
            await self.http_client.aclose()
        if self.neo4j_driver:
            self.neo4j_driver.close()
        await Database.close_db()

# Global service manager
services = ServiceManager()

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await services.initialize_services()

# Hardcoded Cypher queries for each label
# Definitive Cypher queries based on the visual graph schema
CYPHER_QUERIES = {
    "movie": """
        // Find the Movie node by its unique elementId
        MATCH (m:Movie)
        WHERE elementId(m) = $node_id

        // A Movie CONTAINS Scenes. We find other entities through the scenes.
        OPTIONAL MATCH (m)-[:CONTAINS]->(s:Scene)
        OPTIONAL MATCH (s)-[:APPEARS_IN]->(c:Character)
        OPTIONAL MATCH (s)-[:TAKES_PLACE_IN]->(l:Location)

        // Return the movie and collected lists of all related nodes
        RETURN m,
               collect(DISTINCT s) AS scenes,
               collect(DISTINCT c) AS characters,
               collect(DISTINCT l) AS locations
    """,

    "character": """
        // Find the Character node by its unique elementId
        MATCH (c:Character)
        WHERE elementId(c) = $node_id

        // Find which scenes the character appears in, and through that, the movie
        OPTIONAL MATCH (m:Movie)-[:CONTAINS]->(s:Scene)-[:APPEARS_IN]->(c)
        
        // Find other characters this one REPRESENTS or RELATES_TO
        OPTIONAL MATCH (c)-[:REPRESENTS]->(represented:Character)
        OPTIONAL MATCH (c)-[:RELATES_TO]-(related_char:Character)
        
        // Find related objects and locations
        OPTIONAL MATCH (c)-[:RELATES_TO]-(o:Object)
        OPTIONAL MATCH (c)-[:RELATES_TO]-(l:Location)

        // Return the character and collected lists of all related nodes
        RETURN c,
               m AS movie,
               collect(DISTINCT s) AS scenes,
               collect(DISTINCT represented) AS represents,
               // Combining related characters from both directions
               collect(DISTINCT related_char) + collect(DISTINCT represented) AS related_characters,
               collect(DISTINCT o) AS related_objects,
               collect(DISTINCT l) AS related_locations
    """,

    "scene": """
        // Find the Scene node by its unique elementId
        MATCH (s:Scene)
        WHERE elementId(s) = $node_id

        // Find the movie that contains this scene
        OPTIONAL MATCH (m:Movie)-[:CONTAINS]->(s)
        
        // Find characters, locations, and objects related to this scene
        OPTIONAL MATCH (s)-[:APPEARS_IN]->(c:Character)
        OPTIONAL MATCH (s)-[:TAKES_PLACE_IN]->(l:Location)
        OPTIONAL MATCH (s)-[:IN_SCENE]->(o:Object)

        // Return the scene and collected lists of all related nodes
        RETURN s,
               m AS movie,
               collect(DISTINCT c) AS characters,
               collect(DISTINCT l) AS locations,
               collect(DISTINCT o) AS objects
    """,

    "location": """
        // Find the Location node by its unique elementId
        MATCH (l:Location)
        WHERE elementId(l) = $node_id

        // Find scenes that take place in this location
        OPTIONAL MATCH (s:Scene)-[:TAKES_PLACE_IN]->(l)
        
        // Find characters explored by this location (Note: unusual direction)
        OPTIONAL MATCH (l)-[:EXPLORES]->(c:Character)
        
        // Find sub-locations (e.g., Paris CONTAINS Eiffel Tower)
        OPTIONAL MATCH (l)-[:CONTAINS]->(sub_location:Location)

        // Return the location and collected lists of all related nodes
        RETURN l,
               collect(DISTINCT s) AS scenes,
               collect(DISTINCT c) AS characters_explored,
               collect(DISTINCT sub_location) AS sub_locations
    """,

    "object": """
        // Find the Object node by its unique elementId
        MATCH (o:Object)
        WHERE elementId(o) = $node_id

        // Find scenes this object is in
        OPTIONAL MATCH (s:Scene)-[:IN_SCENE]->(o)
        
        // Find characters related to this object
        OPTIONAL MATCH (o)-[:RELATES_TO]->(c:Character)
        
        // Find sub-objects (e.g., Box CONTAINS Key)
        OPTIONAL MATCH (o)-[:CONTAINS]->(sub_object:Object)

        // Return the object and the scenes it's contained in
        RETURN o,
               collect(DISTINCT s) AS scenes,
               collect(DISTINCT c) AS related_characters,
               collect(DISTINCT sub_object) AS sub_objects
    """
}
class EmbeddingService:
    @staticmethod
    async def get_embedding(text: str) -> np.ndarray:
        """Get embedding for text using external embedding service"""
        try:
            embedding_request = EmbeddingRequest(text=text)
            
            response = await services.http_client.post(
                Config.EMBEDDING_SERVICE_URL,
                json=embedding_request.dict(),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"Embedding service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=502, 
                    detail=f"Embedding service unavailable: {response.status_code}"
                )
            
            embedding_response = EmbeddingResponse(**response.json())
            return np.array(embedding_response.embedding)
            
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to embedding service: {e}")
            raise HTTPException(
                status_code=503, 
                detail="Embedding service unavailable"
            )
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate embedding"
            )

class QueryProcessor:
    @staticmethod
    async def enhance_query_with_gemini(query: str) -> str:
        """Enhance the user query using Gemini"""
        if not services.gemini_configured:
            return query
            
        try:
            model = genai.GenerativeModel(model_name='gemini-2.5-flash')
            prompt = f"""
            Enhance this movie search query to be more specific and detailed while keeping the original intent:
            
            Original query: "{query}"
            
            Please provide an enhanced version that:
            1. Clarifies vague terms
            2. Adds relevant context
            3. Makes it more searchable
            4. Keeps it concise (max 2 sentences)
            
            Enhanced query:
            """
            
            response = model.generate_content(prompt)
            enhanced = response.text.strip()
            return enhanced if enhanced else query
            
        except Exception as e:
            logger.error(f"Failed to enhance query with Gemini: {e}")
            return query
    
    @staticmethod
    async def classify_query_label(query: str) -> str:
        """Classify the query into one of the predefined labels"""
        if not services.gemini_configured:
            # Fallback classification based on keywords
            query_lower = query.lower()
            if any(word in query_lower for word in ['movie', 'film', 'cinema']):
                return 'movie'
            elif any(word in query_lower for word in ['character', 'protagonist', 'hero', 'villain']):
                return 'character'
            elif any(word in query_lower for word in ['scene', 'sequence', 'moment']):
                return 'scene'
            elif any(word in query_lower for word in ['location', 'place', 'setting']):
                return 'location'
            elif any(word in query_lower for word in ['object', 'item', 'thing']):
                return 'object'
            else:
                return 'movie'  # default
        
        try:
            model = genai.GenerativeModel(model_name='gemini-2.5-flash')
            prompt = f"""
            Classify this movie-related query into exactly one of these categories:
            - movie: queries about films, movies, or overall stories
            - character: queries about people, protagonists, villains, or characters
            - scene: queries about specific scenes, sequences, or moments
            - location: queries about places, settings, or locations
            - object: queries about specific objects, items, or things that appear in movies
            
            Query: "{query}"
            
            Respond with only the category name (movie/character/scene/location/object):
            """
            
            response = model.generate_content(prompt)
            label = response.text.strip().lower()
            
            valid_labels = ['movie', 'character', 'scene', 'location', 'object']
            return label if label in valid_labels else 'movie'
            
        except Exception as e:
            logger.error(f"Failed to classify query with Gemini: {e}")
            return 'movie'  # default fallback

class Neo4jService:
    @staticmethod
    def get_embedding_similarity_query(label: str) -> str:
        """Generate Cypher query for embedding similarity search"""
        embedding_fields = {
            'movie': 'plot_summary',
            'character': 'description',
            'scene': 'summary',
            'location': 'description',
            'object': 'significance'
        }
        
        field = embedding_fields.get(label, 'description')
        
        return f"""
        MATCH (n:{label.capitalize()})
        WHERE n.{field} IS NOT NULL
        WITH n, n.{field} as text
        RETURN elementId(n) as node_id, text, n
        """
    
    @staticmethod
    async def search_similar_nodes(query_embedding: np.ndarray, label: str, top_k: int = 5) -> List[Dict]:
        """Search for similar nodes using cosine similarity"""
        try:
            cypher_query = Neo4jService.get_embedding_similarity_query(label)
            
            with services.neo4j_driver.session() as session:
                result = session.run(cypher_query)
                nodes = []
                
                for record in result:
                    text = record['text']
                    if text:
                        # Get embedding for the node text using external service
                        node_embedding = await EmbeddingService.get_embedding(text)
                        
                        # Calculate cosine similarity
                        similarity = np.dot(query_embedding, node_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(node_embedding)
                        )
                        
                        nodes.append({
                            'node_id': record['node_id'],
                            'similarity': float(similarity),
                            'node': {k: v for k, v in dict(record['n']).items() if k != 'embedding'},
                            'text': text
                        })
                
                # Sort by similarity and return top k
                nodes.sort(key=lambda x: x['similarity'], reverse=True)
                return nodes[:top_k]
                
        except Exception as e:
            logger.error(f"Failed to search similar nodes: {e}")
            return []
    
    # In class Neo4jService:

    @staticmethod
    def _remove_embeddings(obj: Any) -> Any:
        """Recursively remove 'embedding' keys from dicts, lists, and Neo4j nodes."""
        if isinstance(obj, dict):
            return {k: Neo4jService._remove_embeddings(v) 
                    for k, v in obj.items() if k != "embedding"}
        elif isinstance(obj, list):
            return [Neo4jService._remove_embeddings(item) for item in obj]
        else:
            try:
                # Handle Neo4j Node or Relationship (castable to dict)
                obj_dict = dict(obj)
                return Neo4jService._remove_embeddings(obj_dict)
            except Exception:
                return obj

    @staticmethod
    async def get_node_details(node_id: str, label: str) -> Dict[str, Any]:
        """Get detailed information about a node using predefined Cypher queries."""
        try:
            cypher_query = CYPHER_QUERIES.get(label)
            if not cypher_query:
                return {}

            with services.neo4j_driver.session() as session:
                result = session.run(cypher_query, node_id=node_id)
                record = result.single()

                if record:
                    # Recursively clean embeddings
                    details = {}
                    for key in record.keys():
                        details[key] = Neo4jService._remove_embeddings(record[key])
                    return details

                return {}
        except Exception as e:
            logger.error(f"Failed to get node details: {e}")
            return {}
        
class ResponseGenerator:
    @staticmethod
    async def generate_response(context: Dict[str, Any], original_query: str) -> str:
        """Generate a natural language response using the context"""
        if not services.gemini_configured:
            return ResponseGenerator._generate_fallback_response(context, original_query)
        
        try:
            model = genai.GenerativeModel(model_name='gemini-2.5-flash')
            context_json = json.dumps(context, indent=2)
            
            prompt = f"""
            Based on the following knowledge graph information, provide a helpful and natural response to the user's query.
            
            User Query: "{original_query}"
            
            Knowledge Graph Context:
            {context_json}
            
            Instructions:
            1. Answer the user's question directly and naturally
            2. Use the specific information from the context
            3. If multiple results are available, mention the most relevant ones
            4. Keep the response conversational and informative
            5. If the context doesn't fully answer the query, acknowledge this
            
            Response:
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate response with Gemini: {e}")
            return ResponseGenerator._generate_fallback_response(context, original_query)
    
    @staticmethod
    def _generate_fallback_response(context: Dict[str, Any], original_query: str) -> str:
        """Generate a simple fallback response when Gemini is not available"""
        if not context:
            return f"I couldn't find specific information related to your query: '{original_query}'"
        
        # Simple template-based response
        response_parts = []
        
        if 'node' in context:
            node = context['node']
            if 'title' in node:
                response_parts.append(f"Found information about '{node['title']}'")
            elif 'name' in node:
                response_parts.append(f"Found information about '{node['name']}'")
        
        if 'characters' in context and context['characters']:
            char_names = [c.get('name', 'Unknown') for c in context['characters'][:3]]
            response_parts.append(f"Characters include: {', '.join(char_names)}")
        
        if 'movies' in context and context['movies']:
            movie_titles = [m.get('title', 'Unknown') for m in context['movies'][:3]]
            response_parts.append(f"Related movies: {', '.join(movie_titles)}")
        
        return '. '.join(response_parts) if response_parts else "Found some relevant information in the knowledge graph."

# API Endpoints
@app.get("/")
async def root():
    return {"message": "MediaGraphAI API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint that also tests embedding service connectivity"""
    embedding_service_status = False
    try:
        # Test embedding service with a simple query
        test_embedding = await EmbeddingService.get_embedding("test")
        embedding_service_status = test_embedding is not None
    except:
        embedding_service_status = False
    
    return {
        "status": "healthy" if all([
            services.neo4j_driver is not None,
            embedding_service_status
        ]) else "degraded",
        "services": {
            "neo4j": services.neo4j_driver is not None,
            "gemini": services.gemini_configured,
            "embedding_service": embedding_service_status,
            "embedding_service_url": Config.EMBEDDING_SERVICE_URL
        }
    }

@app.post("/chat/session")
async def create_chat_session():
    """Create a new chat session"""
    try:
        # Create new session
        session = ChatSession()
        
        # Get database connection
        db = Database.get_db()
        
        # Convert session to dict and insert
        session_dict = session.model_dump(by_alias=True)
        logger.info(f"Creating new chat session with data: {session_dict}")
        
        result = await db.chat_sessions.insert_one(session_dict)
        session.id = result.inserted_id
        
        # Verify the session was created
        created_session = await db.chat_sessions.find_one({"_id": result.inserted_id})
        if not created_session:
            logger.error("Session created but not found in immediate verification")
            raise HTTPException(status_code=500, detail="Failed to verify session creation")
            
        logger.info(f"Successfully created chat session with ID: {result.inserted_id}")
        return session.model_dump(by_alias=True)
        
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")

@app.get("/chat/session/{session_id}")
async def get_chat_session(session_id: str):
    """Get a chat session by ID"""
    try:
        db = Database.get_db()
        try:
            session_object_id = session_id
            logger.info(f"Session object ID: {session_object_id}")
            
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid session ID format")
            
        session = await db.chat_sessions.find_one({"_id": session_object_id})
        logger.info(f"Chat session found: {session}")
    
        if not session:
            logger.info(f"Chat session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, session_id: str = None):
    """Main endpoint to process user queries"""
    try:
        original_query = request.query
        
        # Create user message
        user_message = Message(
            role="user",
            content=original_query
        )
        
        # Step 1: Enhance query with Gemini
        enhanced_query = await QueryProcessor.enhance_query_with_gemini(original_query)
        logger.info(f"Enhanced query: {enhanced_query}")
        
        # Step 2: Classify query label
        detected_label = await QueryProcessor.classify_query_label(enhanced_query)
        logger.info(f"Detected label: {detected_label}")
        
        # Step 3: Generate query embedding using external service
        query_embedding = await EmbeddingService.get_embedding(enhanced_query)
        logger.info(f"Generated embedding with shape: {query_embedding.shape}")
        
        # Step 4: Search for similar nodes
        similar_nodes = await Neo4jService.search_similar_nodes(
            query_embedding, detected_label, Config.TOP_K_RESULTS
        )
        
        if not similar_nodes:
            raise HTTPException(status_code=404, detail="No relevant results found")
        
        # Step 5: Get detailed information for the top result
        top_result = similar_nodes[0]
        node_details = await Neo4jService.get_node_details(
            top_result['node_id'], detected_label
        )
        print("node_details:", node_details)
        # Step 6: Generate response
        response_text = await ResponseGenerator.generate_response(node_details, original_query)
        
        # Create assistant message
        assistant_message = Message(
            role="assistant",
            content=response_text,
            query_metadata={
                "enhanced_query": enhanced_query,
                "detected_label": detected_label,
                "results": similar_nodes
            }
        )
        
        # If session_id is provided, store messages in the session
        if session_id:
            try:
                db = Database.get_db()
                await db.chat_sessions.update_one(
                    {"_id": ObjectId(session_id)},
                    {
                        "$push": {"messages": {
                            "$each": [
                                user_message.model_dump(by_alias=True),
                                assistant_message.model_dump(by_alias=True)
                            ]
                        }},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
            except Exception as e:
                logger.error(f"Failed to update chat session: {e}")
        
        return QueryResponse(
            original_query=original_query,
            enhanced_query=enhanced_query,
            detected_label=detected_label,
            results=similar_nodes,
            response=response_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await services.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)