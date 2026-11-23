from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

AUTHORS = {
    'foodgram-demo-anna': ('Анна', 'Петрова'),
    'foodgram-demo-boris': ('Борис', 'Соколов'),
}

RECIPES = (
    (
        'foodgram-demo-anna',
        'Овсяная каша с яблоком',
        'Сварите хлопья на молоке. Нарежьте яблоко и добавьте в кашу.',
        15,
        ('Демо: завтрак', 'demo-breakfast'),
        (('овсяные хлопья', 'г', 80), ('молоко', 'мл', 200),
         ('яблоки', 'г', 100)),
        '#e8c992',
    ),
    (
        'foodgram-demo-anna',
        'Салат из огурцов и помидоров',
        'Нарежьте овощи и перемешайте с оливковым маслом.',
        10,
        ('Демо: салат', 'demo-salad'),
        (('огурцы', 'г', 120), ('помидоры', 'г', 160),
         ('оливковое масло', 'г', 15)),
        '#9fc5a3',
    ),
    (
        'foodgram-demo-boris',
        'Йогурт с яблоком и бананом',
        'Нарежьте фрукты и смешайте с йогуртом.',
        5,
        ('Демо: завтрак', 'demo-breakfast'),
        (('йогурт натуральный', 'г', 150), ('яблоки', 'г', 80),
         ('бананы', 'г', 100)),
        '#e6ae9c',
    ),
)


class Command(BaseCommand):
    help = 'Добавляет двух демонстрационных авторов и три рецепта.'

    @transaction.atomic
    def handle(self, *args, **options):
        user_model = get_user_model()
        authors = {}
        for username, (first_name, last_name) in AUTHORS.items():
            authors[username], _ = user_model.objects.select_for_update(
            ).get_or_create(
                email=f'{username}@example.org',
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'password': make_password(None),
                },
            )

        created_count = 0
        for username, name, text, minutes, tag, ingredients, color in RECIPES:
            author = authors[username]
            if Recipe.objects.filter(author=author, name=name).exists():
                continue

            recipe_ingredients = []
            for ingredient_name, unit, amount in ingredients:
                try:
                    ingredient = Ingredient.objects.get(
                        name=ingredient_name, measurement_unit=unit
                    )
                except Ingredient.DoesNotExist as error:
                    raise CommandError(
                        'Сначала запустите python manage.py load_ingredients.'
                    ) from error
                recipe_ingredients.append(
                    RecipeIngredient(ingredient=ingredient, amount=amount)
                )

            tag_name, slug = tag
            recipe_tag, _ = Tag.objects.get_or_create(
                slug=slug, defaults={'name': tag_name}
            )
            recipe = Recipe(
                author=author, name=name, text=text, cooking_time=minutes
            )
            image = BytesIO()
            Image.new('RGB', (320, 200), color).save(image, format='PNG')
            recipe.image.save(f'{slug}.png', ContentFile(image.getvalue()))
            recipe.tags.add(recipe_tag)
            for item in recipe_ingredients:
                item.recipe = recipe
            RecipeIngredient.objects.bulk_create(recipe_ingredients)
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Добавлено деморецептов: {created_count}')
        )
