import csv
import os

from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import models, serializers
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для пользователей."""

    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (AllowAny,)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получение информации о пользователе."""
        return super().me(request)

    @action(detail=False,
            methods=['put'],
            url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        """Обновление аватара пользователя."""
        serializer = serializers.AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара пользователя."""
        if not request.user.avatar:
            raise exceptions.ValidationError('Аватар не существует.')
        request.user.avatar.delete()
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получение списка подписок."""
        subscriptions = request.user.subscriptions.all()
        authors = [subscription.author for subscription in subscriptions]
        page = self.paginate_queryset(authors)
        serializer = serializers.UserSerializer(
            page,
            many=True,
            context={'request': request, 'include_recipes': True}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['post'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        """Подписка на пользователя."""
        author = get_object_or_404(models.User, id=id)
        serializer = serializers.SubscriptionSerializer(
            data={'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        """Отписка от пользователя."""
        author = get_object_or_404(models.User, id=id)
        delete_count, _ = (
            models.Subscription.objects.filter(
                author=author, subscriber=request.user
            ).delete()
        )
        if not delete_count:
            raise exceptions.ValidationError(
                f'Не подписаны на пользователя {author.username}.'
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = (
        models.Recipe.objects.select_related('author')
        .prefetch_related('ingredient_in_recipe', 'tags')
    )
    permission_classes = (IsAuthorOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.RecipeReadSerializer
        return serializers.RecipeCreateSerializer

    @action(detail=True, methods=['get'], url_path='get-link',
            permission_classes=[AllowAny])
    def get_short_link(self, request, pk):
        """Метод для получения короткой ссылки на рецепт."""
        recipe = get_object_or_404(models.Recipe, id=pk)
        data = {'short-link': settings.SHORT_LINK_WRAPPER + recipe.short_link}
        return Response(data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """Метод для добавления рецепта в список покупок."""
        recipe = get_object_or_404(models.Recipe, id=pk)
        serializer = serializers.ShoppingCartSerializer(
            data={'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk):
        """Метод для удаления рецепта из списка покупок."""
        recipe = get_object_or_404(models.Recipe, id=pk)
        delete_count, _ = (
            request.user.shopping_cart.filter(recipe=recipe).delete()
        )
        if not delete_count:
            raise exceptions.ValidationError(
                f'"{recipe.name}" отсутствует в списке покупок.'
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        """Метод для добавления рецепта в избранное."""
        recipe = get_object_or_404(models.Recipe, id=pk)
        serializer = serializers.FavoriteSerializer(
            data={'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_from_favorites(self, request, pk):
        """Метод для удаления рецепта из избранного."""
        recipe = get_object_or_404(models.Recipe, id=pk)
        delete_count, _ = request.user.favorites.filter(
            recipe=recipe).delete()
        if not delete_count:
            raise exceptions.ValidationError(
                f'"{recipe.name}" отсутствует в избранном.'
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        try:
            """Метод для скачивания списка покупок."""
            ingredients = (
                models.RecipeIngredient.objects
                .filter(recipe__shopping_cart__user=request.user)
                .values(
                    'ingredient__name',
                    'ingredient__measurement_unit'
                )
                .annotate(total_amount=Sum('amount'))
            )
            if not ingredients.exists():
                return Response(
                    {'error': 'Список покупок пуст'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = (
                'attachment; filename="shopping_list.csv"'
            )
            writer = csv.writer(response)
            writer.writerow(['Ингредиент', 'Количество', 'Ед. изм.'])
            for ingredient in ingredients:
                writer.writerow([
                    ingredient['ingredient__name'],
                    ingredient['total_amount'],
                    ingredient['ingredient__measurement_unit']
                ])
            return response
        except Exception:
            return Response(
                {'error': 'Ошибка при формировании списка покупок'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""

    serializer_class = serializers.TagSerializer
    permission_classes = (AllowAny,)
    queryset = models.Tag.objects.all()
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    serializer_class = serializers.IngredientSerializer
    permission_classes = (AllowAny,)
    queryset = models.Ingredient.objects.all()
    pagination_class = None


@api_view(('GET',))
@permission_classes([AllowAny])
def redirect_to_recipe(request, short_link):
    try:
        recipe = get_object_or_404(models.Recipe, short_link=short_link)
        recipe_url = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return HttpResponseRedirect(recipe_url)
    except Exception:
        return Response(
            {'error': 'Не удалось перенаправить по короткой ссылке'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def redoc_view(request):
    """View для отображения документации Redoc."""
    redoc_path = os.path.join(settings.BASE_DIR, 'docs', 'redoc.html')

    try:
        with open(redoc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content)
    except FileNotFoundError:
        return HttpResponse(
            f"Redoc file not found at: {redoc_path}", status=404
        )


def openapi_schema_view(request):
    """View для отдачи схемы OpenAPI."""
    schema_path = os.path.join(
        settings.BASE_DIR, 'docs', 'openapi-schema.yml'
    )

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            content = f.read()
        response = HttpResponse(content, content_type='application/x-yaml')
        return response
    except FileNotFoundError:
        return HttpResponse(
            f"Schema file not found at: {schema_path}", status=404
        )
