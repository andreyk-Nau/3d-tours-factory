# Берем официальный легкий образ Python
FROM python:3.11-slim

# Отключаем интерактивные запросы при установке пакетов
ENV DEBIAN_FRONTEND=noninteractive

# Устанавливаем системные утилиты, которые нужны для работы скриптов
# ffmpeg и imagemagick - для работы с картинками
# libgl1 и libglib2.0-0 - обязательны для работы OpenCV
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    hugin-tools \
    enblend \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя с UID 1000 (как у вас в WSL), 
# чтобы файлы, создаваемые контейнером, не были "залочены" под root
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -m -u ${USER_ID} -g appuser appuser

# Задаем рабочую директорию
WORKDIR /app

# Устанавливаем Python-библиотеки
RUN pip install --no-cache-dir \
    rawpy \
    imageio \
    pillow \
    numpy \
    opencv-python-headless \
    ollama

# Переключаемся на нашего пользователя
USER appuser

# По умолчанию контейнер будет просто запускать веб-сервер
CMD ["python3", "-m", "http.server", "8000"]
