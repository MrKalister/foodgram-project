from xml.dom import ValidationErr
import base64
import webcolors

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import (ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField,
                                        SlugRelatedField, ValidationError,
                                        ImageField, Field, ReadOnlyField, 
                                        IntegerField, BooleanField)
                                        

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag
from users.models import Follow, User


class Hex2NameColor(Field):
    def to_representation(self, value):
        return value
    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')  
            ext = format.split('/')[-1]  
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustumUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, following=obj).exists()


class CustumUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class TagSerializer(ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'color',
            'slug'
        )


class FollowListSerializer(CustumUserSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )
    def get_recipes(self, obj):
        return obj.recipes.all()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(CustumUserSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'following')

    def validate(self, data):
        get_object_or_404(User, username=data['following'])
        if self.context['request'].user == data['following']:
            raise ValidationError({
                'errors': 'Невозможно подписаться на себя.'
            })
        if Follow.objects.filter(
            user=self.context['request'].user,
            following=data['following']
        ):
            raise ValidationError({
                'errors': 'Вы уже подписаны.'
            })
        return data

    def to_representation(self, instance):
        return FollowListSerializer(
            instance.following,
            context={'request': self.context.get('request')}
        ).data


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class GetIngredientRecipeSerializer(ModelSerializer):
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
    tags = TagSerializer(many=True, read_only=True)
    author = CustumUserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    # is_in_shopping_cart = SerializerMethodField(read_only=True)
    # is_favorited = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe

        fields = (
            'id', 'tags', 'author', 'ingredients',
            # 'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )


    def get_ingredients(self, obj):
        ingredients = IngredientRecipe.objects.filter(recipe=obj)
        return GetIngredientRecipeSerializer(ingredients, many=True).data


class CreateIngredientRecipeSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class CreateRecipeSerializer(ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = CreateIngredientRecipeSerializer(many=True)

    def to_representation(self, value):
        data = RecipeSerializer(
            value,
            context={
                'request': self.context.get('request')
            }
        ).data
        return data


    def add_ingredients(self, ingredients_data, recipe):
        IngredientRecipe.objects.bulk_create([
            IngredientRecipe(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients_data
        ])

    def create(self, validated_data):
        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data, author=author)
        recipe.tags.set(tags_data)
        self.add_ingredients(ingredients_data, recipe)
        return recipe
    

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

