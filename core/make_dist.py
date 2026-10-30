import shutil
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
PROJECTS_DIR = ROOT_DIR / "projects"

def make_dist(project_name):
    project_path = PROJECTS_DIR / project_name
    out_dir = project_path / "output"
    dist_dir = project_path / "dist"
    
    zip_name = project_path / f"{project_name}_website"

    if not out_dir.exists():
        print(f"❌ Ошибка: Папка {out_dir} не найдена. Сначала соберите тур (build_tour.py).")
        return

    print(f"📦 Собираю дистрибутив для проекта '{project_name}'...")

    # Очищаем старую папку dist (если осталась от прошлых запусков)
    if dist_dir.exists():
        print(f"🧹 Удаляю старую папку dist...")
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Список того, что обязательно копируем
    include_files = ["index.html", "tour.json", "map_points.json", ".htaccess", "info.html"]
    include_dirs = ["thumbnails", "multires", "assets"]
    
    # Ищем планы и логотипы (любые расширения)
    for f in out_dir.iterdir():
        if f.is_file() and f.name.lower().startswith(("plan", "logo")):
            include_files.append(f.name)

    # Копируем файлы
    for item in include_files:
        src = out_dir / item
        if src.exists():
            shutil.copy2(src, dist_dir / item)
            print(f"  + {item}")
        else:
            if item not in ["map_points.json", ".htaccess", "info.html"]:
                print(f"  ⚠️  Внимание: {item} не найден")

    # Копируем папки
    for item in include_dirs:
        src = out_dir / item
        if src.exists():
            print(f"  + {item}/ (это может занять минуту...)")
            shutil.copytree(src, dist_dir / item)
        else:
            if item != "assets": # assets может не быть, это нормально
                print(f"  ❌ Ошибка: Папка {item} не найдена!")

    # Упаковываем в ZIP
    print(f"\n🤐 Упаковываю в архив...")
    
    old_zip = Path(f"{zip_name}.zip")
    if old_zip.exists():
        old_zip.unlink()
        
    shutil.make_archive(str(zip_name), 'zip', dist_dir)
    
    zip_path = Path(f"{zip_name}.zip")
    size_mb = zip_path.stat().st_size / (1024 * 1024)

    # Очищаем dist после упаковки — она больше не нужна
    print(f"🧹 Удаляю временную папку dist...")
    shutil.rmtree(dist_dir)

    print(f"\n✅ УСПЕХ! Дистрибутив готов к загрузке на хостинг.")
    print(f"📁 Файл: {zip_path}")
    print(f"📊 Размер: {size_mb:.1f} МБ")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=str, help="Имя проекта (например, house_854)")
    args = parser.parse_args()
    make_dist(args.project)
