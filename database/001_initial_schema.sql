
BEGIN;

CREATE SCHEMA IF NOT EXISTS oracle;

-- ==========================================
-- TABLE 1: CONVERSATIONS
-- ==========================================

CREATE TABLE oracle.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    title TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);


-- ==========================================
-- TABLE 2: MESSAGES
-- ==========================================

CREATE TABLE oracle.messages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    conversation_id UUID NOT NULL
        REFERENCES oracle.conversations(id)
        ON DELETE CASCADE,

    role TEXT NOT NULL
        CHECK (role IN ('system', 'user', 'assistant', 'tool')),

    content TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);


-- ==========================================
-- INDEXES
-- ==========================================

CREATE INDEX idx_messages_conversation_id
    ON oracle.messages(conversation_id);

CREATE INDEX idx_messages_created_at
    ON oracle.messages(created_at);

COMMIT;
