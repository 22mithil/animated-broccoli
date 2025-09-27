from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
from neo4j import GraphDatabase
import numpy as np
import httpx
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
import json
import uvicorn
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MediaGraphAI Chatbot API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    response: str
    session_id: str
    conversation_state: str  
    suggestions: Optional[List[str]] = None
    results: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationContext(BaseModel):
    session_id: str
    original_query: str
    enhanced_queries: List[str] = []
    detected_labels: List[str] = []
    excluded_results: List[int] = [] 
    conversation_history: List[Dict[str, str]] = []
    created_at: datetime
    last_updated: datetime
    current_state: str = "initial"  

class Config:
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    EMBEDDING_SERVICE_URL =  "http://localhost:8005/embed"

    TOP_K_RESULTS = 5
    SESSION_TIMEOUT_HOURS = 24

# In-memory session storage (in production, use Redis or database)
conversation_sessions: Dict[str, ConversationContext] = {}

# Initialize services (same as before)
class ServiceManager:
    def __init__(self):
        self.neo4j_driver = None
        self.gemini_configured = False
        self.http_client = None
        self.initialize_services()
    
    def initialize_services(self):
        try:
            # Initialize Neo4j
            self.neo4j_driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
            )
            logger.info("Neo4j connection initialized")
            
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

services = ServiceManager()

# Session Management
class SessionManager:
    @staticmethod
    def create_session(initial_query: str) -> str:
        session_id = str(uuid.uuid4())
        conversation_sessions[session_id] = ConversationContext(
            session_id=session_id,
            original_query=initial_query,
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        return session_id
    
    @staticmethod
    def get_session(session_id: str) -> Optional[ConversationContext]:
        # Clean up expired sessions
        SessionManager.cleanup_expired_sessions()
        return conversation_sessions.get(session_id)
    
    @staticmethod
    def update_session(session_id: str, updates: Dict[str, Any]):
        if session_id in conversation_sessions:
            context = conversation_sessions[session_id]
            for key, value in updates.items():
                if hasattr(context, key):
                    setattr(context, key, value)
            context.last_updated = datetime.now()
    
    @staticmethod
    def cleanup_expired_sessions():
        cutoff_time = datetime.now() - timedelta(hours=Config.SESSION_TIMEOUT_HOURS)
        expired_sessions = [
            sid for sid, context in conversation_sessions.items()
            if context.last_updated < cutoff_time
        ]
        for sid in expired_sessions:
            del conversation_sessions[sid]

# Enhanced Conversation Agent using Gemini
class ConversationAgent:
    @staticmethod
    async def analyze_user_intent(message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze user intent and determine conversation flow"""
        if not services.gemini_configured:
            return ConversationAgent._fallback_intent_analysis(message, context)
        
        try:
            model = genai.GenerativeModel(model_name='gemini-2.5-flash')
            
            conversation_history = "\n".join([
                f"{entry['role']}: {entry['message']}" 
                for entry in context.conversation_history[-5:]  # Last 5 messages for context
            ])
            
            prompt = f"""
            You are an intelligent movie search assistant. Analyze the user's message and determine the appropriate action.
            
            Conversation Context:
            - Original Query: "{context.original_query}"
            - Previous Enhanced Queries: {context.enhanced_queries}
            - Excluded Results: {len(context.excluded_results)} items
            - Current State: {context.current_state}
            
            Recent Conversation:
            {conversation_history}
            
            Current User Message: "{message}"
            
            Determine the user's intent and provide a JSON response with:
            {{
                "intent": "search_new|refine_search|ask_clarification|negative_feedback|positive_feedback|general_chat",
                "action": "search|clarify|acknowledge|end_conversation",
                "needs_more_info": true/false,
                "search_refinements": ["specific", "refinement", "keywords"],
                "clarifying_questions": ["question1", "question2"],
                "confidence": 0.0-1.0
            }}
            
            Intent Guidelines:
            - search_new: User wants to search for something completely new
            - refine_search: User wants to modify/refine current search (e.g., "not this movie", "something else")
            - ask_clarification: User is asking for more details about results
            - negative_feedback: User indicates results are wrong/not helpful
            - positive_feedback: User is satisfied with results
            - general_chat: User is having casual conversation
            """
            
            response = model.generate_content(prompt)
            return json.loads(response.text.strip())
            
        except Exception as e:
            logger.error(f"Failed to analyze intent with Gemini: {e}")
            return ConversationAgent._fallback_intent_analysis(message, context)
    
    @staticmethod
    def _fallback_intent_analysis(message: str, context: ConversationContext) -> Dict[str, Any]:
        """Fallback intent analysis when Gemini is not available"""
        message_lower = message.lower()
        
        negative_indicators = ['no', 'not', 'wrong', 'different', 'another', 'else', 'not this']
        clarification_indicators = ['tell me more', 'what about', 'details', 'explain']
        positive_indicators = ['yes', 'thanks', 'perfect', 'that\'s it', 'correct']
        
        if any(indicator in message_lower for indicator in negative_indicators):
            return {
                "intent": "negative_feedback",
                "action": "clarify",
                "needs_more_info": True,
                "search_refinements": [],
                "clarifying_questions": ["Can you provide more specific details about what you're looking for?"],
                "confidence": 0.7
            }
        elif any(indicator in message_lower for indicator in positive_indicators):
            return {
                "intent": "positive_feedback",
                "action": "acknowledge",
                "needs_more_info": False,
                "search_refinements": [],
                "clarifying_questions": [],
                "confidence": 0.8
            }
        elif any(indicator in message_lower for indicator in clarification_indicators):
            return {
                "intent": "ask_clarification",
                "action": "clarify",
                "needs_more_info": False,
                "search_refinements": [],
                "clarifying_questions": [],
                "confidence": 0.6
            }
        else:
            return {
                "intent": "refine_search",
                "action": "search",
                "needs_more_info": False,
                "search_refinements": [message],
                "clarifying_questions": [],
                "confidence": 0.5
            }

    @staticmethod
    async def generate_enhanced_query(original_query: str, refinements: List[str], excluded_context: List[str]) -> str:
        """Generate enhanced query with refinements and exclusions"""
        if not services.gemini_configured:
            # Simple fallback
            combined_query = original_query + " " + " ".join(refinements)
            if excluded_context:
                combined_query += " (not: " + ", ".join(excluded_context[:3]) + ")"
            return combined_query
        
        try:
            model = genai.GenerativeModel(model_name='gemini-2.5-flash')
            
            excluded_text = ", ".join(excluded_context[-5:]) if excluded_context else "None"
            refinements_text = ", ".join(refinements) if refinements else "None"
            
            prompt = f"""
            Create an enhanced search query for a movie knowledge graph search.
            
            Original Query: "{original_query}"
            User Refinements: {refinements_text}
            Previously Found (to exclude): {excluded_text}
            
            Instructions:
            1. Combine the original query with refinements
            2. Make it more specific and searchable
            3. Incorporate hints to avoid previously found results
            4. Keep it concise but descriptive
            5. Focus on movie, character, scene, location, or object details
            
            Enhanced Query:
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Failed to enhance query with Gemini: {e}")
            return original_query + " " + " ".join(refinements)

    @staticmethod
    async def generate_clarifying_questions(context: ConversationContext) -> List[str]:
        """Generate clarifying questions to help narrow down search"""
        if not services.gemini_configured:
            return [
                "Can you provide more details about the movie you're looking for?",
                "What genre or time period are you interested in?",
                "Do you remember any specific actors or characters?"
            ]
        
        try:
            model = genai.GenerativeModel(model_name='gemini-2.5-flash')
            
            prompt = f"""
            Generate 2-3 helpful clarifying questions to help narrow down a movie search.
            
            Context:
            - Original Query: "{context.original_query}"
            - Previous Queries: {context.enhanced_queries}
            - Number of Previous Results: {len(context.excluded_results)}
            
            Generate questions that would help identify:
            - Specific movie details
            - Genre, era, or style preferences  
            - Character or plot specifics
            - Any other distinguishing features
            
            Return as a JSON array of strings:
            ["Question 1?", "Question 2?", "Question 3?"]
            """
            
            response = model.generate_content(prompt)
            questions = json.loads(response.text.strip())
            return questions if isinstance(questions, list) else []
            
        except Exception as e:
            logger.error(f"Failed to generate clarifying questions: {e}")
            return [
                "Can you describe more details about what you're looking for?",
                "What specific aspects are most important to you?"
            ]

    @staticmethod
    async def generate_conversational_response(intent_analysis: Dict, context: ConversationContext, results: Optional[List] = None) -> str:
        """Generate natural conversational response based on intent"""
        if not services.gemini_configured:
            return ConversationAgent._fallback_response(intent_analysis, context, results)
        
        try:
            model = genai.GenerativeModel(model_name='gemini-2.5-flash')
            
            results_summary = ""
            if results:
                results_summary = f"Found {len(results)} results. Top result: {results[0].get('node', {}).get('title', 'Unknown')}"
            
            prompt = f"""
            Generate a natural, conversational response for a movie search chatbot.
            
            Context:
            - User Intent: {intent_analysis['intent']}
            - Recommended Action: {intent_analysis['action']}
            - Original Query: "{context.original_query}"
            - Current State: {context.current_state}
            - Search Results: {results_summary}
            - Conversation Length: {len(context.conversation_history)}
            
            Instructions:
            1. Be helpful and conversational
            2. Acknowledge the user's intent appropriately
            3. If search results are available, present them naturally
            4. If clarification is needed, ask follow-up questions
            5. Keep responses concise but informative
            6. Show empathy if user is frustrated
            
            Response:
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate conversational response: {e}")
            return ConversationAgent._fallback_response(intent_analysis, context, results)
    
    @staticmethod
    def _fallback_response(intent_analysis: Dict, context: ConversationContext, results: Optional[List] = None) -> str:
        """Fallback response when Gemini is not available"""
        intent = intent_analysis.get('intent', 'search_new')
        
        if intent == 'negative_feedback':
            return "I understand that wasn't what you were looking for. Can you provide more specific details to help me find the right result?"
        elif intent == 'positive_feedback':
            return "Great! I'm glad I could help you find what you were looking for. Is there anything else you'd like to know?"
        elif intent == 'refine_search':
            if results:
                return f"I found some new results for you. Here's what I found: {results[0].get('node', {}).get('title', 'a relevant match')}"
            else:
                return "Let me search with your additional details..."
        else:
            return "I'm here to help you find information about movies. What would you like to know?"

# Keep existing classes (EmbeddingService, QueryProcessor, Neo4jService, etc.) with modifications
class EmbeddingService:
    @staticmethod
    async def get_embedding(text: str) -> np.ndarray:
        """Get embedding for text using external embedding service"""
        try:
            from pydantic import BaseModel
            
            class EmbeddingRequest(BaseModel):
                text: str
            
            class EmbeddingResponse(BaseModel):
                embedding: List[float]
            
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

# Enhanced Neo4j Service with exclusion support
class Neo4jService:
    @staticmethod
    def get_embedding_similarity_query(label: str, excluded_ids: List[int] = None) -> str:
        """Generate Cypher query for embedding similarity search with exclusions"""
        embedding_fields = {
            'movie': 'plot_summary',
            'character': 'description',
            'scene': 'summary',
            'location': 'description',
            'object': 'significance'
        }
        
        field = embedding_fields.get(label, 'description')
        exclusion_clause = ""
        if excluded_ids:
            exclusion_clause = f"AND NOT id(n) IN {excluded_ids}"
        
        return f"""
        MATCH (n:{label.capitalize()})
        WHERE n.{field} IS NOT NULL {exclusion_clause}
        WITH n, n.{field} as text
        RETURN id(n) as node_id, text, n
        """
    
    @staticmethod
    async def search_similar_nodes(query_embedding: np.ndarray, label: str, excluded_ids: List[int] = None, top_k: int = 5) -> List[Dict]:
        """Search for similar nodes using cosine similarity with exclusions"""
        try:
            cypher_query = Neo4jService.get_embedding_similarity_query(label, excluded_ids)
            
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
                            'node': dict(record['n']),
                            'text': text
                        })
                
                # Sort by similarity and return top k
                nodes.sort(key=lambda x: x['similarity'], reverse=True)
                return nodes[:top_k]
                
        except Exception as e:
            logger.error(f"Failed to search similar nodes: {e}")
            return []

    # Keep existing get_node_details method and CYPHER_QUERIES

# Enhanced API Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage):
    """Main conversational endpoint"""
    try:
        message = request.message.strip()
        session_id = request.session_id
        
        # Get or create session
        if session_id:
            context = SessionManager.get_session(session_id)
            if not context:
                # Session expired, create new one
                session_id = SessionManager.create_session(message)
                context = SessionManager.get_session(session_id)
        else:
            session_id = SessionManager.create_session(message)
            context = SessionManager.get_session(session_id)
        
        # Add message to conversation history
        context.conversation_history.append({"role": "user", "message": message})
        
        # Analyze user intent
        intent_analysis = await ConversationAgent.analyze_user_intent(message, context)
        
        # Handle different intents
        if intent_analysis['action'] == 'search':
            # Perform enhanced search
            enhanced_query = await ConversationAgent.generate_enhanced_query(
                context.original_query,
                intent_analysis.get('search_refinements', [message]),
                [result.get('node', {}).get('title', '') for result in context.excluded_results]
            )
            
            # Classify query label (reuse existing logic)
            detected_label = await QueryProcessor.classify_query_label(enhanced_query)
            
            # Generate embedding and search
            query_embedding = await EmbeddingService.get_embedding(enhanced_query)
            excluded_node_ids = [result for result in context.excluded_results if isinstance(result, int)]
            
            similar_nodes = await Neo4jService.search_similar_nodes(
                query_embedding, detected_label, excluded_node_ids, Config.TOP_K_RESULTS
            )
            
            if similar_nodes:
                # Add current results to excluded list for future searches
                context.excluded_results.extend([node['node_id'] for node in similar_nodes[:1]])
                context.enhanced_queries.append(enhanced_query)
                context.detected_labels.append(detected_label)
                
                # Generate conversational response
                response_text = await ConversationAgent.generate_conversational_response(
                    intent_analysis, context, similar_nodes
                )
                
                # Update session
                SessionManager.update_session(session_id, {
                    'current_state': 'searching',
                    'conversation_history': context.conversation_history + [{"role": "assistant", "message": response_text}]
                })
                
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    conversation_state='searching',
                    results=similar_nodes,
                    metadata={'enhanced_query': enhanced_query, 'detected_label': detected_label}
                )
            else:
                # No results found, ask for clarification
                clarifying_questions = await ConversationAgent.generate_clarifying_questions(context)
                response_text = "I couldn't find any matches for that. Let me ask a few questions to help narrow it down."
                
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    conversation_state='clarifying',
                    suggestions=clarifying_questions
                )
        
        elif intent_analysis['action'] == 'clarify':
            # Ask clarifying questions
            clarifying_questions = await ConversationAgent.generate_clarifying_questions(context)
            response_text = await ConversationAgent.generate_conversational_response(
                intent_analysis, context
            )
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                conversation_state='clarifying',
                suggestions=clarifying_questions
            )
        
        elif intent_analysis['action'] == 'acknowledge':
            # Acknowledge and potentially end conversation
            response_text = await ConversationAgent.generate_conversational_response(
                intent_analysis, context
            )
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                conversation_state='completed'
            )
        
        else:
            # Default response
            response_text = "I'm here to help you find information about movies, characters, scenes, locations, and objects from films. What would you like to search for?"
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                conversation_state='initial'
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "MediaGraphAI Chatbot API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    embedding_service_status = False
    try:
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
            "embedding_service": embedding_service_status
        },
        "active_sessions": len(conversation_sessions)
    }

# Keep existing QueryProcessor class for backward compatibility
class QueryProcessor:
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

# Hardcoded Cypher queries (same as original)
CYPHER_QUERIES = {
    "movie": """
        MATCH (m:Movie)-[:EXPLORES]->(theme)
        WHERE id(m) = $node_id
        OPTIONAL MATCH (m)-[:CONTAINS]->(c:Character)
        OPTIONAL MATCH (m)-[:TAKES_PLACE_IN]->(l:Location)
        OPTIONAL MATCH (m)-[:IN_SCENE]->(s:Scene)
        RETURN m, collect(DISTINCT c) as characters, 
               collect(DISTINCT l) as locations, 
               collect(DISTINCT s) as scenes,
               collect(DISTINCT theme) as themes
    """,
    "character": """
        MATCH (c:Character)-[:APPEARS_IN]->(m:Movie)
        WHERE id(c) = $node_id
        OPTIONAL MATCH (c)-[:IN_SCENE]->(s:Scene)
        OPTIONAL MATCH (c)-[:RELATES_TO]->(other:Character)
        RETURN c, m, collect(DISTINCT s) as scenes, 
               collect(DISTINCT other) as related_characters
    """,
    "scene": """
        MATCH (s:Scene)-[:PART_OF]->(m:Movie)
        WHERE id(s) = $node_id
        OPTIONAL MATCH (s)<-[:IN_SCENE]-(c:Character)
        OPTIONAL MATCH (s)-[:TAKES_PLACE_IN]->(l:Location)
        OPTIONAL MATCH (s)-[:CONTAINS]->(o:Object)
        RETURN s, m, collect(DISTINCT c) as characters,
               collect(DISTINCT l) as locations,
               collect(DISTINCT o) as objects
    """,
    "location": """
        MATCH (l:Location)<-[:TAKES_PLACE_IN]-(m:Movie)
        WHERE id(l) = $node_id
        OPTIONAL MATCH (l)<-[:TAKES_PLACE_IN]-(s:Scene)
        OPTIONAL MATCH (l)-[:CONTAINS]->(o:Object)
        RETURN l, collect(DISTINCT m) as movies,
               collect(DISTINCT s) as scenes,
               collect(DISTINCT o) as objects
    """,
    "object": """
        MATCH (o:Object)-[:APPEARS_IN]->(m:Movie)
        WHERE id(o) = $node_id
        OPTIONAL MATCH (o)<-[:CONTAINS]-(s:Scene)
        OPTIONAL MATCH (o)<-[:CONTAINS]-(l:Location)
        RETURN o, collect(DISTINCT m) as movies,
               collect(DISTINCT s) as scenes,
               collect(DISTINCT l) as locations
    """
}

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await services.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)