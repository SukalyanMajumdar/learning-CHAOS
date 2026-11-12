
-- ==========================================
-- PROJECT CHAOS
-- 003 - CONVERSATIONAL MESSAGE EMBEDDINGS
-- ==========================================

CREATE TABLE oracle.message_embeddings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    message_id BIGINT NOT NULL UNIQUE
        REFERENCES oracle.messages(id)
        ON DELETE CASCADE,

    embedding VECTOR(1536) NOT NULL,

    embedding_model TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW index for cosine similarity search
CREATE INDEX idx_message_embeddings_vector
ON oracle.message_embeddings
USING hnsw (embedding vector_cosine_ops);

-- Support message-to-embedding lookup
CREATE INDEX idx_message_embeddings_message_id
ON oracle.message_embeddings(message_id);
