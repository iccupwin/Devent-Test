import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from django.shortcuts import render
from .vector_service import search_planfix_tasks, get_employee_tasks, upsert_planfix_task
from .planfix_cache_service import planfix_cache
import logging
import json
import os

logger = logging.getLogger(__name__)

CACHE_PATH = os.path.join(os.path.dirname(__file__), 'cache', 'vector_data_cache.json')

def update_vector_store():
    """
    Обновляет векторное хранилище данными из Planfix
    """
    try:
        tasks = planfix_cache.get_all_tasks()
        logger.info(f"Получено {len(tasks)} задач из Planfix для обновления векторного хранилища")
        
        updated_count = 0
        for task in tasks:
            try:
                task_id = task.get('id')
                if task_id:
                    upsert_planfix_task(task_id, task)
                    updated_count += 1
            except Exception as e:
                logger.error(f"Ошибка при обновлении задачи {task.get('id')}: {str(e)}")
        
        logger.info(f"Обновлено {updated_count} задач в векторном хранилище")
        return updated_count
    except Exception as e:
        logger.error(f"Ошибка при обновлении векторного хранилища: {str(e)}")
        return 0

def create_vector_dataframe():
    """
    Создает DataFrame с данными из векторного хранилища
    """
    try:
        # Получаем все задачи из Planfix
        tasks = planfix_cache.get_all_tasks()
        logger.info(f"Получено {len(tasks)} задач из Planfix")
        
        if not tasks:
            logger.warning("Нет задач в кэше Planfix")
            return pd.DataFrame()
        
        # Создаем список для хранения данных
        data = []
        
        for task in tasks:
            try:
                # Получаем векторное представление задачи
                task_name = task.get('name', '')
                logger.info(f"Обработка задачи: {task_name}")
                vector_results = search_planfix_tasks(task_name, limit=1)
                logger.info(f"Результаты поиска для задачи {task_name}: {len(vector_results) if vector_results else 0}")
                
                if vector_results:
                    vector = vector_results[0].vector
                    similarity = vector_results[0].score
                    # Проверка: вектор должен быть массивом чисел
                    if (vector is None or not isinstance(vector, (list, tuple)) or not all(isinstance(x, (int, float)) for x in vector)):
                        logger.warning(f"Вектор для задачи '{task_name}' невалиден: {vector}")
                        vector = 'Нет данных'
                    task_data = {
                        'ID': task['id'],
                        'Название': task_name,
                        'Статус': task.get('status', {}).get('name', ''),
                        'Приоритет': task.get('priority', {}).get('name', ''),
                        'Ответственный': task.get('assignee', {}).get('name', ''),
                        'Срок': task.get('deadline', ''),
                        'Проект': task.get('project', {}).get('name', ''),
                        'Вектор': vector,
                        'Схожесть': similarity
                    }
                    data.append(task_data)
                    logger.info(f"Добавлена задача {task_name} в DataFrame")
                else:
                    logger.warning(f"Не найдено векторное представление для задачи {task_name}")
                    task_data = {
                        'ID': task['id'],
                        'Название': task_name,
                        'Статус': task.get('status', {}).get('name', ''),
                        'Приоритет': task.get('priority', {}).get('name', ''),
                        'Ответственный': task.get('assignee', {}).get('name', ''),
                        'Срок': task.get('deadline', ''),
                        'Проект': task.get('project', {}).get('name', ''),
                        'Вектор': 'Нет данных',
                        'Схожесть': None
                    }
                    data.append(task_data)
            except Exception as e:
                logger.error(f"Ошибка при обработке задачи {task.get('id')}: {str(e)}")
        df = pd.DataFrame(data)
        logger.info(f"Создан DataFrame с {len(df)} строками")
        logger.info(f"Колонки в DataFrame: {df.columns.tolist()}")
        if df.empty:
            logger.warning("DataFrame пустой после обработки всех задач")
        return df
    except Exception as e:
        logger.error(f"Ошибка при создании DataFrame: {str(e)}")
        return pd.DataFrame()

def save_vector_cache(df):
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        df.to_json(CACHE_PATH, orient='records', force_ascii=False)
        logger.info(f"Сохранено {len(df)} строк в кэш {CACHE_PATH}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении кэша: {str(e)}")

def load_vector_cache():
    try:
        if not os.path.exists(CACHE_PATH):
            logger.warning(f"Кэш {CACHE_PATH} не найден")
            return pd.DataFrame()
        df = pd.read_json(CACHE_PATH, orient='records')
        logger.info(f"Загружено {len(df)} строк из кэша {CACHE_PATH}")
        return df
    except Exception as e:
        logger.error(f"Ошибка при загрузке кэша: {str(e)}")
        return pd.DataFrame()

def vector_visualization(request):
    """View для отображения визуализации векторов (только из кэша)"""
    try:
        df = load_vector_cache()
        if df.empty:
            return render(request, 'vector_visualization.html', {
                'error': 'Нет кэшированных данных для отображения. Нажмите "Обновить данные".'
            })
        table_data = {
            'data': df.to_dict(orient='records'),
            'columns': df.columns.tolist()
        }
        plot_data = {
            'x': df['Схожесть'].tolist(),
            'type': 'histogram',
            'name': 'Распределение схожести'
        }
        return render(request, 'vector_visualization.html', {
            'table_data': json.dumps(table_data),
            'plot_data': json.dumps(plot_data)
        })
    except Exception as e:
        logger.error(f"Error in vector visualization: {str(e)}")
        return render(request, 'vector_visualization.html', {
            'error': f'Ошибка при создании визуализации: {str(e)}'
        }) 