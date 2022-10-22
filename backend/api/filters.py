from django_filters import FilterSet
from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag, Ingredient

class RecipeFilter(FilterSet):
    author = filters.CharFilter(
        field_name='author__id',
        lookup_expr='icontains'
    )
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited', 
        method='get_is_favorit',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    def get_is_favorit(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorit_recipe__user=self.request.user)
        return queryset
    
    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ['author', 'tags',  'is_favorited', 'is_in_shopping_cart']


class SubscriptionsFilter(FilterSet):
    recipes_limit = filters.NumberFilter(
        field_name='recipes_limit', 
        method='get_recipes_limit',
        queryset = Recipe.objects.all()
    )

    def get_recipes_limit(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            
            queryset = queryset.filter(following__user__user=self.request.user).values('recipes')[:value]
            return queryset
        return queryset

    class Meta:
        model = Recipe
        fields = ['recipes_limit',]


class IngredientSearchFilter(filters.FilterSet):
    """Фильтр поиска по названию ингредиента."""
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name', )