import os
import functools
import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
_model = None

def _load_model():
    global _model
    if _model is None:
        name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        logger.info(f"Loading embedding model: {name}")
        _model = SentenceTransformer(name)
    return _model

@functools.lru_cache(maxsize=1024)
def embed_text(text: str) -> List[float]:
    """Возвращает L2-нормированный эмбеддинг"""
    model = _load_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist() if isinstance(vec, np.ndarray) else vec
