# Foodgram

Сервис для публикации рецептов, подписок на авторов и составления списка покупок.

Создайте `infra/.env` на основе `infra/.env.example`. Задайте `SECRET_KEY` и `POSTGRES_PASSWORD`. Для учебной ВМ добавьте ее внешний IP или домен в `ALLOWED_HOSTS`.

## Локальный запуск

```bash
docker compose -f infra/docker-compose.yml build
docker compose -f infra/docker-compose.yml up -d
```

Приложение доступно на `http://localhost/`, документация по пути `/api/docs/`, админка по пути `/admin/`.

## Запуск на учебной ВМ

Из корня клонированного репозитория выполните:

```bash
docker compose -f infra/docker-compose.production.yml pull
docker compose -f infra/docker-compose.production.yml up -d
docker compose -f infra/docker-compose.production.yml exec backend python manage.py seed_demo
docker compose -f infra/docker-compose.production.yml exec backend python manage.py createsuperuser
```
