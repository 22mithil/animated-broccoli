from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# Load model once at startup
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

app = FastAPI()

# Input schema
class QueryRequest(BaseModel):
    query: str

@app.post("/embed")
async def embed_text(request: QueryRequest):
    # Encode query into embeddings
    embeddings = model.encode([request.query])[0]
    return {"query": request.query, "embedding": embeddings.tolist()}
