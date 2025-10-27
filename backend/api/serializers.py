import base64

from api.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                        ShoppingCart, Subscription, Tag, User)
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Сериализатор для преобразования изображений в формат Base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для выдачи информации о пользователе."""

    avatar = Base64ImageField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context.get('include_recipes'):
            self.fields.pop('recipes', None)
            self.fields.pop('recipes_count', None)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscribers.filter(subscriber=request.user).exists()
        return False

    def get_recipes(self, obj):
        if not self.context.get('include_recipes'):
            return None
        request = self.context.get('request')
        recipes_limit = (
            request.query_params.get('recipes_limit') if request else None
        )
        try:
            limit = int(recipes_limit) if recipes_limit else None
        except (TypeError, ValueError):
            limit = None
        recipes = obj.recipes.all()
        if limit and limit > 0:
            recipes = recipes[:limit]
        return ShortRecipeSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        if hasattr(obj, 'recipes_count'):
            return obj.recipes_count
        return obj.recipes.count()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя."""

    avatar = Base64ImageField(required=True, allow_empty_file=False)

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для единицы измерения ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для получения информации о рецепте."""

    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientsSerializer(
        source='ingredient_in_recipe', read_only=True, many=True
    )
    image = Base64ImageField(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shopping_cart.filter(user=request.user).exists()
        return False

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'cooking_time', 'image', 'author',
            'ingredients', 'tags', 'is_favorited', 'is_in_shopping_cart'
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и рекатирования рецепта."""

    ingredients = RecipeIngredientsSerializer(
        required=True, allow_empty=False, many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), allow_empty=False, many=True,
    )
    image = Base64ImageField(required=True, allow_empty_file=False)

    class Meta:
        model = Recipe
        fields = (
            'name', 'text', 'cooking_time', 'image', 'ingredients', 'tags'
        )

    @staticmethod
    def _add_ingredients(recipe, ingredients):
        """Метод для создания и редактрования ингредиентов в рецепте."""
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._add_ingredients(recipe, ingredients)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        recipe = super().update(recipe, validated_data)
        if tags is not None:
            recipe.tags.set(tags)
        if ingredients is not None:
            recipe.ingredient_in_recipe.all().delete()
            self._add_ingredients(recipe, ingredients)
        return recipe

    def validate(self, data):
        self._check_ingredients(data.get('ingredients'))
        self._check_tags(data.get('tags'))
        return data

    def _check_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Рецепт должен содержать ингредиенты'
            )
        seen_ingredients = set()
        for item in ingredients:
            ingredient_id = item['ingredient'].id
            if ingredient_id in seen_ingredients:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться'
                )
            seen_ingredients.add(ingredient_id)

    def _check_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Укажите теги для рецепта')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не могут повторяться')

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для короткого представления рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""

    class Meta:
        model = Subscription
        fields = ('author', 'subscriber')
        read_only_fields = ('subscriber',)

    def validate(self, data):
        request = self.context.get('request')
        author = data['author']
        subscriber = (
            request.user
            if request and request.user.is_authenticated
            else None
        )
        if not subscriber:
            raise serializers.ValidationError(
                'Требуется авторизация'
            )
        if subscriber == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        if Subscription.objects.filter(
            author=author, subscriber=subscriber
        ).exists():
            raise serializers.ValidationError(
                f'{subscriber.username} уже подписан '
                f'на пользователя {author.username}.'
            )

        data['subscriber'] = subscriber
        return data

    def to_representation(self, instance):
        context = {'include_recipes': True}
        if 'request' in self.context:
            context['request'] = self.context['request']
        return UserSerializer(instance.author, context=context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в список покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        read_only_fields = ('user',)

    def validate(self, data):
        request = self.context.get('request')
        recipe = data['recipe']
        user = (
            request.user
            if request and request.user.is_authenticated
            else None
        )
        if not user:
            raise serializers.ValidationError('Требуется авторизация')
        if user.shopping_cart.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт "{recipe.name}" уже находится в списке покупок'
            )
        data['user'] = user
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в избранное."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        read_only_fields = ('user',)

    def validate(self, data):
        request = self.context.get('request')
        recipe = data['recipe']
        user = (
            request.user
            if request and request.user.is_authenticated
            else None
        )
        if not user:
            raise serializers.ValidationError('Требуется авторизация')
        if user.favorites.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт "{recipe.name}" уже находится в избранном.'
            )
        data['user'] = user
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context=self.context
        ).data
