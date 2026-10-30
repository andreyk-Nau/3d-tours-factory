import zipfile
import os
from pathlib import Path
from datetime import datetime

# Корень проекта (на уровень выше папки core)
ROOT_DIR = Path(__file__).parent.parent.resolve()
BACKUP_DIR = ROOT_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Что сохраняем (папки и файлы)
INCLUDE_DIRS = ['core', 'editors', 'templates', 'tools']
INCLUDE_FILES = ['docker-compose.yml', 'Dockerfile', 'README.md', '.gitignore']
EXCLUDE_DIRS = {'__pycache__', '.venv', '.git', 'projects', 'backups'}

def save_factory():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    zip_path = BACKUP_DIR / f"factory_backup_{timestamp}.zip"
    
    print("🏭 Собираю бэкап фабрики (скрипты, шаблоны, редакторы)...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Сохраняем папки
        for d in INCLUDE_DIRS:
            dir_path = ROOT_DIR / d
            if not dir_path.exists(): continue
            
            for root, dirs, files in os.walk(dir_path):
                # Очищаем список dirs на месте, чтобы os.walk не заходил в исключенные папки
                dirs[:] = [x for x in dirs if x not in EXCLUDE_DIRS]
                
                for file in files:
                    if file.endswith('.pyc') or file == '.DS_Store':
                        continue
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(ROOT_DIR)
                    zipf.write(file_path, arcname)
                    
        # Сохраняем отдельные файлы в корне
        for f in INCLUDE_FILES:
            file_path = ROOT_DIR / f
            if file_path.exists():
                zipf.write(file_path, f)
                
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Фабрика сохранена!")
    print(f"📁 Файл: {zip_path}")
    print(f"📊 Размер: {size_mb:.2f} МБ")

if __name__ == "__main__":
    save_factory()
