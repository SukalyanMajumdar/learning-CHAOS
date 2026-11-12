
BEGIN;

-- ==========================================
-- MIGRATION 002: CONVERSATION LIFECYCLE
-- ==========================================

-- 1. Classify conversations
-- Existing conversations become temporary by default.

ALTER TABLE oracle.conversations
ADD COLUMN conversation_type TEXT NOT NULL
DEFAULT 'temporary'
CHECK (
    conversation_type IN ('primary', 'temporary')
);


-- 2. Introduce lifecycle status

ALTER TABLE oracle.conversations
ADD COLUMN status TEXT NOT NULL
DEFAULT 'active'
CHECK (
    status IN ('active', 'archived')
);


-- 3. Ensure only ONE primary conversation exists

CREATE UNIQUE INDEX idx_single_primary_conversation
ON oracle.conversations (conversation_type)
WHERE conversation_type = 'primary';


-- 4. Index conversation lifecycle queries

CREATE INDEX idx_conversations_type_status
ON oracle.conversations (conversation_type, status);


-- 5. Create the Oracle's permanent primary timeline
-- Existing test conversations remain temporary.

INSERT INTO oracle.conversations (
    title,
    conversation_type,
    status,
    metadata
)
SELECT
    'Oracle — Primary Timeline',
    'primary',
    'active',
    '{"purpose": "permanent_oracle_conversation"}'::jsonb
WHERE NOT EXISTS (
    SELECT 1
    FROM oracle.conversations
    WHERE conversation_type = 'primary'
);


COMMIT;
