from django.urls import include, path, re_path
from rest_framework import routers

from .views import (CustomTokenCreateView, IngredientViewSet, RecipeViewSet,
                    TagViewSet, UsersViewSet,)

v1_router = routers.DefaultRouter()
v1_router.register('users', UsersViewSet, basename='subscriptions')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('recipes', RecipeViewSet, basename='recipes')
v1_router.register('tags', TagViewSet, basename='tags')


urlpatterns = [
    path('', include(v1_router.urls)),
    path('', include('djoser.urls')),
    re_path(r"^auth/token/login/?$", CustomTokenCreateView.as_view(), name="login"),
    path('auth/', include('djoser.urls.authtoken')),
]

'''
v1_router.register(
    r'recipes/(?P<recipes_id>\d+)/favorite',
    FavoriteViewSet,
    basename='favorite'
)
'''