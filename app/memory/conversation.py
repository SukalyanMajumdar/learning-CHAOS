
import logging

from uuid import UUID
from typing import Any

from db import get_connection
from app.memory.embeddings import embed_message
from pgvector import Vector


logger = logging.getLogger(__name__)


# ==========================================
# 1. GET PRIMARY CONVERSATION
# ==========================================

def get_primary_conversation() -> dict[str, Any]:

    query = """
        SELECT id, title, conversation_type, status
        FROM oracle.conversations
        WHERE conversation_type = 'primary'
          AND status = 'active';
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()

    if row is None:
        raise RuntimeError("Oracle primary conversation not found.")

    return {
        "id": row[0],
        "title": row[1],
        "conversation_type": row[2],
        "status": row[3],
    }


# ==========================================
# 2. CREATE TEMPORARY CONVERSATION
# ==========================================

def create_temporary_conversation(title: str) -> UUID:

    query = """
        INSERT INTO oracle.conversations (
            title,
            conversation_type,
            status
        )
        VALUES (%s, 'temporary', 'active')
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (title,))
            conversation_id = cur.fetchone()[0]

    return conversation_id


# ==========================================
# 3. SAVE MESSAGE
# ==========================================

def save_message(
    conversation_id: UUID,
    role: str,
    content: str
) -> int:

    allowed_roles = {"system", "user", "assistant", "tool"}

    if role not in allowed_roles:
        raise ValueError(f"Invalid message role: {role}")

    if not content.strip():
        raise ValueError("Message content cannot be empty.")

    insert_query = """
        INSERT INTO oracle.messages (
            conversation_id,
            role,
            content
        )
        SELECT id, %s, %s
        FROM oracle.conversations
        WHERE id = %s
          AND status = 'active'
        RETURNING id;
    """

    update_query = """
        UPDATE oracle.conversations
        SET updated_at = NOW()
        WHERE id = %s;
    """

    # --------------------------------------
    # STEP 1: Persist the original message
    # --------------------------------------

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                insert_query,
                (role, content, conversation_id)
            )

            row = cur.fetchone()

            if row is None:
                raise ValueError(
                    "Conversation not found or is not active."
                )

            message_id = row[0]

            cur.execute(update_query, (conversation_id,))

    # --------------------------------------
    # STEP 2: Generate and persist embedding
    # --------------------------------------

    # Only user and assistant messages are indexed.
    if role in {"user", "assistant"}:

        try:
            embedding = embed_message(content)

            save_message_embedding(
                message_id=message_id,
                embedding=embedding,
                model="text-embedding-3-small",
            )

            logger.info(
                "Embedding successfully saved for message ID %s.",
                message_id,
            )

        except Exception:
            logger.exception(
                "Embedding generation or persistence failed "
                "for message ID %s. Message remains saved "
                "and can be recovered through backfill.",
                message_id,
            )

    return message_id


# ==========================================
# 4. GET RECENT MESSAGES
# ==========================================

def get_recent_messages(
    conversation_id: UUID,
    limit: int = 20
) -> list[dict[str, Any]]:

    if limit < 1:
        raise ValueError("Limit must be greater than zero.")

    query = """
        SELECT id, role, content, created_at
        FROM (
            SELECT id, role, content, created_at
            FROM oracle.messages
            WHERE conversation_id = %s
            ORDER BY id DESC
            LIMIT %s
        ) AS recent
        ORDER BY id ASC;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (conversation_id, limit))
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]


# ==========================================
# 5. GET COMPLETE CONVERSATION HISTORY
# ==========================================

def get_conversation_history(
    conversation_id: UUID
) -> list[dict[str, Any]]:

    query = """
        SELECT id, role, content, created_at
        FROM oracle.messages
        WHERE conversation_id = %s
        ORDER BY id ASC;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (conversation_id,))
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]


# ==========================================
# 6. SAVE MESSAGE EMBEDDING
# ==========================================

def save_message_embedding(
    message_id: int,
    embedding: list[float],
    model: str
) -> int:

    if not embedding:
        raise ValueError("Embedding cannot be empty.")

    if not model.strip():
        raise ValueError("Embedding model cannot be empty.")

    if len(embedding) != 1536:
        raise ValueError(
            f"Expected 1536 dimensions, got {len(embedding)}."
        )

    query = """
        INSERT INTO oracle.message_embeddings (
            message_id,
            embedding,
            embedding_model
        )
        VALUES (%s, %s, %s)

        ON CONFLICT (message_id)
        DO UPDATE SET
            embedding = EXCLUDED.embedding,
            embedding_model = EXCLUDED.embedding_model,
            created_at = NOW()

        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    message_id,
                    Vector(embedding),
                    model
                )
            )

            embedding_id = cur.fetchone()[0]

    return embedding_id
