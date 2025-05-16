import os, logging
from qdrant_client import QdrantClient, models
from .embed import embed_text, _load_model

logger = logging.getLogger(__name__)

QDRANT_URL      = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("VECTOR_COLLECTION", "chat_messages")
VECTOR_SIZE     = _load_model().get_sentence_embedding_dimension()  # Получаем размерность из модели

client = QdrantClient(url=QDRANT_URL)

def ensure_collection():
    try:
        collections = client.get_collections().collections
        if COLLECTION_NAME not in [c.name for c in collections]:
            logger.info(f"Creating collection {COLLECTION_NAME} with vector size {VECTOR_SIZE}")
            client.recreate_collection(
                COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )
        else:
            # Проверяем существующую коллекцию
            collection_info = client.get_collection(COLLECTION_NAME)
            if collection_info.config.params.vectors.size != VECTOR_SIZE:
                logger.warning(f"Collection {COLLECTION_NAME} has wrong vector size. Recreating...")
                client.recreate_collection(
                    COLLECTION_NAME,
                    vectors_config=models.VectorParams(
                        size=VECTOR_SIZE,
                        distance=models.Distance.COSINE,
                    ),
                )
    except Exception as e:
        logger.error(f"Error ensuring collection: {e}")
        raise

ensure_collection()

def upsert_message(message_id: int, content: str, meta: dict):
    try:
        vec = embed_text(content)
        if len(vec) != VECTOR_SIZE:
            raise ValueError(f"Vector size mismatch: expected {VECTOR_SIZE}, got {len(vec)}")
        
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=str(message_id),
                    vector=vec,
                    payload=meta,
                )
            ],
        )
    except Exception as e:
        logger.error(f"Error upserting message {message_id}: {e}")
        raise

def search(query: str, limit: int = 5):
    try:
        vec = embed_text(query)
        if len(vec) != VECTOR_SIZE:
            raise ValueError(f"Vector size mismatch: expected {VECTOR_SIZE}, got {len(vec)}")
            
        return client.search(
            COLLECTION_NAME,
            vec,
            limit=limit,
            with_payload=True,
        )
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise
