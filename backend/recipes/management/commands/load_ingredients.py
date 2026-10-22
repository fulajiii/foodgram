import json

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


DATA_PATH = settings.BASE_DIR.parent / 'data' / 'ingredients.json'


class Command(BaseCommand):
    help = 'Загружает ингредиенты из data/ingredients.json'

    def handle(self, *args, **options):
        # Открываем файл и превращаем JSON в список словарей.
        with open(DATA_PATH, encoding='utf-8') as file:
            data = json.load(file)

        # Из каждого словаря делаем объект Ingredient (в памяти).
        ingredients = [Ingredient(**item) for item in data]

        # Сохраняем все объекты в базу одним запросом.
        count_before = Ingredient.objects.count()
        Ingredient.objects.bulk_create(
            ingredients,
            ignore_conflicts=True,
        )
        added = Ingredient.objects.count() - count_before

        self.stdout.write(
            self.style.SUCCESS(f'Добавлено ингредиентов: {added}')
        )
