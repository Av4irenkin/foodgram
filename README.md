# Foodgram - «Продуктовый помощник»

[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.15-red.svg)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-🐳-blue.svg)](https://www.docker.com/)

Foodgram - это веб-приложение для публикации рецептов. Пользователи могут создавать рецепты, добавлять их в избранное, подписываться на других авторов и формировать список покупок.

**Проект доступен по адресу:** [https://foodgram1338.hopto.org/](https://foodgram1338.hopto.org/)

- **API документация:** [https://foodgram1338.hopto.org/api/docs/](https://foodgram1338.hopto.org/api/docs/)
- **Админка:** [https://foodgram1338.hopto.org/admin/](https://foodgram1338.hopto.org/admin/)

## Технологии

- **Backend:** Django 4.2 + Django REST Framework
- **Database:** PostgreSQL
- **Frontend:** React (в процессе разработки)
- **Containerization:** Docker + Docker Compose
- **Web Server:** Nginx
- **CI/CD:** GitHub Actions
- **Deployment:** Yandex Cloud

## Функциональность

### Аутентификация и пользователи
- Регистрация и авторизация по email
- JWT-токены для API
- Кастомная модель пользователя с аватарами
- Подписки на других пользователей

### Рецепты
- Создание, редактирование, удаление рецептов
- Система тегов (завтрак, обед, ужин)
- Ингредиенты с единицами измерения
- Изображения рецептов
- Короткие ссылки для шаринга

### Избранное и корзина
- Добавление рецептов в избранное
- Список покупок с возможностью скачивания
- Фильтрация по тегам, автору, избранному

### Поиск и фильтрация
- Поиск ингредиентов по названию
- Фильтрация рецептов по тегам и статусам
- Пагинация результатов

## Архитектура
```
foodgram/
├── backend/          # Django приложение
│   ├── api/         # Основное приложение
│   ├── backend/     # Настройки проекта
│   └── Dockerfile
├── frontend/         # React приложение
│   └── Dockerfile
├── nginx/           # Nginx конфигурация
│   └── nginx.conf
├── data/            # Фикстуры и данные
├── docker-compose.production.yml
└── .env
```

## Локальный запуск

### Требования
- Docker
- Docker Compose

## Быстрый старт

### Клонировать репозиторий
git clone https://github.com/Av4irenkin/foodgram.git

### Запустить контейнеры
cd foodgram
docker-compose up -d --build

### Применить миграции
docker-compose exec backend python manage.py migrate

### Загрузить ингредиенты
docker-compose exec backend python manage.py loaddata new_ingredients.json

### Создать суперпользователя
docker-compose exec backend python manage.py createsuperuser

## Production деплой
Проект настроен с CI/CD через GitHub Actions. При пуше в ветку main автоматически:
1. Запускаются тесты
2. Собираются Docker образы
3. Образы пушатся в Docker Hub
4. Происходит деплой на сервер

## Пример .env файла
```
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-domain.com
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
SHORT_LINK_WRAPPER=https://your-domain/s/
CSRF_TRUSTED_ORIGINS=https://your-domain
```

## Автор
Автор проекта: [Av4irenkin](https://github.com/Av4irenkin)
