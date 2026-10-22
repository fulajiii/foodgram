from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag, ShoppingCart, Favorite


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'measurement_unit')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 2
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    search_fields = ('name', 'author__username')
    list_display = ('name', 'author',)
    list_filter = ('tags',)
    readonly_fields = ('favorites_count',)
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(Favorite, ShoppingCart)
class UserRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    search_fields = ('user__username', 'recipe__name')
