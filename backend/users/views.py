import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets, mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from api.permissions import AdminOnlyExceptUpdateDestroy
from .serializers import (UserSerializer, UserSignUpSerializer,
                          UserTokenObtainSerializer)
from .models import User


class UsersViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                   mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    pagination_class = PageNumberPagination
    permission_classes = (AdminOnlyExceptUpdateDestroy, )
    filter_backends = (filters.SearchFilter, )
    search_fields = ('username',)

    def get_permissions(self):
        if self.action == 'retrieve':
            if self.kwargs.get('username') == 'me':
                return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    def retrieve(self, request, username):
        if username == 'me':
            me = get_object_or_404(User, pk=request.user.id)
            serializer = self.get_serializer(me)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return super().retrieve(request, username)

    def partial_update(self, request, username):
        if username == 'me':
            me = get_object_or_404(User, pk=request.user.id)
            data = request.data.copy()
            if (
                'role' in data
                and not request.user.is_superuser
            ):
                data['role'] = me.role
            serializer = self.get_serializer(me, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return super().partial_update(request, username)

    def destroy(self, request, username):
        if username == 'me':
            return Response(
                {'error': 'Нельзя удалить себя!'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().destroy(request, username)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def sign_up(request):
    serializer = UserSignUpSerializer(data=request.data)
    if serializer.is_valid():
        confirmation_code = uuid.uuid4()
        message_subject = (
            f'Вы зарегистрировались на yamdb '
            f'как {request.data.get("username")}'
        )
        message_text = f'Ваш регистрационный код: {confirmation_code}'
        if serializer.validated_data.get('username') == 'me':
            return Response(
                {'error': 'Такое имя пользователя недопустимо!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(
                username=serializer.validated_data.get('username')
            )
            if user.confirmation_code:
                return Response(
                    {'error': 'Такое имя пользователя уже занято!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.confirmation_code = confirmation_code
            user.save()
            send_mail(
                message_subject,
                message_text,
                'yamdb@yamdb.com',
                [serializer.validated_data.get('email')],
                fail_silently=False,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            if User.objects.filter(email=request.data.get('email')).exists():
                return Response(
                    {'error': 'Такой email уже был зарегистрирован!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            new_user = User.objects.create_user(
                username=serializer.validated_data.get("username"),
                email=serializer.validated_data.get("email")
            )
            new_user.confirmation_code = confirmation_code
            new_user.role = 'user'
            new_user.save()
            send_mail(
                message_subject,
                message_text,
                'yamdb@yamdb.com',
                [serializer.validated_data.get('email')],
                fail_silently=False,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def token_obtain(request):
    serializer = UserTokenObtainSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = User.objects.get(username=request.data.get('username'))
        except ObjectDoesNotExist:
            return Response(
                {'error': 'Такой пользователь не существует'},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.data.get('confirmation_code') != user.confirmation_code:
            return Response(
                {'error': 'Неверный код регистрации'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token = AccessToken.for_user(user)
        return Response(
            {
                'token': str(token)
            },
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
