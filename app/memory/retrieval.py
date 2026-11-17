from uuid import UUID
from typing import Any

from db import get_connection
from app.memory.embeddings import embed_message
from pgvector import Vector


# ==========================================
# 1. SEARCH CONVERSATION HISTORY
# ==========================================

def search_conversation(
    conversation_id: UUID,
    query: str,
    limit: int = 5,
    min_similarity: float = 0.40,
) -> list[dict[str, Any]]:
    """
    Search a conversation's historical messages using cosine similarity.

    Args:
        conversation_id: Conversation timeline to search.
        query: Natural-language search query.
        limit: Maximum number of candidate messages to retrieve.
        min_similarity: Minimum cosine similarity score to return.
                        Valid range is -1.0 to 1.0.

    Returns:
        Matching messages ordered from most to least similar.
    """

    # --------------------------------------
    # Validate inputs
    # --------------------------------------

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if limit < 1:
        raise ValueError("Limit must be greater than zero.")

    if not -1.0 <= min_similarity <= 1.0:
        raise ValueError(
            "Similarity threshold must be between -1 and 1."
        )

    # --------------------------------------
    # Generate query embedding
    # --------------------------------------

    query_embedding = embed_message(query)
    vector = Vector(query_embedding)

    # --------------------------------------
    # Semantic similarity search
    # --------------------------------------

    sql_query = """
        SELECT
            m.id,
            m.role,
            m.content,
            m.created_at,
            1 - (me.embedding <=> %s) AS similarity
        FROM oracle.messages AS m
        INNER JOIN oracle.message_embeddings AS me
            ON m.id = me.message_id
        WHERE m.conversation_id = %s
        ORDER BY me.embedding <=> %s
        LIMIT %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql_query,
                (
                    vector,
                    conversation_id,
                    vector,
                    limit,
                ),
            )
            rows = cur.fetchall()

    # --------------------------------------
    # Apply similarity threshold and format
    # --------------------------------------

    return [
        {
            "message_id": row[0],
            "role": row[1],
            "content": row[2],
            "created_at": row[3],
            "similarity": float(row[4]),
        }
        for row in rows
        if float(row[4]) >= min_similarity
    ]
