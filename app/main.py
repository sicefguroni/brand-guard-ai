from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.safety import init_safety, validate_content
from app.services.vector_db import initialize_db, upsert_brand_rule, search_brand_rules
from app.services.generator import generate_social_post
from app.services.cache import get_cached_post, save_to_cache

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
    try:
        # --- NEW: INPUT GUARDRAIL ---
        # Check if the USER'S topic contains banned words
        is_topic_safe, topic_msg = validate_content(request.topic)
        if not is_topic_safe:
             return {
                "status": "blocked",
                "reason": f"Topic violation: {topic_msg}",
                "generated_content": "[REDACTED]"
            }
        # ---------------------------
        cached_result = get_cached_post(request.topic, request.platform)
        if cached_result:
            return {
                "status": "success",
                "post": cached_result['post'],
                "context_used": cached_result['context_used'],
                "meta": "Served from Cache ⚡" # Just to show off speed
            }

        # 1. Retrieval
        query = f"{request.topic} style for {request.platform}"
        relevant_rules = search_brand_rules(query)
        
        # 2. Generation
        generated_content = generate_social_post(
            topic=request.topic,
            platform=request.platform,
            context_rules=relevant_rules
        )
        
        # 3. OUTPUT GUARDRAIL (Keep this too!)
        is_safe, message = validate_content(generated_content)

        if not is_safe:
            return {
                "status": "blocked",
                "reason": message,
                "generated_content": "[REDACTED]" 
            }

         # 4. Save to Cache
        save_to_cache(request.topic, request.platform, generated_content, relevant_rules)

        return {
            "status": "success",
            "post": generated_content,
            "context_used": relevant_rules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))