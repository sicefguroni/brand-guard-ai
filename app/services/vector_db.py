from ctypes import pointer
import os
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# CONFIGURATION
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST")

# Configure Google Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Connect to Qdrant
client = QdrantClient(host=QDRANT_HOST, port=6333)

COLLECTION_NAME = "brand_knowledge"

def initialize_db():
    """Creates the collection if it doesn't exist and configures the vector space."""
    try:
        # Check if collection exists
        collections = client.get_collections()
        exists = any(c.name == COLLECTION_NAME for c in collections.collections)

        if not exists:
            print(f"Creating collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
        else:
            print(f"Collection {COLLECTION_NAME} already exists.")

    except Exception as e:
        print(f"Error initializing database: {e}")

def embed_text(text: str):
    """Turns text into a vector using Gemini."""
    model = "models/text-embedding-004"
    
    result = genai.embed_content(
        model=model,
        content=text,
        # 'retrieval_document' helps the model understand this is data for a database
        task_type="retrieval_document" 
    )
    return result['embedding']

def upsert_brand_rule(text: str, category: str):
    """Saves a brand rule to the vector database."""
    # 1. Get the vector
    vector = embed_text(text)

    # 2. Save to Qdrant
    import uuid
    point_id = str(uuid.uuid4())

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "text": text,
                    "category": category
                }
            )
        ]
    )
    return {"status": "success", "id": point_id}

def search_brand_rules(query_text: str, limit: int = 3):
    """
    1. Converts query to vector.
    2. Searches Qdrant for similar vectors.
    3. Returns the text of the best matches.
    """
    # 1. Embed the query
    query_vector = embed_text(query_text)

    # 2. Search Qdrant
    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit
    )

    # 3. Return the text of the best matches
    results = [hit.payload['text'] for hit in search_results]
    return results