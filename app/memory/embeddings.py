
from langchain_openai import OpenAIEmbeddings

from config.settings import settings

# ==========================================
# 1. INITIALIZE EMBEDDING MODEL
# ==========================================

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.openai_api_key.get_secret_value(),
)


# ==========================================
# 2. GENERATE SINGLE MESSAGE EMBEDDING
# ==========================================

def embed_message(content: str) -> list[float]:

    if not content.strip():
        raise ValueError("Cannot embed empty content.")

    return embedding_model.embed_query(content)


# ==========================================
# 3. GENERATE MULTIPLE MESSAGE EMBEDDINGS
# ==========================================

def embed_messages(contents: list[str]) -> list[list[float]]:

    if not contents:
        return []

    if any(not content.strip() for content in contents):
        raise ValueError("Cannot embed empty content.")

    return embedding_model.embed_documents(contents)

