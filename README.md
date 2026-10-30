# 🏭 3D Tour Factory

Универсальная фабрика для сборки интерактивных 3D-туров (виртуальных прогулок) на базе Pannellum, Python и Docker.

Этот репозиторий содержит **движок** (скрипты сборки, редакторы, шаблоны). Исходники туров (панорамы, планы) лежат в папке `projects/`, которая не попадает в Git.

## 🚀 Ключевые возможности

*   **Smart Transition:** При переходе по стрелке камера автоматически разворачивается спиной к двери (если в целевой комнате есть обратная стрелка).
*   **Интерактивная планировка:** Поддержка нескольких этажей. Плавный зум в точку курсора, перетаскивание мышью/пальцем, поворот на 90°.
*   **Мультиформатность:** Поддержка планов и логотипов в форматах `.jpg`, `.png` и `.svg` (с автоопределением).
*   **Валидатор:** Встроенный в редактор поиск «односторонних» переходов.
*   **Кэш-бастинг:** Автоматическая защита от кэша браузера при обновлении панорам (`?v=timestamp`).
*   **Инфо-модалка:** Вынос текста «О проекте» в отдельный `info.html` с поддержкой любых HTML-тегов и медиа из папки `assets`.

## 📂 Структура репозитория (Движок)

```text
├── core/               # Python-скрипты фабрики
│   ├── build_tour.py   # Нарезка тайлов, сборка tour.json
│   ├── init_project.py # Сканирование панорам, создание project.json
│   ├── make_dist.py    # Упаковка готового тура в ZIP
│   ├── new_project.py  # Создание нового проекта
│   ├── save_factory.py # Бэкап движка
│   └── server.py       # Локальный сервер + API автосохранения
├── editors/            # Веб-интерфейсы для настройки туров
│   ├── editor.html     # Редактор стрелок и настроек сцен
│   └── map_editor.html # Редактор точек на планировке
├── templates/          # Шаблоны для финального сайта
│   ├── index.html      # Главный HTML-шаблон тура
│   └── .htaccess       # Настройки кэширования для Apache
├── tools/              # Pannellum utils (нарезка на multires)
├── docker-compose.yml
└── Dockerfile
```

💻 Быстрый старт
1. Клонируйте репозиторий и запустите контейнеры:

docker compose up -d --build

2. Создайте новый проект:
docker compose exec tour-app python3 core/new_project.py my_tour

3. Скопируйте панорамы, планы и логотип в projects/my_tour/input/.

4. Сгенерируйте конфигурацию сцен:
docker compose exec tour-app python3 core/init_project.py my_tour

5. Нарежьте тайлы (займет время):
docker compose exec tour-app python3 core/build_tour.py my_tour

6. Откройте редактор в браузере:
http://localhost:8000/editors/editor.html?project=my_tour
(Не забудьте в редакторе нажать "Сохранить" для links.json и project.json).

🛠 Шпаргалка команд и флагов
Задача	Команда
Создать новый проект	docker compose exec tour-app python3 core/new_project.py <name>
Обновить project.json	docker compose exec tour-app python3 core/init_project.py <name>
Только пересобрать JSON	docker compose exec tour-app python3 core/build_tour.py <name> --skip-tiles
Пересоздать 1 сцену (тайлы)	docker compose exec tour-app python3 core/build_tour.py <name> --force-scene scene_05
Пересоздать ВСЕ тайлы	docker compose exec tour-app python3 core/build_tour.py <name> --force-all
Упаковать для хостинга в ZIP	docker compose exec tour-app python3 core/make_dist.py <name>
Сделать бэкап фабрики	docker compose exec tour-app python3 core/save_factory.py

🌐 Локальный сервер
В docker-compose.yml уже настроен автоматический запуск core/server.py. Он работает в фоне и пересобирает тур при каждом нажатии кнопки «Сохранить» в редакторе.
Если вы внесли изменения в код server.py, перезапустите его:
docker compose restart tour-app
