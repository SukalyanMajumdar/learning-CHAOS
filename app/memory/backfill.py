
"""
Project CHAOS - Conversational Memory Backfill

Maintenance utility:
- Finds primary-timeline messages without embeddings.
- Generates embeddings in batches.
- Persists vectors in PostgreSQL.
- Skips messages that already have embeddings.

Run from project root:
    python -m app.memory.backfill

Custom batch size:
    python -m app.memory.backfill --batch-size 25
"""

import argparse

from pgvector import Vector

from db import get_connection
from app.memory.embeddings import embed_messages


EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_BATCH_SIZE = 50


# ==========================================
# 1. FETCH MESSAGES WITHOUT EMBEDDINGS
# ==========================================

def get_unembedded_messages(
    limit: int
) -> list[dict]:

    query = """
        SELECT
            m.id,
            m.content
        FROM oracle.messages AS m

        JOIN oracle.conversations AS c
            ON c.id = m.conversation_id

        LEFT JOIN oracle.message_embeddings AS me
            ON me.message_id = m.id

        WHERE c.conversation_type = 'primary'
          AND c.status = 'active'
          AND me.message_id IS NULL

        ORDER BY m.id ASC
        LIMIT %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall()

    return [
        {
            "message_id": row[0],
            "content": row[1],
        }
        for row in rows
    ]


# ==========================================
# 2. SAVE EMBEDDINGS IN BATCH
# ==========================================

def save_embedding_batch(
    messages: list[dict],
    vectors: list[list[float]]
) -> None:

    if len(messages) != len(vectors):
        raise ValueError(
            "Message count and embedding count do not match."
        )

    query = """
        INSERT INTO oracle.message_embeddings (
            message_id,
            embedding,
            embedding_model
        )
        VALUES (%s, %s, %s)

        ON CONFLICT (message_id)
        DO NOTHING;
    """

    records = []

    for message, vector in zip(messages, vectors):

        if len(vector) != 1536:
            raise ValueError(
                f"Invalid embedding dimensions for message "
                f"{message['message_id']}: {len(vector)}"
            )

        records.append((
            message["message_id"],
            Vector(vector),
            EMBEDDING_MODEL,
        ))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, records)


# ==========================================
# 3. RUN BACKFILL
# ==========================================

def run_backfill(batch_size: int) -> None:

    total_processed = 0
    batch_number = 0

    print("=" * 55)
    print("PROJECT CHAOS - CONVERSATIONAL MEMORY BACKFILL")
    print("=" * 55)

    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Batch size: {batch_size}")

    while True:

        messages = get_unembedded_messages(batch_size)

        if not messages:
            break

        batch_number += 1

        message_ids = [
            message["message_id"]
            for message in messages
        ]

        print(
            f"\nBatch {batch_number}: "
            f"Processing {len(messages)} messages"
        )

        print(f"Message IDs: {message_ids}")

        contents = [
            message["content"]
            for message in messages
        ]

        # Generate vectors through the embedding service.
        vectors = embed_messages(contents)

        # Persist the generated vectors.
        save_embedding_batch(messages, vectors)

        total_processed += len(messages)

        print(
            f"Batch {batch_number} completed successfully."
        )

    print("\n" + "=" * 55)
    print("BACKFILL COMPLETED")
    print(f"Messages processed: {total_processed}")
    print("=" * 55)


# ==========================================
# 4. APPLICATION ENTRY POINT
# ==========================================

def main():

    parser = argparse.ArgumentParser(
        description="Backfill missing conversational embeddings."
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of messages to process per batch.",
    )

    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error("Batch size must be greater than zero.")

    try:
        run_backfill(args.batch_size)

    except Exception as error:
        print(f"\n[BACKFILL ERROR] {error}")
        raise


if __name__ == "__main__":
    main()
