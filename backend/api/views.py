from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser import utils, views
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import IngredientSearchFilter, RecipeFilter
from .paginations import CustomPagination
from .pdf_downloader import create_pdf_file
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CreateRecipeSerializer,
    CreateResponseSerializer,
    FavoriteSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionShowSerializer,
    TagSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import Follow, User


class CustomTokenCreateView(views.TokenCreateView):
    """Для получения токена."""

    def _action(self, serializer):
        super()._action(serializer)
        token = utils.login_user(self.request, serializer.user)
        token_serializer_class = settings.SERIALIZERS.token
        return Response(
            data=token_serializer_class(token).data,
            status=status.HTTP_201_CREATED
        )


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для обьектов класса Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для обьектов класса Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter
    permission_classes = (permissions.AllowAny,)


class UsersViewSet(UserViewSet):
    """Вьюсет для подписок, модель Follow."""

    pagination_class = LimitOffsetPagination

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        """Возвращает авторов, на которых подписан пользователь."""
        recipes_limit = request.query_params['recipes_limit']
        authors = User.objects.filter(following__user=request.user)
        result_pages = self.paginate_queryset(
            queryset=authors
        )
        serializer = SubscriptionShowSerializer(
            result_pages,
            context={
                'request': request,
                'recipes_limit': recipes_limit
            },
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, id):
        """Позволяет добавить/удалить авторов в/из подписок."""
        if request.method != 'POST':
            subscription = Follow.objects.filter(
                user=request.user,
                following=get_object_or_404(User, id=id)
            )
            if subscription.exists():
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
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    )
    pagination_class = CustomPagination
    filterset_class = RecipeFilter
    filter_backends = [DjangoFilterBackend, ]

    def get_serializer_class(self):
        """Выбирает сериализотор в зависимости от запроса."""
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return CreateRecipeSerializer

    @staticmethod
    def post_method_for_actions(request, pk, serializer_req):
        """Для post запросов к shopping_cart и favorite."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {'user': request.user.id, 'recipe': pk}
        serializer = serializer_req(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer_data = CreateResponseSerializer(recipe)
        return Response(serializer_data.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_method_for_actions(request, pk, error, model):
        """Для delete запросов к shopping_cart и favorite."""
        recipe = get_object_or_404(Recipe, pk=pk)
        obj = model.objects.filter(
            user=request.user,
            recipe=recipe
        )
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': f'Рецепт уже удален из {error}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        """Метод для добавления и удаления рецепта в favorite."""
        if request.method == 'POST':
            return self.post_method_for_actions(request, pk,
                                                FavoriteSerializer)
        return self.delete_method_for_actions(request, pk,
                                              'избранного', Favorite)

    @action(methods=['post', 'delete'], detail=True,)
    def shopping_cart(self, request, pk):
        """Метод для добавления и удаления рецепта в shopping_cart."""
        if request.method == 'POST':
            return self.post_method_for_actions(request, pk,
                                                ShoppingCartSerializer)
        return self.delete_method_for_actions(request, pk,
                                              'списка покупок', ShoppingCart)

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
