import os
import functools
import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
_model = None

def _load_model():
    global _model
    if _model is None:
        # Используем BGE для лучшего поиска
        name = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
        logger.info(f"Loading embedding model: {name}")
        _model = SentenceTransformer(name)
    return _model

@functools.lru_cache(maxsize=1024)
def embed_text(text: str) -> List[float]:
    """Возвращает L2-нормированный эмбеддинг"""
    model = _load_model()
    # Добавляем префикс для BGE модели
    if not text.startswith("Represent this sentence for searching relevant passages:"):
        text = "Represent this sentence for searching relevant passages: " + text
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist() if isinstance(vec, np.ndarray) else vec

def format_task_for_vectorization(task_data: Dict[str, Any]) -> str:
    """
    Форматирует данные задачи для векторизации в структурированном виде
    """
    # Извлекаем данные с учетом возможной вложенности
    title = task_data.get('title', '')
    description = task_data.get('description', '')
    
    # Обработка вложенных объектов
    project_name = task_data.get('project', {}).get('name', '') if isinstance(task_data.get('project'), dict) else str(task_data.get('project', ''))
    assignee_name = task_data.get('assignee', {}).get('name', '') if isinstance(task_data.get('assignee'), dict) else str(task_data.get('assignee', ''))
    status_name = task_data.get('status', {}).get('name', '') if isinstance(task_data.get('status'), dict) else str(task_data.get('status', ''))
    
    # Форматируем дату дедлайна, если она есть
    deadline = task_data.get('deadline', '')
    if deadline and isinstance(deadline, str):
        try:
            from datetime import datetime
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            deadline = deadline_dt.strftime('%d.%m.%Y')
        except:
            pass
    
    # Форматируем теги
    tags = task_data.get('tags', [])
    if isinstance(tags, list):
        tags_str = ', '.join(tags)
    else:
        tags_str = str(tags)
    
    return (
        f"Тип: Задача. Название: {title}. "
        f"Описание: {description}. Проект: {project_name}. "
        f"Ответственный: {assignee_name}. Статус: {status_name}. "
        f"Приоритет: {task_data.get('priority', '')}. "
        f"Дедлайн: {deadline}. Теги: {tags_str}."
    )
