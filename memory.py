import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is not set")


redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)


MAX_MESSAGES = 10
MEMORY_TTL = 3600


def get_memory(session_id: str):
    key = f"chat:{session_id}"

    messages = redis_client.lrange(
        key,
        0,
        -1
    )

    return [
        json.loads(message)
        for message in messages
    ]


def add_message(
    session_id: str,
    role: str,
    content: str
):
    key = f"chat:{session_id}"

    message = {
        "role": role,
        "content": content
    }

    redis_client.rpush(
        key,
        json.dumps(message)
    )

    # Keep only the latest messages
    redis_client.ltrim(
        key,
        -MAX_MESSAGES,
        -1
    )

    # Expire inactive conversations
    redis_client.expire(
        key,
        MEMORY_TTL
    )


def clear_memory(session_id: str):
    key = f"chat:{session_id}"

    redis_client.delete(key)