from django.contrib import admin

from users.models import User

from .models import Ingredient, IngredientRecipe, Recipe, Tag


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1
    verbose_name = 'Ингредиент'

class UserAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = ('username', 'email',)
    list_filter = ('username', 'email',)
    empty_value_display = '-пусто-'



class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk','name','author',)
    search_fields = ('author__username', 'name', 'tags__name',)
    list_filter = ('author__username', 'name', 'tags__name',)
    empty_value_display = '-пусто-'
    inlines = [
        IngredientRecipeInline,
    ]


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'measurement_unit',
    )
    search_fields = ('name', )
    list_filter = ('name', )
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)

