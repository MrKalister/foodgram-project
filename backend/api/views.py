from django.db.models import Sum, Subquery
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from djoser import utils, views
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from .filters import RecipeFilter, IngredientSearchFilter, SubscriptionsFilter
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow, User
from .permissions import IsAuthorOrReadOnly



from .pdf_downloader import create_pdf_file
from .serializers import (CreateRecipeSerializer, CreateResponseSerializer,
                          FavoriteSerializer, FollowListSerializer,
                          FollowSerializer,
                          IngredientSerializer, RecipeSerializer,
                          ShoppingCartSerializer, TagSerializer)


class CustomTokenCreateView(views.TokenCreateView):
    def _action(self, serializer):
        super()._action(serializer)
        token = utils.login_user(self.request, serializer.user)
        token_serializer_class = settings.SERIALIZERS.token
        return Response(
            data=token_serializer_class(token).data, status=status.HTTP_201_CREATED
        )


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter
    permission_classes = (permissions.AllowAny,)


class UsersViewSet(UserViewSet):
    pagination_class = LimitOffsetPagination
    # filterset_class = SubscriptionsFilter
    # filter_backends = [DjangoFilterBackend,]

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        subscriptions_list = self.paginate_queryset(
                User.objects.filter(following__user=request.user)
            )
        serializer = FollowListSerializer(
            subscriptions_list, many=True, context={
                'request': request
            }
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, id):
        if request.method != 'POST':
            subscription = Follow.objects.filter(
                user=request.user,
                following=get_object_or_404(User, id=id)
            )
            if subscription:
                self.perform_destroy(subscription)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Вы уже отписались или не были подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = FollowSerializer(
            data={
                'user': request.user.id,
                'following': get_object_or_404(User, id=id).id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    )
    pagination_class = LimitOffsetPagination
    filterset_class = RecipeFilter
    filter_backends = [DjangoFilterBackend,]

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return CreateRecipeSerializer


    @staticmethod
    def post_method_for_actions(request, pk, serializers):
        data = {'user': request.user.id, 'recipe': pk}
        serializer = serializers(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': request.user.id, 'recipe': pk}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            favorite_serializer = CreateResponseSerializer(recipe)
            return Response(
                favorite_serializer.data, status=status.HTTP_201_CREATED
            )
        favorite_recipe = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        )
        if favorite_recipe:
            favorite_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт уже удален из избранного'},
            status=status.HTTP_400_BAD_REQUEST
        ) 

    @action(methods=['post', 'delete'], detail=True,)
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'user': request.user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            shopping_cart_serializer = CreateResponseSerializer(recipe)
            return Response(
                shopping_cart_serializer.data, status=status.HTTP_201_CREATED
            )
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        )
        if shopping_cart:
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт уже удален из избранного'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Позволяет текущему пользователю закрузить список покупок."""
        shopping_cart = (
            IngredientRecipe.objects.filter(
                recipe__shopping_cart__user=request.user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit',
            ).order_by(
                'ingredient__name'
            ).annotate(ingredient_amount_sum=Sum('amount'))
        )
        return create_pdf_file(shopping_cart)
