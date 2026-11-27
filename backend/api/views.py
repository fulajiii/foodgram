from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    UserWithRecipesSerializer,
)


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UserViewSet(DjoserUserViewSet):
    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def avatar(self, request):
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.subscriptions.filter(author=author).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Subscription.objects.create(user=user, author=author)
        serializer = UserWithRecipesSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if not user.subscriptions.filter(author=author).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.subscriptions.filter(author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        authors = User.objects.filter(followers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'recipe_ingredients__ingredient'
    )
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_recipe(self, request, pk, model, error_message):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self._add_recipe(
            request, pk, Favorite, 'Рецепт уже добавлен в избранное.'
        )

    def _remove_recipe(self, request, pk, model, error_message):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if not model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return self._remove_recipe(
            request, pk, Favorite, 'Этот рецепт не был добавлен в избранное.'
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self._add_recipe(
            request, pk, ShoppingCart, 'Этот рецепт уже добавлен в корзину.'
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self._remove_recipe(
            request, pk, ShoppingCart, 'Рецепт не был добавлен в корзину.'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(
            total=Sum('amount')
        ).order_by('ingredient__name')
        lines = [
            f'{item["ingredient__name"]} '
            f'({item["ingredient__measurement_unit"]}) — {item["total"]}'
            for item in ingredients
        ]
        response = HttpResponse(
            '\n'.join(lines),
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        link = request.build_absolute_uri(f'/s/{recipe.pk}/')
        return Response({'short-link': link})


def recipe_short_link(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect(f'/recipes/{recipe.pk}/')
