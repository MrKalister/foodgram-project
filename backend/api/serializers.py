from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework.serializers import (ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField, ValidationError)
from rest_framework.validators import UniqueTogetherValidator
from users.models import Follow, User

from .fields import Base64ImageField, Hex2NameColor


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор для ответа на запрос User.

    Служит для отображения сериализованных данных
    с дополнительным полем is_subscribed.
    """

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """
        Возвращает bool на запрос подписки.

        Отображает подписки при запросе User
        Ответ True или False.
        """
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, following=obj).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для ответа на создания User."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class TagSerializer(ModelSerializer):
    """Сериализатор для модели Tag."""

    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'color',
            'slug'
        )


class IngredientSerializer(ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class GetIngredientRecipeSerializer(ModelSerializer):
    """Сериализатор для модели IngredientRecipe."""

    id = ReadOnlyField(source="ingredient.id")
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeSerializer(ModelSerializer):
    """
    Сериализатор для модели Recipe.

    Служит для безопасных запросов к recipes.
    """

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = GetIngredientRecipeSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True
    )
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    is_favorited = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe

        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, object):
        """Возвращает bool value на запрос есть рецепт в избранном."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.favorit_user.filter(recipe=object).exists()

    def get_is_in_shopping_cart(self, object):
        """Возвращает bool value на запрос есть рецепт в списке покупок."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.shopping_cart.filter(recipe=object).exists()


class CreateResponseSerializer(ModelSerializer):
    """Короткий отображение рецептов при создании подписки."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowListSerializer(CustomUserSerializer):
    """Ответ при создании подписки."""

    recipes = CreateResponseSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes_count(self, object):
        """Сообщает количество рецептов при get запросе к подпискам."""
        return object.recipes.count()


class FollowSerializer(ModelSerializer):
    """Ответ при запросе мои подписки."""

    def validate_following(self, following):
        """Валидация поля following."""
        user = self.context.get('request').user
        if user == following:
            raise ValidationError(
                'It is impossible to follow yourself'
            )
        return following

    class Meta:
        model = Follow
        fields = ('user', 'following')

        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='You are already following'
            )
        ]

    def to_representation(self, instance):
        """Сериализация данных при помощи FollowListSerializer."""
        return FollowListSerializer(
            instance.following,
            context={'request': self.context.get('request')}
        ).data


class CreateIngredientRecipeSerializer(ModelSerializer):
    """Для возврата краткой информации о ингредиентах при создании рецепта."""

    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class CreateRecipeSerializer(ModelSerializer):
    """
    Сериализатор для модели Recipe.

    Служит для небезопасных запросов к recipes.
    """

    image = Base64ImageField(required=False, allow_null=True)
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = CreateIngredientRecipeSerializer(many=True)

    def to_representation(self, value):
        """Сериализация данных при помощи RecipeSerializer."""
        return RecipeSerializer(
            value,
            context={
                'request': self.context.get('request')
            }
        ).data

    def validate_ingredients(self, ingredients):
        """Проверяем, что рецепт содержит уникальные ингредиенты."""
        ingredients_data = [
            ingredient.get('id') for ingredient in ingredients
        ]
        if len(ingredients_data) != len(set(ingredients_data)):
            raise ValidationError(
                'Ингредиенты рецепта должны быть уникальными'
            )
        return ingredients

    def validate_tags(self, tags):
        """Проверяем, что рецепт содержит уникальные теги."""
        if len(tags) != len(set(tags)):
            raise ValidationError(
                'Теги рецепта должны быть уникальными'
            )
        return tags

    def add_ingredients(self, ingredients_data, recipe):
        """Добавляет в рецепты ингредиенты."""
        IngredientRecipe.objects.bulk_create([
            IngredientRecipe(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients_data
        ])

    def create(self, validated_data):
        """
        Кастомный метод create.

        Создан, чтобы подгрузить автора, теги и ингредиенты.
        """

        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data, author=author)
        recipe.tags.set(tags_data)
        self.add_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        """
        Кастомный метод update.
        Создан, чтобы подгрузить автора, теги и ингредиенты.
        """

        recipe = instance
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        super().update(instance, validated_data)
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(tags)
        IngredientRecipe.objects.filter(recipe=recipe).delete()
        self.add_ingredients(ingredients, recipe)
        instance.save()
        return instance

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )


class FavoriteSerializer(ModelSerializer):
    """Сериализатор для модели Избранного."""

    class Meta:
        model = Favorite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавляли это рецепт в избранное'
            )
        ]


class ShoppingCartSerializer(ModelSerializer):
    """Сериализатор для модели ShoppingCart."""

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавляли это рецепт в список покупок'
            )
        ]


class SubscriptionShowSerializer(CustomUserSerializer):
    """Сериализатор отображения подписок."""

    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, object):
        """Возвращает рецепты в подписках с использованием лимита."""
        recipes_limit = self.context.get('recipes_limit')
        author_recipes = object.recipes.all()[:int(recipes_limit)]
        return CreateResponseSerializer(
            author_recipes, many=True
        ).data

    def get_recipes_count(self, object):
        """Сообщает количество рецептов при get запросе к подпискам."""
        return object.recipes.count()
