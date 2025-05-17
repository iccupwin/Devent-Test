app.conf.beat_schedule = {
    'update-planfix-vector-store': {
        'task': 'chat.tasks.update_planfix_vector_store',
        'schedule': 300.0,  # каждые 5 минут
    },
} 