from rest_framework import serializers

from .models import User


class UserSignUpSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()


class UserTokenObtainSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    lookup_field = 'username'

    class Meta:
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'role'
        )
        model = User
