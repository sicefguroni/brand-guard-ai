from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.vector_db import initialize_db, upsert_brand_rule

# LIFESPAN: This is the modern way to run startup code in FastAPI
# It runs ONE TIME when the server starts.
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB and create table
    initialize_db()
    yield
    # Shutdown: (Cleanup code would go here if needed)

app = FastAPI(title="BrandGuard AI", lifespan=lifespan)

# DATA MODEL: Defines what JSON data we accept
class BrandRule(BaseModel):
    rule: str
    category: str # e.g., "Tone", "Banned Words", "Formatting"

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