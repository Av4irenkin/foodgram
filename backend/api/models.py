from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.crypto import get_random_string


class User(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.EmailField(unique=True, verbose_name='Email')
    avatar = models.ImageField(
        null=True,
        blank=True,
        upload_to='avatars/',
        verbose_name='Аватар'
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'Пользователь {self.username}'


class Tag(models.Model):
    """Модель для тега рецепта."""

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название',
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'Тег {self.name}'


class Ingredient(models.Model):
    """Модель для ингредиента."""

    name = models.CharField(
        max_length=150,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=50
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_measurement_unit_name'
            )
        ]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """Модель для подписки."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Пользователь'
    )
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'subscriber'),
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('subscriber')),
                name='self_subscribe'
            )
        ]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'


class Recipe(models.Model):
    """Модель для рецепта."""

    name = models.CharField(
        max_length=150,
        verbose_name='Название',
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(1, message='Минимум 1 минута'),
            MaxValueValidator(10000, message='Максимум 10000 минут')
        ],
        help_text='Время приготовления (мин)'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/images/'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    short_link = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        editable=False
    )

    def get_short_link(
        self, length=10, attempt=10
    ):
        """Метод генерации короткой ссылки."""
        for _ in range(attempt):
            short_link = get_random_string(length=length)
            if not self.__class__.objects.filter(
                short_link=short_link
            ).exists():
                self.short_link = short_link
                break
        else:
            raise ValueError(
                'Не удалось сгенерировать уникальную короткую ссылку'
            )

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.get_short_link()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'

    def __str__(self):
        return f'Рецепт {self.name}'


class RecipeIngredient(models.Model):
    """Модель для ингредиента в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(1, message='Минимум 1 единица'),
            MaxValueValidator(10000, message='Максимум 10000 единиц')
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.amount} {self.ingredient.measurement_unit} '
                f'{self.ingredient} в рецепте {self.recipe}')


class Favorite(models.Model):
    """Модель для избранных рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return (f'"{self.recipe}" в избранном {self.user}')


class ShoppingCart(models.Model):
    """Модель для списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart_list'
            )
        ]

    def __str__(self):
        return (f'"{self.recipe}" в списке покупок {self.user}')
