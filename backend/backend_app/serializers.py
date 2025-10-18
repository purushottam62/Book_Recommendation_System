from rest_framework import serializers
from .models import RegisteredUser, User, Book, Rating
from django.contrib.auth.hashers import make_password, check_password


# ----------------------------
# Registration & Login
# ----------------------------
class RegisteredUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = RegisteredUser
        fields = ['id', 'username', 'email', 'password', 'full_name', 'date_joined']

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


# ----------------------------
# ML Model Tables
# ----------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'
