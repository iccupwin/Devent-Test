import os, logging
from qdrant_client import QdrantClient, models
from .embed import embed_text, format_task_for_vectorization, _load_model
from typing import List, Dict, Any, Optional
import time
from datetime import datetime

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

def search(query: str, limit: int = 5, score_threshold: float = 0.7):
    try:
        vec = embed_text(query)
        if len(vec) != VECTOR_SIZE:
            raise ValueError(f"Vector size mismatch: expected {VECTOR_SIZE}, got {len(vec)}")
            
        return client.search(
            COLLECTION_NAME,
            vec,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise

def upsert_planfix_task(task_id: int, task_data: dict):
    """
    Сохраняет задачу Planfix в векторное хранилище
    """
    try:
        # Используем новый формат для векторизации
        task_text = format_task_for_vectorization(task_data)
        
        vec = embed_text(task_text)
        if len(vec) != VECTOR_SIZE:
            raise ValueError(f"Vector size mismatch: expected {VECTOR_SIZE}, got {len(vec)}")
        
        # Добавляем метаданные
        meta = {
            "type": "planfix_task",
            "task_id": task_id,
            "data": {
                "title": task_data.get('title', ''),
                "description": task_data.get('description', ''),
                "project": task_data.get('project', {}),
                "assignee": task_data.get('assignee', {}),
                "status": task_data.get('status', {}),
                "priority": task_data.get('priority', ''),
                "deadline": task_data.get('deadline', ''),
                "created_at": task_data.get('created_at'),
                "updated_at": task_data.get('updated_at'),
                "tags": task_data.get('tags', []),
                "comments": task_data.get('comments', [])
            }
        }
        
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=str(task_id),
                    vector=vec,
                    payload=meta,
                )
            ],
        )
        
        logger.info(f"Successfully upserted task {task_id}")
    except Exception as e:
        logger.error(f"Error upserting Planfix task {task_id}: {e}")
        raise

def search_planfix_tasks(
    query: str, 
    limit: int = 5, 
    filters: Optional[Dict[str, Any]] = None,
    score_threshold: float = 0.7
) -> List[Any]:
    """
    Поиск задач Planfix по векторному представлению запроса
    """
    try:
        # Используем чистый запрос без дополнительных префиксов
        vec = embed_text(query)
        if len(vec) != VECTOR_SIZE:
            raise ValueError(f"Vector size mismatch: expected {VECTOR_SIZE}, got {len(vec)}")
        
        # Базовый поиск
        search_params = {
            "collection_name": COLLECTION_NAME,
            "query_vector": vec,
            "limit": limit,
            "score_threshold": score_threshold,
            "with_payload": True,
        }
        
        # Добавляем фильтры, если они есть
        if filters:
            search_params["query_filter"] = models.Filter(
                must=[
                    models.FieldCondition(
                        key="type",
                        match=models.MatchValue(value="planfix_task")
                    ),
                    *[
                        models.FieldCondition(
                            key=f"data.{key}",
                            match=models.MatchValue(value=value)
                        )
                        for key, value in filters.items()
                    ]
                ]
            )
        else:
            # Если фильтров нет, ищем только задачи
            search_params["query_filter"] = models.Filter(
                must=[
                    models.FieldCondition(
                        key="type",
                        match=models.MatchValue(value="planfix_task")
                    )
                ]
            )
        
        # Выполняем поиск
        results = client.search(**search_params)
        
        # Логируем результаты
        if not results:
            logger.warning(f"Поиск не дал результатов для запроса: {query}")
            return []
            
        for hit in results:
            task_data = hit.payload.get('data', {})
            logger.info(
                f"Found task {hit.payload.get('task_id')} "
                f"with score {hit.score:.3f}: "
                f"Title: {task_data.get('title', '')}, "
                f"Project: {task_data.get('project', {}).get('name', '')}, "
                f"Status: {task_data.get('status', {}).get('name', '')}, "
                f"Assignee: {task_data.get('assignee', {}).get('name', '')}, "
                f"Priority: {task_data.get('priority', '')}, "
                f"Deadline: {task_data.get('deadline', '')}"
            )
        
        return results
    except Exception as e:
        logger.error(f"Error searching Planfix tasks: {e}")
        raise

def update_vector_store():
    """
    Обновляет векторное хранилище данными из Planfix
    """
    try:
        from .planfix_cache_service import planfix_cache
        tasks = planfix_cache.get_all_tasks()
        logger.info(f"Получено {len(tasks)} задач из Planfix")
        
        # Получаем существующие ID в векторном хранилище
        existing_ids = set()
        scroll_response = client.scroll(
            COLLECTION_NAME,
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        for point in scroll_response[0]:  # scroll_response возвращает кортеж (points, next_page_offset)
            if point.payload.get('type') == 'planfix_task':
                existing_ids.add(point.payload.get('task_id'))
        
        # Обновляем или добавляем новые задачи
        updated_count = 0
        current_ids = set()
        
        for task in tasks:
            try:
                task_id = task.get('id')
                if task_id:
                    current_ids.add(task_id)
                    upsert_planfix_task(task_id, task)
                    updated_count += 1
            except Exception as e:
                logger.error(f"Ошибка при обновлении задачи {task.get('id')}: {str(e)}")
        
        # Удаляем устаревшие задачи
        deleted_ids = existing_ids - current_ids
        if deleted_ids:
            client.delete(
                COLLECTION_NAME,
                points_selector=models.PointIdsList(
                    points=[str(id) for id in deleted_ids]
                )
            )
            logger.info(f"Удалено {len(deleted_ids)} устаревших задач")
        
        logger.info(f"Обновлено {updated_count} задач в векторном хранилище")
        return updated_count
    except Exception as e:
        logger.error(f"Ошибка при обновлении векторного хранилища: {str(e)}")
        return 0

def get_employee_tasks(employee_name: str, limit: int = 100) -> List[Any]:
    """
    Получает задачи конкретного сотрудника из векторного хранилища
    
    Args:
        employee_name: Имя сотрудника
        limit: Максимальное количество задач
        
    Returns:
        Список найденных задач
    """
    try:
        # Создаем фильтр для поиска задач сотрудника
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="type",
                    match=models.MatchValue(value="planfix_task")
                ),
                models.FieldCondition(
                    key="data.assignee.name",
                    match=models.MatchValue(value=employee_name)
                )
            ]
        )
        
        # Получаем все задачи сотрудника
        scroll_response = client.scroll(
            COLLECTION_NAME,
            limit=limit,
            with_payload=True,
            with_vectors=False,
            query_filter=search_filter
        )
        
        tasks = []
        for point in scroll_response[0]:  # scroll_response возвращает кортеж (points, next_page_offset)
            task_data = point.payload.get('data', {})
            
            # Форматируем дату дедлайна
            deadline = task_data.get('deadline', '')
            if deadline and isinstance(deadline, str):
                try:
                    deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    deadline = deadline_dt.strftime('%d.%m.%Y')
                except:
                    pass
            
            # Форматируем даты создания и обновления
            created_at = task_data.get('created_at', '')
            if created_at and isinstance(created_at, str):
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = created_dt.strftime('%d.%m.%Y %H:%M')
                except:
                    pass
                    
            updated_at = task_data.get('updated_at', '')
            if updated_at and isinstance(updated_at, str):
                try:
                    updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    updated_at = updated_dt.strftime('%d.%m.%Y %H:%M')
                except:
                    pass
            
            # Форматируем теги
            tags = task_data.get('tags', [])
            if isinstance(tags, list):
                tags_str = ', '.join(tags)
            else:
                tags_str = str(tags)
            
            task = {
                'id': point.payload.get('task_id'),
                'title': task_data.get('title', 'Без названия'),
                'description': task_data.get('description', ''),
                'project': task_data.get('project', {}).get('name', 'Без проекта'),
                'status': task_data.get('status', {}).get('name', 'Не определен'),
                'priority': task_data.get('priority', 'Не указан'),
                'deadline': deadline,
                'created_at': created_at,
                'updated_at': updated_at,
                'tags': tags_str,
                'assignee': task_data.get('assignee', {}).get('name', 'Не назначен')
            }
            
            # Добавляем комментарии, если они есть
            comments = task_data.get('comments', [])
            if comments and isinstance(comments, list):
                task['comments'] = [
                    {
                        'author': comment.get('author', {}).get('name', 'Неизвестный'),
                        'text': comment.get('text', ''),
                        'created_at': comment.get('created_at', '')
                    }
                    for comment in comments
                ]
            
            tasks.append(task)
        
        logger.info(f"Найдено {len(tasks)} задач для сотрудника {employee_name}")
        return tasks
        
    except Exception as e:
        logger.error(f"Ошибка при получении задач сотрудника {employee_name}: {str(e)}")
        return []
