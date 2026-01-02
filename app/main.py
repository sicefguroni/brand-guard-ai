from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.safety import init_safety, validate_context
from app.services.vector_db import initialize_db, upsert_brand_rule, search_brand_rules
from app.services.generator import generate_social_post

# LIFESPAN: This is the modern way to run startup code in FastAPI
# It runs ONE TIME when the server starts.
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB and create table
    initialize_db()
    init_safety() # Load banned words into profanity filter
    yield
    # Shutdown: (Cleanup code would go here if needed)

app = FastAPI(title="BrandGuard AI", lifespan=lifespan)

# DATA MODEL: Defines what JSON data we accept
class BrandRule(BaseModel):
    rule: str
    category: str # e.g., "Tone", "Banned Words", "Formatting"

class PostRequest(BaseModel):
    topic: str
    platform: str

@app.get("/")
def health_check():
    return {"status": "BrandGuard AI is Ready"}

@app.post("/add-rule")
def add_knowledge(data: BrandRule):
    """
    Endpoint to add a new rule to the knowledge base.
    Example: {"rule": "Never use slang", "category": "Tone"}
    """
    try:
        result = upsert_brand_rule(data.rule, data.category)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-post")
def create_post(request: PostRequest):
    """
    The Full RAG Pipeline:
    1. Search DB for relevant rules.
    2. Send rules + topic to LLM.
    3. Return the safe, on-brand post.
    """
    try: 
        # Step 1: Retrieval (R)
        # We search for rules related to the topic AND the platform
        query = f"{request.topic} style for {request.platform}"
        relevant_rules = search_brand_rules(query)
        
        # Step 2: Generation (G)
        generated_content = generate_social_post(
            topic=request.topic,
            platform=request.platform,
            context_rules=relevant_rules
        )
        
        return {
            "status": "success",
            "post": generated_content,
            "context_used": relevant_rules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))