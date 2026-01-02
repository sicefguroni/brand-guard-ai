import os
import redis
import json
import hashlib

redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "cache"), port=6379, db=0)

def get_cache_key(topic: str, platform: str):
    """Creates a unique ID for this request"""
    raw_key = f"{platform.lower()}:{topic.lower()}"
    # Handles long strings
    return hashlib.md5(raw_key.encode()).hexdigest()

def get_cached_post(topic: str, platform: str):
    """Tries to get a cached post from Redis"""
    key = get_cache_key(topic, platform)
    cached_data = redis_client.get(key)

    if cached_data:
        return json.loads(cached_data)
    return None

def save_to_cache(topic: str, platform: str, content: str, context: str):
    """Save the result to Redis for 1 hour"""
    key = get_cache_key(topic, platform)

    data = {
        "post": content,
        "context_used": context,
        "source": "cache"
    }

    redis_client.set(key, json.dumps(data), ex=3600)