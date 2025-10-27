from api.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from django.db.models import Exists, OuterRef
from django_filters import rest_framework as filters


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для рецептов по автору, тегам,
    нахождению в избранном и списке покупок.
    """

    author = filters.NumberFilter(
        field_name='author__id',
        label='id автора рецепта'
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Теги рецепта'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_user_favorites',
        label='Избранные рецепты'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_shopping_list',
        label='Рецепты в списке покупок'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def __init__(self, *args, **kwargs):
        """Инициализация с сохранением текущего пользователя."""
        super().__init__(*args, **kwargs)
        self.current_user = getattr(self.request, 'user', None)

    def filter_user_favorites(self, queryset, name, value):
        """Фильтрация рецептов по статусу избранного."""
        if not self.current_user or not self.current_user.is_authenticated:
            return queryset.none() if value else queryset
        favorites_subquery = Favorite.objects.filter(
            user=self.current_user,
            recipe=OuterRef('pk')
        )
        if value:
            return queryset.filter(Exists(favorites_subquery))
        else:
            return queryset.exclude(Exists(favorites_subquery))

    def filter_shopping_list(self, queryset, name, value):
        """Фильтрация рецептов по наличию в корзине покупок."""
        if not self.current_user or not self.current_user.is_authenticated:
            return queryset.none() if value else queryset
        shopping_cart_subquery = ShoppingCart.objects.filter(
            user=self.current_user,
            recipe=OuterRef('pk')
        )
        if value:
            return queryset.filter(Exists(shopping_cart_subquery))
        else:
            return queryset.exclude(Exists(shopping_cart_subquery))


class IngredientFilter(filters.FilterSet):
    """Фильтр ингредиентов по начальным символам названия."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
