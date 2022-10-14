from django.db import models
from django.forms import model_to_dict
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Ingredient(models.Model):
    # добавить количество.
    name = models.CharField('Ингредиент', max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=16)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Ингредиет'
        verbose_name_plural = "Ингредиеты"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('Тэг', max_length=200)
    slug = models.CharField(
        'Слаг',
        max_length=200,
        unique=True
    )
    color = models.CharField('Цвет',max_length=16)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Тэг'
        verbose_name_plural = "Тэги"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField('Рецепт', max_length=200)
    text = models.TextField('Описание', blank=True, null=True)
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/', 
        null=True,  
        default=None
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(300)]
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name = 'Ингредиент'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        related_name='recipes',
        verbose_name = 'Тэг'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name = 'Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name = 'Рецепт'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        default=1,
        validators=[MinValueValidator(1),])

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name = 'Тэг'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name = 'Рецепт'
    )

    def __str__(self):
        return f'{self.tag} {self.recipe}'

'''
class Genre(models.Model):
    name = models.CharField(max_length=256)
    slug = models.CharField(
        max_length=50,
        unique=True
    )

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(max_length=128)
    year = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='titles',
        blank=True,
        null=True
    )
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle',
        related_name='titles'
    )

    def __str__(self):
        return self.name


class GenreTitle(models.Model):
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    def __str__(self):
        return f'Жанр - {self.genre}, произведение - {self.title}'


class Review(models.Model):
    score = models.PositiveSmallIntegerField()
    text = models.TextField()
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    pub_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review'
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique review'
            )
        ]

    def __str__(self):
        return self.text


class Comment(models.Model):
    text = models.TextField()
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    pub_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    def __str__(self):
        return self.text
'''