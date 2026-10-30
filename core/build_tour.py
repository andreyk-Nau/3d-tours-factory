import json
import argparse
import subprocess
import shutil
import time
from pathlib import Path
from PIL import Image

ROOT_DIR = Path(__file__).parent.parent.resolve()
PROJECTS_DIR = ROOT_DIR / "projects"

def build_project(project_name, skip_tiles=False, force_all=False, force_scenes=None):
    force_scenes = set(force_scenes or [])
    project_path = PROJECTS_DIR / project_name
    config_file = project_path / "config" / "project.json"
    links_file = project_path / "config" / "links.json"
    out_dir = project_path / "output"
    
    if not config_file.exists():
        print(f"❌ {config_file} не найден. Сначала запустите init_project.py")
        return
    
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    print(f"✅ Проект: {config['project_name']} ({len(config['scenes'])} сцен)")
    
    (out_dir / "multires").mkdir(parents=True, exist_ok=True)
    (out_dir / "thumbnails").mkdir(parents=True, exist_ok=True)
    
    # ── НАРЕЗКА ТАЙЛОВ ─────────────────────────────────────────────
    if not skip_tiles:
        sliced = 0
        skipped = 0
        for scene in config["scenes"]:
            sid = scene["id"]
            img_path = project_path / "input" / scene["image"]
            
            if not img_path.exists():
                print(f"⚠️  {scene['image']} не найден, пропускаю")
                continue
            
            tile_dir = out_dir / "multires" / sid
            is_valid = tile_dir.exists() and any(tile_dir.iterdir())
            must_rebuild = force_all or sid in force_scenes
            
            if not is_valid or must_rebuild:
                reason = "новый" if not is_valid else "принудительно"
                print(f"⏳ {sid} ({scene['image']}) — {reason}...")
                if tile_dir.exists():
                    shutil.rmtree(tile_dir)
                result = subprocess.run([
                    "python3", "tools/pannellum/utils/multires/generate.py",
                    "-n", "nona", "-o", str(tile_dir), "-s", "512",
                    "-f", "4096", "-c", "2976", "-q", "90", str(img_path)
                ], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Ошибка {sid}: {result.stderr[-300:]}")
                    continue
                sliced += 1
            else:
                skipped += 1
            
            thumb = out_dir / "thumbnails" / f"{sid}.jpg"
            if not thumb.exists() or must_rebuild:
                try:
                    with Image.open(img_path) as img:
                        img.thumbnail((400, 200))
                        img.save(thumb, "JPEG", quality=85)
                except Exception as e:
                    print(f"⚠️  Превью {sid}: {e}")
        
        print(f"✅ Нарезано: {sliced}, пропущено: {skipped}")
    # ───────────────────────────────────────────────────────────────
    
    links = {}
    if links_file.exists():
        with open(links_file, "r", encoding="utf-8") as f:
            links = json.load(f)
    
    scenes_data = {}
    for scene in config["scenes"]:
        sid = scene["id"]
        cfg_path = out_dir / "multires" / sid / "config.json"
        multi = {}
        if cfg_path.exists():
            with open(cfg_path, "r") as f:
                multi = json.load(f).get("multiRes", {})
                
        if multi:
            multi["basePath"] = f"multires/{sid}"
            
            # Cache busting: ставим ?v= в extension, т.к. Pannellum клеит его в конец URL
            cache_version = int(time.time()) if not skip_tiles else 1
            orig_ext = multi.get("extension", "jpg")
            if "?" not in orig_ext:
                multi["extension"] = f"{orig_ext}?v={cache_version}"
        
        scenes_data[sid] = {
            "title": scene["name"],
            "type": "multires" if multi else "equirectangular",
            "hfov": 100, "minHfov": 60,
            "multiRes": multi if multi else None,
            "panorama": f"input/{scene['image']}" if not multi else None,
            "floor": scene.get("floor", 1),
            "hotSpots": []
        }
        
        if sid in links:
            for link in links[sid]:
                target = link["target"]
                if target in [s["id"] for s in config["scenes"]]:
                    target_name = next((s["name"] for s in config["scenes"] if s["id"] == target), target)
                    scenes_data[sid]["hotSpots"].append({
                        "pitch": link["pitch"], "yaw": link["yaw"],
                        "type": "scene", "text": f"→ {target_name}", "sceneId": target
                    })
    
    # ── АВТООПРЕДЕЛЕНИЕ РАСШИРЕНИЯ ПЛАНОВ И УГЛА ПОВОРОТА ──────────
    floors_data = config.get("floors", [])
    for floor in floors_data:
        plan_name = floor.get("plan", "")
        if plan_name:
            base_name = plan_name.rsplit('.', 1)[0]
            for ext in ['.png', '.jpg', '.jpeg', '.svg', '.webp', '.PNG', '.JPG', '.JPEG', '.SVG']:
                if (project_path / "input" / f"{base_name}{ext}").exists():
                    floor["plan"] = f"{base_name}{ext}"
                    break
        
        # Гарантируем наличие угла поворота (по умолчанию 0)
        if "rotation" not in floor:
            floor["rotation"] = 0
    # ───────────────────────────────────────────────────────────────

    # ── АВТООПРЕДЕЛЕНИЕ ЛОГОТИПА ───────────────────────────────────
    logo_file = None
    for ext in ['.svg', '.png', '.jpg', '.jpeg', '.webp', '.SVG', '.PNG', '.JPG', '.JPEG']:
        candidate = project_path / "input" / f"logo{ext}"
        if candidate.exists():
            logo_file = f"logo{ext}"
            break
    # ───────────────────────────────────────────────────────────────

    tour_config = {
        "default": {
            "firstScene": config["start_scene"],
            "author": "HoltsovHouse",
            "sceneFadeDuration": 0 if config.get("transition") == "zoom" else 1000,
            "autoLoad": True,
            "transition": config.get("transition", "smart_fade"),
            "logo": logo_file
        },
        "scenes": scenes_data,
        "floors": floors_data
    }
    
    with open(out_dir / "tour.json", "w", encoding="utf-8") as f:
        json.dump(tour_config, f, ensure_ascii=False, indent=2)
    
    # ── КОПИРОВАНИЕ ШАБЛОНОВ И КОНФИГОВ ────────────────────────────
    shutil.copy(ROOT_DIR / "templates" / "index.html", out_dir / "index.html")
    
    htaccess_src = ROOT_DIR / "templates" / ".htaccess"
    if htaccess_src.exists():
        shutil.copy(htaccess_src, out_dir / ".htaccess")
        
    info_src = project_path / "config" / "info.html"
    if info_src.exists():
        shutil.copy(info_src, out_dir / "info.html")
        
    assets_dir = project_path / "config" / "assets"
    if assets_dir.exists():
        if (out_dir / "assets").exists():
            shutil.rmtree(out_dir / "assets")
        shutil.copytree(assets_dir, out_dir / "assets")
    
    for f in (project_path / "input").iterdir():
        if f.name.lower().startswith(("plan", "logo")):
            shutil.copy(f, out_dir / f.name)
            
    if (project_path / "config" / "map_points.json").exists():
        shutil.copy(project_path / "config" / "map_points.json", out_dir / "map_points.json")
    # ───────────────────────────────────────────────────────────────
    
    print(f"\n🎉 Готово! tour.json пересобран.")
    print(f"📁 {out_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сборка тура")
    parser.add_argument("project", type=str, help="Имя проекта")
    parser.add_argument("--skip-tiles", action="store_true", help="Только пересобрать JSON, без нарезки")
    parser.add_argument("--force-all", action="store_true", help="Пересоздать ВСЕ тайлы заново")
    parser.add_argument("--force-scene", action="append", default=[], metavar="SCENE_ID",
                        help="Пересоздать тайлы конкретной сцены (можно несколько раз)")
    args = parser.parse_args()
    build_project(args.project, args.skip_tiles, args.force_all, args.force_scene)
