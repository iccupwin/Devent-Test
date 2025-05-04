import os
from pathlib import Path

# Создание директории кэша
cache_dir = Path('chat/cache')
if not cache_dir.exists():
    print(f"Создаем директорию кэша: {cache_dir}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаем .gitkeep для отслеживания пустой директории
    gitkeep = cache_dir / '.gitkeep'
    with open(gitkeep, 'w') as f:
        pass
    
    print("Директория кэша создана успешно!")
else:
    print("Директория кэша уже существует.")