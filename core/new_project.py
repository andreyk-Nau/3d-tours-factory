import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
PROJECTS_DIR = ROOT_DIR / "projects"

def create_project(project_name):
    project_path = PROJECTS_DIR / project_name
    if project_path.exists():
        print(f"⚠️ Проект '{project_name}' уже существует!")
        return
    
    (project_path / "input").mkdir(parents=True)
    (project_path / "config").mkdir(parents=True)
    (project_path / "output").mkdir(parents=True)
    
    print(f"✅ Папка для проекта '{project_name}' создана!")
    print(f"👉 1. Положите ваши JPG-панорамы и планы (plan1.png) в: {project_path}/input/")
    print(f"👉 2. Затем запустите одну команду: docker compose exec tour-app python3 core/deploy.py {project_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str, help="Имя проекта")
    args = parser.parse_args()
    create_project(args.name)
