from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Класс админ-панели, отвечающий за ингредиенты."""

    list_display = (
        'pk',
        'name',
        'measurement_unit',
    )
    search_fields = ('name', )
    list_filter = ('name', )


class IngredientRecipeInline(admin.TabularInline):
    """Класс админ-панели, позволяющий добавлять ингредиенты в рецепт."""

    model = IngredientRecipe
    extra = 1
    verbose_name = 'Ингредиент'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Класс админ-панели, отвечающий за теги."""

    list_display = (
        'pk',
        'name',
        'color',
        'slug'
    )
    list_filter = ('name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Класс админ-панели, отвечающий за рецепты."""

    list_display = ('pk', 'name', 'author', 'favorite_count',)
    search_fields = ('author', 'name',)
    list_filter = ('author', 'name', 'tags',)
    inlines = [
        IngredientRecipeInline,
    ]

    def favorite_count(self, obj):
        """Выводит общее число добавлений этого рецепта в избранное."""
        return obj.favorit_recipe.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Класс админ-панели, отвечающий за избранное."""

    list_display = (
        'pk',
        'user',
        'recipe',
    )
    list_filter = ('user', 'recipe', )
    search_fields = ('user', 'recipe', )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Класс админ-панели, отвечающий за список покупок."""

    list_display = (
        'pk',
        'user',
        'recipe',
    )
    list_filter = ('user', 'recipe', )
    search_fields = ('user', 'recipe', )


admin.sites.AdminSite.empty_value_display = '-пусто-'
