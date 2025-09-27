from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-large-en-v1.5")

app = FastAPI()

class EmbeddingRequest(BaseModel):
    text: str  

@app.post("/embed")
async def embed_text(request: EmbeddingRequest):  
    embeddings = model.encode([request.text])[0] 
    return {"text": request.text, "embedding": embeddings.tolist()}