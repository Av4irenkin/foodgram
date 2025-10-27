from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, Tag, User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админ-панель для кастомной модели пользователя."""

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': (
            'first_name',
            'last_name',
            'email',
            'avatar'
        )}),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-панель для тегов."""

    list_display = ('id', 'name', 'slug')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-панель для ингредиентов."""

    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientInline(admin.TabularInline):
    """Inline для отображения ингредиентов в рецепте."""

    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-панель для рецептов."""

    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'pub_date',
        'short_link',
        'favorites_count'
    )
    list_display_links = ('id', 'name')
    list_filter = ('tags', 'pub_date', 'author')
    search_fields = ('name', 'author__username', 'text')
    readonly_fields = ('pub_date', 'short_link', 'favorites_count')
    inlines = (RecipeIngredientInline,)

    fieldsets = (
        (None, {
            'fields': ('name', 'author', 'text', 'cooking_time', 'image')
        }),
        ('Дополнительно', {
            'fields': ('tags', 'pub_date', 'short_link', 'favorites_count'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Аннотируем queryset количеством добавлений в избранное."""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _favorites_count=Count('favorites', distinct=True)
        )
        return queryset

    def favorites_count(self, obj):
        """Отображаем количество добавлений в избранное."""
        return obj._favorites_count
    favorites_count.short_description = 'В избранном'
    favorites_count.admin_order_field = '_favorites_count'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель для подписок."""

    list_display = ('id', 'subscriber', 'author')
    list_display_links = ('id', 'subscriber')
    list_filter = ('author',)
    search_fields = ('subscriber__username', 'author__username')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-панель для избранного."""

    list_display = ('id', 'user', 'recipe')
    list_display_links = ('id', 'user')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-панель для списка покупок."""

    list_display = ('id', 'user', 'recipe')
    list_display_links = ('id', 'user')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админ-панель для связи рецепт-ингредиент."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_display_links = ('id', 'recipe')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe__name', 'ingredient__name')
