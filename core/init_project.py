import json
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
PROJECTS_DIR = ROOT_DIR / "projects"

def init_project(project_name):
    project_path = PROJECTS_DIR / project_name
    config_path = project_path / "config" / "project.json"
    input_dir = project_path / "input"
    
    input_dir.mkdir(parents=True, exist_ok=True)
    (project_path / "config").mkdir(parents=True, exist_ok=True)
    
    old_config = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            old_config = json.load(f)
        backup = config_path.with_suffix(".json.bak")
        with open(backup, "w", encoding="utf-8") as f:
            json.dump(old_config, f, ensure_ascii=False, indent=2)
        print(f"💾 Бэкап: {backup.name}")
    
    # Карта: имя файла -> старые данные сцены (для сохранения ID/названия/этажа)
    old_by_image = {}
    max_num = 0
    if "scenes" in old_config:
        for s in old_config["scenes"]:
            img = s.get("image")
            if img:
                old_by_image[img] = s
            sid = s.get("id", "")
            if sid.startswith("scene_"):
                try:
                    max_num = max(max_num, int(sid.replace("scene_", "")))
                except ValueError:
                    pass
    
    all_images = sorted([
        f for f in input_dir.iterdir() 
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png'] 
        and not f.name.lower().startswith(('plan', 'logo'))
    ])
    
    if not all_images:
        print(f"⚠️  В {input_dir} нет JPG-панорам.")
        return
    
    # Проверка на удаленные файлы
    current_images = {f.name for f in all_images}
    removed = set(old_by_image.keys()) - current_images
    if removed:
        print(f"\n⚠️  Удалены изображения:")
        for r in removed:
            print(f"   - {r} (был {old_by_image[r]['id']})")
        print(f"   ⚠️  Стрелки к этим сценам в links.json перестанут работать!\n")
    
    # Собираем сцены, сохраняя старые ID
    scenes = []
    new_count = 0
    for file in all_images:
        if file.name in old_by_image:
            scenes.append(old_by_image[file.name])
        else:
            max_num += 1
            new_count += 1
            scenes.append({
                "id": f"scene_{max_num:02d}",
                "name": f"Сцена {max_num}",
                "floor": 1,
                "image": file.name
            })
            print(f"➕ Новая: {file.name} → scene_{max_num:02d}")
    
    config = {
        "project_name": old_config.get("project_name", project_name),
        "start_scene": old_config.get("start_scene", scenes[0]["id"]),
        "floors": old_config.get("floors", [{"id": 1, "name": "1 этаж", "plan": "plan1.png"}]),
        "scenes": scenes
    }

    # Сохраняем настройку перехода (иначе теряется при каждом init_project)
    if "transition" in old_config:
        config["transition"] = old_config["transition"]
    
    scene_ids = {s["id"] for s in scenes}
    if config["start_scene"] not in scene_ids:
        config["start_scene"] = scenes[0]["id"]
        print(f"⚠️  Стартовая сцена была удалена → {config['start_scene']}")
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Проект '{project_name}': {len(scenes)} сцен (новых: {new_count})")
    print(f"\n👉 Следующий шаг: docker compose exec tour-app python3 core/build_tour.py {project_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str)
    args = parser.parse_args()
    init_project(args.name)
