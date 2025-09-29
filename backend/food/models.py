from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email')
    avatar = models.ImageField(
        null=True,
        blank=True,
        upload_to='avatars/',
        verbose_name='Изображение профиля'
    )
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'Пользователь {self.username}'


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'Тег {self.name}'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=50,
        verbose_name='единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        related_name='author_followers',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    follower = models.ForeignKey(
        User,
        related_name='follower_followers',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'follower'],
                name='author_follower'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.follower} подписан на {self.author}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Название',
    )
    description = models.TextField(
        verbose_name='Описание',
    )
    image = models.ImageField(
        upload_to='recipes_images/',
        verbose_name='Изображение',
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления (мин)'
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        related_name='recipes'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Дата создания'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент в рецепте'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient'
            )
        ]
    
    def __str__(self):
        return f'{self.ingredient} в {self.recipe}'


class BaseUserRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)s_relations'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)s_relations'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.recipe} от {self.user}'


class Favorite(BaseUserRecipe):
    class Meta(BaseUserRecipe.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCartItem(BaseUserRecipe):
    class Meta(BaseUserRecipe.Meta):
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Корзина покупок'
