from django.urls import path, include
from rest_framework import routers

from users.views import (UsersViewSet,
                        sign_up, token_obtain)

v1_router = routers.DefaultRouter()
v1_router.register('users', UsersViewSet, basename='users')

urlpatterns = [
    path('', include(v1_router.urls)),
    path('auth/signup/', sign_up, name='sign_up'),
    path('auth/token/', token_obtain, name='token_obtain_pair')
]
